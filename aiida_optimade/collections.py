from typing import Tuple, List, Union

from aiida import orm
from fastapi import HTTPException

from optimade.filterparser import LarkParser
from optimade.server.deps import EntryListingQueryParams, SingleEntryQueryParams
from optimade.models import NonnegativeInt, EntryResource
from optimade.server.collections import EntryCollection as OptimadeEntryCollection

from aiida_optimade.transformers import AiidaTransformer
from aiida_optimade.mappers import ResourceMapper
from aiida_optimade.config import CONFIG


class EntryCollection(OptimadeEntryCollection):
    def __init__(
        self, collection, resource_cls: EntryResource, resource_mapper: ResourceMapper
    ):
        self.collection = collection
        self.parser = LarkParser()
        self.resource_cls = resource_cls
        self.resource_mapper = resource_mapper

    @staticmethod
    def _find(entity_type: orm.Entity, **kwargs) -> orm.QueryBuilder:
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


class AiidaCollection(EntryCollection):
    """Collection of AiiDA entities"""

    def __init__(
        self,
        collection: orm.entities.Collection,
        resource_cls: EntryResource,
        resource_mapper: ResourceMapper,
    ):
        super().__init__(collection, resource_cls, resource_mapper)

        self.transformer = AiidaTransformer()
        self.provider = CONFIG.provider
        self.provider_fields = CONFIG.provider_fields
        self.page_limit = CONFIG.page_limit
        self.parser = LarkParser(version=(0, 9, 7))

    def __len__(self) -> int:
        return self.collection.query().count()

    def __contains__(self, entry) -> bool:
        return self.collection.count(filters={"uuid": entry.uuid}, limit=1) > 0

    def count(self, **kwargs) -> int:
        offset = kwargs.get("offset", 0)
        for key in list(kwargs.keys()):
            if key not in ("filters", "order_by"):
                del kwargs[key]
        return self.collection.count(**kwargs) - offset

    def find(
        self, params: Union[EntryListingQueryParams, SingleEntryQueryParams]
    ) -> Tuple[List[EntryResource], bool, NonnegativeInt, set]:
        criteria = self._parse_params(params)

        if isinstance(params, EntryListingQueryParams):
            nresults_total = self.count(**criteria)
            nresults_now = min(criteria["limit"], nresults_total)

            more_data_available = nresults_now < nresults_total
            data_available = nresults_total
        else:
            more_data_available = False
            data_available = self.count(**criteria)
            if data_available != 1:
                raise HTTPException(
                    status_code=404,
                    detail=f"Instead of a single entry, {data_available} entries were found",
                )

        all_fields = criteria.pop("fields")
        if getattr(params, "response_fields", False):
            fields = set(params.response_fields.split(","))
        else:
            fields = all_fields.copy()

        results = []
        for entity in self._find(self.collection.entity_type, **criteria).all():
            results.append(
                self.resource_cls(
                    **self.resource_mapper.map_back(
                        dict(zip(criteria["project"], entity))
                    )
                )
            )

        if isinstance(params, SingleEntryQueryParams):
            results = results[0]

        return results, more_data_available, data_available, all_fields - fields

    def _alias_filter(self, filter_: dict) -> dict:
        res = {}
        for key, value in filter_.items():
            new_value = value
            if isinstance(value, dict):
                new_value = self._alias_filter(value)
            res[self.resource_mapper.alias_for(key)] = new_value
        return res

    def _parse_params(self, params: EntryListingQueryParams) -> dict:
        cursor_kwargs = {}

        # filter
        if getattr(params, "filter", False):
            tree = self.parser.parse(params.filter)
            aiida_filter = self.transformer.transform(tree)
            cursor_kwargs["filters"] = self._alias_filter(aiida_filter)
        else:
            cursor_kwargs["filters"] = {}

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
            limit = self.page_limit
            if params.page_limit != self.page_limit:
                limit = params.page_limit
            if limit > self.page_limit:
                raise HTTPException(
                    status_code=403,
                    detail=f"Max page_limit is {self.page_limit}, you requested {limit}",
                )
            if limit == 0:
                limit = self.page_limit
            cursor_kwargs["limit"] = limit

        # response_fields
        # All OPTiMaDe fields
        fields = {"id", "type"}
        fields |= self.get_attribute_fields()
        # All provider-specific fields
        fields |= {self.provider + _ for _ in self.provider_fields}
        cursor_kwargs["fields"] = fields
        cursor_kwargs["project"] = list(
            {self.resource_mapper.alias_for(f) for f in fields}
        )

        # sort
        if getattr(params, "sort", False):
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
        if getattr(params, "page_offset", False):
            cursor_kwargs["offset"] = params.page_offset

        return cursor_kwargs
