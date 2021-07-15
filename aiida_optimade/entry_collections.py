from typing import Any, Dict, Tuple, List, Set, Union
import warnings

from tqdm import tqdm

from aiida.orm.nodes import Node
from aiida.orm.querybuilder import QueryBuilder

from optimade.models import EntryResource
from optimade.server.entry_collections import EntryCollection
from optimade.server.exceptions import BadRequest, NotFound
from optimade.server.query_params import EntryListingQueryParams, SingleEntryQueryParams
from optimade.server.warnings import UnknownProviderProperty

from aiida_optimade.common import CausationError
from aiida_optimade.common.logger import LOGGER
from aiida_optimade.mappers import ResourceMapper
from aiida_optimade.transformers import AiidaTransformer
from aiida_optimade.utils import retrieve_queryable_properties


class AiidaCollection(EntryCollection):
    """Collection of AiiDA entities"""

    CAST_MAPPING = {
        "string": "t",
        "float": "f",
        "integer": "i",
        "boolean": "b",
        "date-time": "d",
    }

    def __init__(
        self,
        entities: Union[str, List[str]],
        resource_cls: EntryResource,
        resource_mapper: ResourceMapper,
    ):
        super().__init__(
            resource_cls=resource_cls,
            resource_mapper=resource_mapper,
            transformer=AiidaTransformer(mapper=resource_mapper),
        )

        self.entities = entities if isinstance(entities, list) else [entities]

        # "Cache"
        self._data_available: int = None
        self._data_returned: int = None
        self._extras_fields: Set[str] = None
        self._latest_filter: Dict[str, Any] = None
        self._count: Dict[str, Any] = None
        self._checked_extras_filter_fields: set = set()

        self._all_fields: Set[str] = None

    @property
    def all_fields(self) -> Set[str]:
        if not self._all_fields:
            self._all_fields = super().all_fields
        return self._all_fields

    @property
    def data_available(self) -> int:
        """Get amount of data available under endpoint"""
        if self._data_available is None:
            raise CausationError(
                "data_available MUST be set before it can be retrieved."
            )
        return self._data_available

    def set_data_available(self):
        """Set _data_available if it has not yet been set"""
        if not self._data_available:
            LOGGER.debug("Setting data_available!")
            self._data_available = self.count()

    @property
    def data_returned(self) -> int:
        """Get amount of data returned for query"""
        if self._data_returned is None:
            raise CausationError(
                "data_returned MUST be set before it can be retrieved."
            )
        return self._data_returned

    def set_data_returned(self, **criteria):
        """Set _data_returned if it has not yet been set or new filter does not equal
        latest filter.

        NB! Nested lists in filters are not accounted for.
        """
        if self._data_returned is None or (
            self._latest_filter is not None
            and criteria.get("filters", {}) != self._latest_filter
        ):
            for key in ["limit", "offset"]:
                if key in list(criteria.keys()):
                    del criteria[key]
            self._latest_filter = criteria.get("filters", {}).copy()
            LOGGER.debug("Setting data_returned using filter: %s", self._latest_filter)
            self._data_returned = self.count(**criteria)

    def _clear_cache(self) -> None:
        """Clear in-memory attributes cache"""
        self._data_available: int = None
        self._data_returned: int = None
        self._extras_fields: set = None
        self._latest_filter: dict = None
        self._count: dict = None
        self._checked_extras_filter_fields: set = set()

    def __len__(self) -> int:
        return self.data_available

    def insert(self, _: List[EntryResource]) -> None:
        raise NotImplementedError(
            f"The insert method is not implemented for {self.__class__.__name__}."
        )

    def count(self, **kwargs) -> int:
        LOGGER.debug("Calling count function in EntryCollection.")
        if self._count is None:
            LOGGER.debug("self._count is None")
            self._count = {
                "count": self._perform_count(**kwargs),
                "filters": kwargs.get("filters", {}),
                "limit": kwargs.get("limit", None),
                "offset": kwargs.get("offset", None),
            }
        else:
            for limiting_param in {"filters", "limit", "offset"}:
                if kwargs.get(limiting_param, None) != self._count.get(
                    limiting_param, None
                ):
                    if limiting_param == "filters":
                        # As the `node_type` field is added to the filters in
                        # `_prepare_query()`, this will make sure to check the *actual*
                        # requested filter fields.
                        count_copy = self._count.get(limiting_param, {}).copy()
                        kwargs_copy = kwargs.get(limiting_param, {}).copy()
                        count_copy.pop("node_type", None)
                        kwargs_copy.pop("node_type", None)
                        if kwargs_copy == count_copy:
                            continue
                    elif limiting_param == "offset":
                        if not kwargs.get(limiting_param, None) and not self._count.get(
                            limiting_param, None
                        ):
                            # This will check also if offset in either is set to 0.
                            # There is no difference if the default page_offset is
                            # requested.
                            continue
                    LOGGER.debug(
                        "%s was not the same as was found in self._count:\n"
                        "self._count[%s] = %s\nkwargs[%s] = %s",
                        limiting_param,
                        limiting_param,
                        self._count.get(limiting_param, None),
                        limiting_param,
                        kwargs.get(limiting_param, None),
                    )
                    self._count = {
                        "count": self._perform_count(**kwargs),
                        "filters": kwargs.get("filters", {}),
                        "limit": kwargs.get("limit", None),
                        "offset": kwargs.get("offset", None),
                    }
                    break
            else:
                LOGGER.debug("Using self._count")

        return self._count.get("count", 0)

    def find(  # pylint: disable=too-many-branches
        self, params: Union[EntryListingQueryParams, SingleEntryQueryParams]
    ) -> Tuple[
        Union[List[EntryResource], EntryResource, None], int, bool, Set[str], Set[str]
    ]:
        self.set_data_available()

        criteria = self.handle_query_params(params)
        single_entry = isinstance(params, SingleEntryQueryParams)
        response_fields = criteria.pop("fields", set())

        if criteria.get("filters", {}) and self._extras_fields:
            for requested_extras_field in self._extras_fields:
                if requested_extras_field not in self._checked_extras_filter_fields:
                    LOGGER.debug(
                        "Checking all extras fields have been calculated (and possibly "
                        "calculate them)."
                    )
                    self._check_and_calculate_entities()
                    self._checked_extras_filter_fields |= self._extras_fields
                    break
            else:
                LOGGER.debug(
                    "Not checking extras fields. Fields have already been checked."
                )
        else:
            LOGGER.debug(
                "Not checking extras fields. No filter and/or no extras fields "
                "requested."
            )

        self.set_data_returned(**criteria)

        results, more_data_available = self._run_db_query(
            criteria=criteria, single_entry=single_entry
        )

        if single_entry:
            if len(results) > 1:
                raise NotFound(
                    detail=f"Instead of a single entry, {len(results)} entries were "
                    "found",
                )

            results = results[0] if results else None

        include_fields = (
            response_fields - self.resource_mapper.TOP_LEVEL_NON_ATTRIBUTES_FIELDS
        )

        bad_optimade_fields = set()
        bad_provider_fields = set()
        for field in include_fields:
            if field not in self.resource_mapper.ALL_ATTRIBUTES:
                if field.startswith("_"):
                    if any(
                        field.startswith(f"_{prefix}_")
                        for prefix in self.resource_mapper.SUPPORTED_PREFIXES
                    ):
                        bad_provider_fields.add(field)
                else:
                    bad_optimade_fields.add(field)

        if bad_provider_fields:
            warnings.warn(
                UnknownProviderProperty(
                    detail=(
                        "Unrecognised field(s) for this provider requested in "
                        f"`response_fields`: {bad_provider_fields}."
                    )
                )
            )

        if bad_optimade_fields:
            raise BadRequest(
                detail=(
                    "Unrecognised OPTIMADE field(s) in requested `response_fields`: "
                    f"{bad_optimade_fields}."
                )
            )

        if results:
            results = self.resource_mapper.deserialize(results)

        return (
            results,
            self.data_returned,
            more_data_available,
            self.all_fields - response_fields,
            include_fields,
        )

    def _run_db_query(
        self, criteria: Dict[str, Any], single_entry: bool = False
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """Run the query on the backend and collect the results.

        Arguments:
            criteria: A dictionary representation of the query parameters.
            single_entry: Whether or not the caller is expecting a single entry
                response.

        Returns:
            The list of entries from the database (without any re-mapping) and a
            boolean for whether or not there is more data available.

        """
        results = []
        for entity in self._find_all(**criteria):
            results.append(dict(zip(criteria["project"], entity)))

        if single_entry:
            more_data_available = False
        else:
            criteria_copy = criteria.copy()
            criteria_copy.pop("limit", None)
            offset = criteria_copy.pop("offset", 0)
            more_data_available = len(results) < (self.count(**criteria_copy) - offset)

        return results, more_data_available

    @staticmethod
    def _prepare_query(node_types: List[str], **kwargs) -> QueryBuilder:
        """Workhorse function to prepare an AiiDA QueryBuilder query"""
        for key in kwargs:
            if key not in {"filters", "order_by", "limit", "project", "offset"}:
                raise ValueError(
                    f"You supplied key {key!r}. The only valid query keys are: "
                    '"filters", "order_by", "limit", "project", "offset"'
                )

        filters = kwargs.get("filters", {})
        filters["node_type"] = {"or": [{"==": node_type} for node_type in node_types]}
        order_by = kwargs.get("order_by", None)
        order_by = {Node: order_by} if order_by else {Node: {"id": "asc"}}
        limit = kwargs.get("limit", None)
        offset = kwargs.get("offset", None)
        project = kwargs.get("project", [])

        query = QueryBuilder(limit=limit, offset=offset)
        query.append(Node, project=project, filters=filters)
        query.order_by(order_by)

        return query

    def _find_all(self, **kwargs) -> list:
        """Execute AiiDA QueryBuilder query, return all results."""
        LOGGER.debug(
            "Using QueryBuilder to get ALL projected values from found entries."
        )
        query = self._prepare_query(self.entities, **kwargs)
        res = query.all()
        del query
        return res

    def _perform_count(self, **kwargs) -> int:
        """Instantiate new QueryBuilder object and perform count()"""
        LOGGER.debug("Using QueryBuilder to COUNT all found entries.")
        query = self._prepare_query(self.entities, **kwargs)
        res = query.count()
        del query
        return res

    def handle_query_params(
        self, params: Union[EntryListingQueryParams, SingleEntryQueryParams]
    ) -> Dict[str, Any]:
        """Parse and interpret the backend-agnostic query parameter models into a
        dictionary that can be used by AiiDA's QueryBuilder.

        Parameters:
            params: The initialized query parameter model from the server.

        Raises:
            Forbidden: If too large of a page limit is provided.
            BadRequest: If an invalid request is made, e.g., with incorrect fields
                or response format.

        Returns:
            A dictionary representation of the query parameters.

        """
        cursor_kwargs: dict = super().handle_query_params(params)

        # Remove Mongo-specific fields introduced in the parent method
        cursor_kwargs.get("projection", {}).pop("_id", None)

        # filter
        if cursor_kwargs.get("filter", False):
            cursor_kwargs["filters"] = cursor_kwargs.pop("filter")
            self._find_extras_fields(cursor_kwargs["filters"])
        else:
            cursor_kwargs.pop("filter", None)

        # response_fields
        cursor_kwargs["project"] = list(cursor_kwargs.pop("projection", {}).keys())

        # sort
        if cursor_kwargs.get("sort", False):
            cursor_kwargs["order_by"] = cursor_kwargs.pop("sort")

        # page_offset
        if cursor_kwargs.get("skip", False):
            cursor_kwargs["offset"] = cursor_kwargs.pop("skip")

        return cursor_kwargs

    def parse_sort_params(self, sort_params: str) -> List[Dict[str, Dict[str, str]]]:
        """Handles any sort parameters passed to the collection,
        resolving aliases and dealing with any invalid fields.

        Note:
            Sorting only works for extras fields for the nodes already with calculated
            extras. To calculate all extras, make a single filter query using any extra
            field.

        Raises:
            BadRequest: If an invalid sort is requested.

        Returns:
            A list of dictionaries definining the sort order, type and indirectly the
            internal priority.

        """
        sort_spec = []
        for entity_property in sort_params.split(","):
            field = entity_property
            sort_direction = "asc"
            if entity_property.startswith("-"):
                field = field[1:]
                sort_direction = "desc"
            aliased_field = self.resource_mapper.get_backend_field(field)

            _, properties = retrieve_queryable_properties(
                self.resource_cls.schema(), {"id", "type", "attributes"}
            )
            field_type = properties[field].get(
                "format", properties[field].get("type", "")
            )
            if field_type == "array":
                raise TypeError("Cannot sort on a field with a list value type.")

            sort_spec.append(
                {
                    aliased_field: {
                        "order": sort_direction,
                        "cast": self.CAST_MAPPING[field_type],
                    }
                }
            )
        return sort_spec

    def _find_extras_fields(self, filters: Union[dict, list]) -> None:
        """Collect all properties to be found in AiiDA Node extras.

        Parameters:
            filters: The complete or part of the parsed and transformed `filter` query
                parameter.

        """
        from copy import deepcopy

        def __filter_fields_util(  # pylint: disable=unused-private-member
            _filters: Union[dict, list]
        ) -> Union[dict, list]:
            if isinstance(_filters, dict):
                res = {}
                for key, value in _filters.items():
                    res[key] = (
                        __filter_fields_util(value)
                        if isinstance(value, (dict, list))
                        else value
                    )
                self._extras_fields |= {
                    key[len(self.resource_mapper.PROJECT_PREFIX) :]
                    for key in _filters
                    if key.startswith(self.resource_mapper.PROJECT_PREFIX)
                }
            elif isinstance(_filters, list):
                res = [
                    __filter_fields_util(item)
                    if isinstance(item, (dict, list))
                    else item
                    for item in _filters
                ]
            else:
                raise NotImplementedError(
                    "_find_extras_fields can only handle dict and list objects."
                )
            return res

        self._extras_fields = set()
        __filter_fields_util(deepcopy(filters))

    def _check_and_calculate_entities(
        self, cli: bool = False, entries: List[List[int]] = None
    ) -> List[int]:
        """Check all entities have OPTIMADE extras, else calculate them

        For a bit of optimization, we only care about a field if it has specifically
        been queried for using "filter".

        Parameters:
            cli: Whether or not this method is run through the CLI.
            entries: AiiDA Node PKs.

        Returns:
            A list of the Node PKs representing the Nodes that were necessary to
            calculate the given fields for.

        """

        def _update_entities(entities: List[List[Any]], fields: List[str]):
            """Utility function to update entities within this method"""
            optimade_fields = [
                self.resource_mapper.get_optimade_field(_) for _ in fields
            ]
            for entity in entities:
                field_to_entity_value = dict(zip(optimade_fields, entity))
                retrieved_attributes = field_to_entity_value.copy()
                for missing_attribute in self._extras_fields:
                    retrieved_attributes.pop(missing_attribute)
                self.resource_mapper.build_attributes(
                    retrieved_attributes=retrieved_attributes,
                    entry_pk=field_to_entity_value["id"],
                    node_type=field_to_entity_value["type"],
                    missing_attributes=self._extras_fields,
                )

        extras_keys = [
            key for key in self.resource_mapper.PROJECT_PREFIX.split(".") if key
        ]
        filter_fields = [{"!has_key": field} for field in self._extras_fields]
        necessary_entity_ids = (
            self._find_all(
                filters={
                    "or": [
                        {extras_keys[0]: {"!has_key": extras_keys[1]}},
                        {".".join(extras_keys): {"or": filter_fields}},
                    ]
                },
                project="id",
            )
            if entries is None
            else entries
        )

        if necessary_entity_ids:
            # Necessary entities for the OPTIMADE query exist with unknown OPTIMADE
            # fields.
            necessary_entity_ids = [pk[0] for pk in necessary_entity_ids]

            # Create the missing OPTIMADE fields
            fields = {"id", "type"}
            fields |= self.get_attribute_fields()
            fields |= {
                f"_{self.provider_prefix}_{field}" for field in self.provider_fields
            }
            fields = list({self.resource_mapper.get_backend_field(_) for _ in fields})

            entities = self._find_all(
                filters={"id": {"in": necessary_entity_ids}}, project=fields
            )

            if cli:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    _update_entities(
                        tqdm(entities, desc="Calculating fields", leave=False),
                        fields,
                    )
            else:
                _update_entities(entities, fields)
            return necessary_entity_ids

        return []
