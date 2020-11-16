from typing import Tuple, List, Union, Any
import warnings

from fastapi import HTTPException
from tqdm import tqdm

from aiida.orm import Entity, QueryBuilder

from optimade.filterparser import LarkParser
from optimade.models import EntryResource
from optimade.server.config import CONFIG
from optimade.server.query_params import EntryListingQueryParams, SingleEntryQueryParams

from aiida_optimade.common import CausationError
from aiida_optimade.mappers import ResourceMapper
from aiida_optimade.transformers import AiidaTransformer
from aiida_optimade.utils import retrieve_queryable_properties


class AiidaCollection:
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
        entity: Entity,
        resource_cls: EntryResource,
        resource_mapper: ResourceMapper,
    ):
        self.entity = entity
        self.parser = LarkParser()
        self.resource_cls = resource_cls
        self.resource_mapper = resource_mapper

        self.transformer = AiidaTransformer()
        self.provider = CONFIG.provider.prefix
        self.provider_fields = CONFIG.provider_fields.get(resource_mapper.ENDPOINT, [])
        self.parser = LarkParser()

        # "Cache"
        self._data_available: int = None
        self._data_returned: int = None
        self._filter_fields: set = None
        self._latest_filter: dict = None

    def get_attribute_fields(self) -> set:
        """Get all attribute properties/fields for OPTIMADE entity"""
        schema = self.resource_cls.schema()
        attributes = schema["properties"]["attributes"]
        if "allOf" in attributes:
            allOf = attributes.pop("allOf")  # pylint: disable=invalid-name
            for dict_ in allOf:
                attributes.update(dict_)
        if "$ref" in attributes:
            path = attributes["$ref"].split("/")[1:]
            attributes = schema.copy()
            while path:
                next_key = path.pop(0)
                attributes = attributes[next_key]
        return set(attributes["properties"].keys())

    @staticmethod
    def _find(entity_type: Entity, **kwargs) -> QueryBuilder:
        """Workhorse function to perform AiiDA QueryBuilder query"""
        for key in kwargs:
            if key not in {"filters", "order_by", "limit", "project", "offset"}:
                raise ValueError(
                    f"You supplied key {key!r}. _find() only takes the keys: "
                    '"filters", "order_by", "limit", "project", "offset"'
                )

        filters = kwargs.get("filters", {})
        order_by = kwargs.get("order_by", None)
        order_by = {entity_type: order_by} if order_by else {entity_type: {"id": "asc"}}
        limit = kwargs.get("limit", None)
        offset = kwargs.get("offset", None)
        project = kwargs.get("project", [])

        query = QueryBuilder(limit=limit, offset=offset)
        query.append(entity_type, project=project, filters=filters)
        query.order_by(order_by)

        return query

    def _find_all(self, **kwargs) -> list:
        """Helper function to instantiate an AiiDA QueryBuilder"""
        query = self._find(self.entity, **kwargs)
        res = query.all()
        del query
        return res

    def count(self, **kwargs) -> int:
        """Count amount of data returned for query"""
        query = self._find(self.entity, **kwargs)
        res = query.count()
        del query
        return res

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
            self._latest_filter = criteria.get("filters", {})
            self._data_returned = self.count(**criteria)

    def find(
        self, params: Union[EntryListingQueryParams, SingleEntryQueryParams]
    ) -> Tuple[List[EntryResource], int, bool, int, set]:
        """Find all requested AiiDA entities as OPTIMADE JSON objects"""
        self.set_data_available()
        criteria = self._parse_params(params)

        all_fields = criteria.pop("fields")
        if getattr(params, "response_fields", False):
            fields = set(params.response_fields.split(","))
            fields |= self.resource_mapper.get_required_fields()
        else:
            fields = all_fields.copy()

        if criteria.get("filters", {}) and self._get_extras_filter_fields():
            self._check_and_calculate_entities()

        self.set_data_returned(**criteria)

        entities = self._find_all(**criteria)
        results = []
        for entity in entities:
            results.append(
                self.resource_cls(
                    **self.resource_mapper.map_back(
                        dict(zip(criteria["project"], entity))
                    )
                )
            )

        if isinstance(params, EntryListingQueryParams):
            criteria_no_limit = criteria.copy()
            criteria_no_limit.pop("limit", None)
            more_data_available = len(results) < self.count(**criteria_no_limit)
        else:
            more_data_available = False
            if len(results) > 1:
                raise HTTPException(
                    status_code=404,
                    detail=f"Instead of a single entry, {len(results)} entries were "
                    "found",
                )

        if isinstance(params, SingleEntryQueryParams):
            results = results[0] if results else None

        return (
            results,
            self.data_returned,
            more_data_available,
            self.data_available,
            all_fields - fields,
        )

    def _alias_filter(self, filters: Any) -> Union[dict, list]:
        """Get aliased field names in nested filter query.

        I.e. turn OPTIMADE field names into AiiDA field names
        """
        if isinstance(filters, dict):
            res = {}
            for key, value in filters.items():
                new_value = value
                if isinstance(value, (dict, list)):
                    new_value = self._alias_filter(value)
                aliased_key = self.resource_mapper.alias_for(key)
                res[aliased_key] = new_value
                self._filter_fields.add(aliased_key)
        elif isinstance(filters, list):
            res = []
            for item in filters:
                new_value = item
                if isinstance(item, (dict, list)):
                    new_value = self._alias_filter(item)
                res.append(new_value)
        else:
            raise NotImplementedError(
                "_alias_filter can only handle dict and list objects"
            )
        return res

    def _parse_params(self, params: EntryListingQueryParams) -> dict:
        """Parse query parameters and transform them into AiiDA QueryBuilder concepts"""
        cursor_kwargs = {}

        # filter
        if getattr(params, "filter", False):
            aiida_filter = self.transformer.transform(self.parser.parse(params.filter))
            self._filter_fields = set()
            cursor_kwargs["filters"] = self._alias_filter(aiida_filter)

        # response_format
        if (
            getattr(params, "response_format", False)
            and params.response_format != "json"
        ):
            raise HTTPException(
                status_code=400, detail="Only 'json' response_format supported"
            )

        # page_limit
        if getattr(params, "page_limit", False):
            limit = params.page_limit
            if limit > CONFIG.page_limit_max:
                raise HTTPException(
                    status_code=403,  # Forbidden
                    detail=f"Max allowed page_limit is {CONFIG.page_limit_max}, "
                    f"you requested {limit}",
                )
            cursor_kwargs["limit"] = limit
        else:
            cursor_kwargs["limit"] = CONFIG.page_limit

        # response_fields
        # All OPTIMADE fields
        fields = self.resource_mapper.TOP_LEVEL_NON_ATTRIBUTES_FIELDS.copy()
        fields |= self.get_attribute_fields()
        # All provider-specific fields
        fields |= {f"_{self.provider}_" + _ for _ in self.provider_fields}
        cursor_kwargs["fields"] = fields
        cursor_kwargs["project"] = list(
            {self.resource_mapper.alias_for(f) for f in fields}
        )

        # sort
        # NOTE: sorting only works for extras fields for the nodes already with
        #       calculated extras. To calculate all extras, make a single filter query
        #       using any extra field.
        if getattr(params, "sort", False):
            sort_spec = []
            for entity_property in params.sort.split(","):
                field = entity_property
                sort_direction = "asc"
                if entity_property.startswith("-"):
                    field = field[1:]
                    sort_direction = "desc"
                aliased_field = self.resource_mapper.alias_for(field)

                _, properties = retrieve_queryable_properties(
                    self.resource_cls.schema(), {"id", "type", "attributes"}
                )
                field_type = properties[field].get(
                    "format", properties[field].get("type", "")
                )
                if field_type == "array":
                    raise TypeError("Cannot sort on a field with a list value type")

                sort_spec.append(
                    {
                        aliased_field: {
                            "order": sort_direction,
                            "cast": self.CAST_MAPPING[field_type],
                        }
                    }
                )
            cursor_kwargs["order_by"] = sort_spec

        # page_offset
        if getattr(params, "page_offset", False):
            cursor_kwargs["offset"] = params.page_offset

        return cursor_kwargs

    def _get_extras_filter_fields(self) -> set:
        return {
            field[len(self.resource_mapper.PROJECT_PREFIX) :]  # noqa: E203
            for field in self._filter_fields
            if field.startswith(self.resource_mapper.PROJECT_PREFIX)
        }

    def _check_and_calculate_entities(self, cli: bool = False) -> List[int]:
        """Check all entities have OPTIMADE extras, else calculate them

        For a bit of optimization, we only care about a field if it has specifically
        been queried for using "filter".

        Parameters:
            cli: Whether or not this method is run through the CLI.

        Returns:
            A list of the Node PKs representing the Nodes that were necessary to
            calculate the given fields for.

        """

        def _update_entities(entities: list, fields: list):
            """Utility function to update entities within this method"""
            for entity in entities:
                self.resource_cls(
                    **self.resource_mapper.map_back(dict(zip(fields, entity)))
                )

        extras_keys = [
            key for key in self.resource_mapper.PROJECT_PREFIX.split(".") if key
        ]
        filter_fields = [
            {"!has_key": field} for field in self._get_extras_filter_fields()
        ]
        necessary_entities_qb = self._find_all(
            filters={
                "or": [
                    {extras_keys[0]: {"!has_key": extras_keys[1]}},
                    {".".join(extras_keys): {"or": filter_fields}},
                ]
            },
            project="id",
        )

        if necessary_entities_qb:
            # Necessary entities for the OPTIMADE query exist with unknown OPTIMADE
            # fields.
            necessary_entity_ids = [pk[0] for pk in necessary_entities_qb]

            # Create the missing OPTIMADE fields:
            # All OPTIMADE fields
            fields = {"id", "type"}
            fields |= self.get_attribute_fields()
            # All provider-specific fields
            fields |= {f"_{self.provider}_" + _ for _ in self.provider_fields}
            fields = list({self.resource_mapper.alias_for(f) for f in fields})

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
