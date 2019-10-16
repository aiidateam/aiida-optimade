from abc import abstractmethod
from configparser import ConfigParser
from pathlib import Path
from typing import Collection, Tuple, List, Union

import aiida
import mongomock
import pymongo.collection
from fastapi import HTTPException
from optimade.filterparser import LarkParser
from optimade.filtertransformers.mongo import MongoTransformer

from transformers import AiidaTransformer
from models import NonnegativeInt
from models import Resource
from models import StructureMapper
from deps import EntryListingQueryParams


config = ConfigParser()
config.read(Path(__file__).resolve().parent.joinpath("config.ini"))
PAGE_LIMIT = config["DEFAULT"].getint("PAGE_LIMIT")
DB_PAGE_LIMIT = config["DB_SPECIFIC"].getint("PAGE_LIMIT")


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
        self, collection: aiida.orm.entities.Collection, resource_cls: Resource
    ):
        super().__init__(collection, resource_cls)
        self.transformer = AiidaTransformer()

    def __len__(self) -> int:
        return self.collection.query().count()

    def __contains__(self, entry) -> bool:
        return self.collection.count(filters={"uuid": entry.uuid}, limit=1) > 0

    def count(self, **kwargs) -> int:
        for key in list(kwargs.keys()):
            if key not in ("filter", "order_by", "limit", "offset"):
                del kwargs[key]
        return self.collection.count(**kwargs)

    def find(
        self, params: EntryListingQueryParams
    ) -> Tuple[List[Resource], bool, NonnegativeInt]:
        criteria = self._parse_params(params)

        criteria_nolimit = criteria.copy()
        del criteria_nolimit["limit"]

        nresults_now = self.count(**criteria)
        nresults_total = self.count(**criteria_nolimit)

        more_data_available = nresults_now < nresults_total
        data_available = nresults_total
        results = []

        for entity in self.collection.find(**criteria):
            results.append(self.resource_cls(**self.resource_mapper.map_back(entity)))

        return results, more_data_available, data_available

    def _parse_params(self, params: EntryListingQueryParams) -> dict:
        cursor_kwargs = {}

        # filter
        if params.filter:
            tree = self.parser.parse(params.filter)
            cursor_kwargs["filter"] = self.transformer.transform(tree)
        else:
            cursor_kwargs["filter"] = {}

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
            fields = {"id", "type", "attributes"}
        cursor_kwargs["projection"] = [
            self.resource_mapper.alias_for(f) for f in fields
        ]

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


class MongoCollection(EntryCollection):
    def __init__(
        self,
        collection: Union[
            pymongo.collection.Collection, mongomock.collection.Collection
        ],
        resource_cls: Resource,
    ):
        super().__init__(collection, resource_cls)
        self.transformer = MongoTransformer()

    def __len__(self):
        return self.collection.estimated_document_count()

    def __contains__(self, entry):
        return self.collection.count_documents(entry.dict()) > 0

    def count(self, **kwargs):
        for k in list(kwargs.keys()):
            if k not in ("filter", "skip", "limit", "hint", "maxTimeMS"):
                del kwargs[k]
        return self.collection.count_documents(**kwargs)

    def find(
        self, params: EntryListingQueryParams
    ) -> Tuple[List[Resource], bool, NonnegativeInt]:
        criteria = self._parse_params(params)
        criteria_nolimit = criteria.copy()
        del criteria_nolimit["limit"]
        nresults_now = self.count(**criteria)
        nresults_total = self.count(**criteria_nolimit)
        more_data_available = nresults_now < nresults_total
        data_available = nresults_total
        results = []
        for doc in self.collection.find(**criteria):
            results.append(self.resource_cls(**StructureMapper.map_back(doc)))
        return results, more_data_available, data_available

    def _parse_params(self, params: EntryListingQueryParams) -> dict:
        cursor_kwargs = {}

        if params.filter:
            tree = self.parser.parse(params.filter)
            cursor_kwargs["filter"] = self.transformer.transform(tree)
        else:
            cursor_kwargs["filter"] = {}

        if params.response_format and params.response_format != "jsonapi":
            raise HTTPException(
                status_code=400, detail="Only 'jsonapi' response_format supported"
            )

        limit = PAGE_LIMIT
        if params.response_limit != PAGE_LIMIT:
            limit = params.response_limit
        elif params.page_limit != PAGE_LIMIT:
            limit = params.page_limit
        if limit > PAGE_LIMIT:
            raise HTTPException(
                status_code=400,
                detail=f"Max response_limit/page[limit] is {PAGE_LIMIT}",
            )
        if limit == 0:
            limit = PAGE_LIMIT
        cursor_kwargs["limit"] = limit

        fields = {"id", "local_id", "last_modified"}
        if params.response_fields:
            fields |= set(params.response_fields.split(","))
        cursor_kwargs["projection"] = [StructureMapper.alias_for(f) for f in fields]

        if params.sort:
            sort_spec = []
            for elt in params.sort.split(","):
                field = elt
                sort_dir = 1
                if elt.startswith("-"):
                    field = field[1:]
                    sort_dir = -1
                sort_spec.append((field, sort_dir))
            cursor_kwargs["sort"] = sort_spec

        if params.page_offset:
            cursor_kwargs["skip"] = params.page_offset

        return cursor_kwargs
