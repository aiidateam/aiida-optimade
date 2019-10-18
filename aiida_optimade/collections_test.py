from abc import abstractmethod
from configparser import ConfigParser
from pathlib import Path
from typing import Collection, Tuple, List

from aiida import orm
from fastapi import HTTPException
from optimade.filterparser import LarkParser

from aiida_optimade.transformers import AiidaTransformer
from aiida_optimade.models import NonnegativeInt
from aiida_optimade.models import Resource
from aiida_optimade.models import ResourceMapper
from aiida_optimade.deps import EntryListingQueryParams


config = ConfigParser()
config.read(Path(__file__).resolve().parent.joinpath("config.ini"))
PAGE_LIMIT = config["DEFAULT"].getint("PAGE_LIMIT")
DB_PAGE_LIMIT = config["DB_SPECIFIC"].getint("PAGE_LIMIT")


def _find(entity_type: str, **kwargs) -> orm.QueryBuilder:
    for key in kwargs:
        if key not in {"filters", "order_by", "limit", "project", "offset"}:
            raise ValueError(
                f"You supplied key {key}. _find() only takes the keys: "
                '"filters", "order_by", "limit", "project", "offset"'
            )

    filters = kwargs.get("filters", {})
    order_by = kwargs.get("order_by", None)
    order_by = {entity_type: order_by} if order_by else {}
    limit = kwargs.get("limit", None)
    offset = kwargs.get("offset", None)
    project = kwargs.get("project", [])

    query = orm.QueryBuilder(limit=limit, offset=offset)
    query.append(entity_type, project=project, filters=filters)
    query.order_by(order_by)

    return query


class EntryCollection(Collection):  # pylint: disable=inherit-non-class
    def __init__(
        self, collection, resource_cls: Resource, resource_mapper: ResourceMapper
    ):
        self.collection = collection
        self.parser = LarkParser()
        self.resource_cls = resource_cls
        self.resource_mapper = resource_mapper

    def __len__(self):
        return self.collection.count()

    def __iter__(self):
        return self.collection.find()

    def __contains__(self, entry):
        return self.collection.count(entry) > 0

    @abstractmethod
    def find(
        self, params: EntryListingQueryParams
    ) -> Tuple[List[Resource], bool, NonnegativeInt]:
        """
        Fetches results and indicates if more data is available.

        Also gives the total number of data available in the absence of response_limit.

        Args:
            params (EntryListingQueryParams): entry listing URL query params

        Returns:
            Tuple[List[Resource], bool, NonnegativeInt]: (results, more_data_available, data_available)

        """

    def count(self, **kwargs):
        return self.collection.count(**kwargs)


class AiidaCollection(EntryCollection):
    """Collection of AiiDA entities"""

    def __init__(
        self,
        collection: orm.entities.Collection,
        resource_cls: Resource,
        resource_mapper: ResourceMapper,
    ):
        super().__init__(collection, resource_cls, resource_mapper)
        self.transformer = AiidaTransformer()

    def __len__(self) -> int:
        return self.collection.query().count()

    def __contains__(self, entry) -> bool:
        return self.collection.count(filters={"uuid": entry.uuid}, limit=1) > 0

    def count(self, **kwargs) -> int:
        for key in list(kwargs.keys()):
            if key not in ("filters", "order_by", "limit", "offset"):
                del kwargs[key]
        return self.collection.find().count(kwargs)

    def find(  # pylint: disable=too-many-locals
        self, params: EntryListingQueryParams
    ) -> Tuple[List[Resource], bool, NonnegativeInt]:
        criteria = self._parse_params(params)

        criteria_nolimit = criteria.copy()
        del criteria_nolimit["limit"]

        nresults_now = self.count(**criteria)
        nresults_total = self.count(**criteria_nolimit)

        more_data_available = nresults_now < nresults_total
        data_available = nresults_total

        criteria_required_projections = criteria.copy()
        criteria_projections = set(criteria_required_projections["project"])
        required_projections = {"uuid"}
        criteria_projections.update(required_projections)
        criteria_required_projections["project"] = sorted(criteria_projections)

        results = []
        for entity in _find(
            self.collection.entity_type, **criteria_required_projections
        ).iterall():
            results.append(
                self.resource_cls(
                    **self.resource_mapper.map_back(
                        dict(zip(criteria_required_projections["project"], entity))
                    )
                )
            )

        project_difference = criteria_projections - set(criteria["project"])
        if project_difference:
            for entry in results:
                if "uuid" in project_difference:
                    del entry["attributes"]["immutable_id"]
                else:
                    raise AssertionError(
                        "project_difference should only ever be able to contain "
                        f'"uuid". project_difference: {project_difference}'
                    )

        return results, more_data_available, data_available

    def _parse_params(self, params: EntryListingQueryParams) -> dict:
        cursor_kwargs = {}

        # filter
        if params.filter:
            tree = self.parser.parse(params.filter)
            cursor_kwargs["filters"] = self.transformer.transform(tree)
        else:
            cursor_kwargs["filters"] = {}

        # response_format
        if params.response_format and params.response_format != "json":
            raise HTTPException(
                status_code=400, detail="Only 'json' response_format supported"
            )

        # page_limit
        limit = PAGE_LIMIT
        if params.page_limit and params.page_limit != PAGE_LIMIT:
            limit = params.page_limit
        if limit > DB_PAGE_LIMIT:
            raise HTTPException(
                status_code=403,
                detail=f"Max page_limit is {DB_PAGE_LIMIT}, you requested {PAGE_LIMIT}",
            )
        if limit == 0:
            limit = PAGE_LIMIT
        cursor_kwargs["limit"] = limit

        # response_fields
        if params.response_fields:
            fields = set(params.response_fields.split(","))
        else:
            fields = {"immutable_id", "last_modified", "type", "id", "all"}
        cursor_kwargs["project"] = list(
            {self.resource_mapper.alias_for(f) for f in fields}
        )

        # sort
        if params.sort:
            sort_spec = []
            for entity_property in params.sort.split(","):
                field = entity_property
                sort_direction = "asc"
                if entity_property.startswith("-"):
                    field = field[1:]
                    sort_direction = "desc"
                sort_spec.append({field: sort_direction})
            cursor_kwargs["order_by"] = sort_spec

        # page_offset
        if params.page_offset:
            cursor_kwargs["offset"] = params.page_offset

        return cursor_kwargs
