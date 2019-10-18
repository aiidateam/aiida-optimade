import urllib
import json
from configparser import ConfigParser
from datetime import datetime
from pathlib import Path
from typing import Union

from fastapi import FastAPI, Depends
from starlette.requests import Request
from aiida import orm, load_profile

from aiida_optimade.deps import EntryListingQueryParams
from aiida_optimade.collections_test import AiidaCollection
from aiida_optimade.models import Link
from aiida_optimade.models import ToplevelLinks
from aiida_optimade.models import (
    StructureResource,
    StructureMapper,
    StructureResourceAttributes,
)
from aiida_optimade.models import EntryInfoResource
from aiida_optimade.models import BaseInfoResource, BaseInfoAttributes
from aiida_optimade.models import (
    ResponseMeta,
    ResponseMetaQuery,
    StructureResponseMany,
    InfoResponse,
    Provider,
    Failure,
    EntryInfoResponse,
)

config = ConfigParser()
config.read(Path(__file__).resolve().parent.joinpath("config.ini"))

app = FastAPI(
    title="OPTiMaDe API",
    description=(
        "The [Open Databases Integration for Materials Design (OPTiMaDe) consortium]"
        "(http://http://www.optimade.org/) aims to make materials databases interoperational"
        " by developing a common REST API."
    ),
    version="0.9",
)

load_profile()
structures = AiidaCollection(
    orm.StructureData.objects, StructureResource, StructureMapper
)

test_structures_path = (
    Path(__file__).resolve().parent.joinpath("tests/test_structures.json")
)


def meta_values(url, data_returned, data_available, more_data_available=False):
    """Helper to initialize the meta values"""
    parse_result = urllib.parse.urlparse(url)
    return ResponseMeta(
        query=ResponseMetaQuery(
            representation=f"{parse_result.path}?{parse_result.query}"
        ),
        api_version="v0.10",
        time_stamp=datetime.utcnow(),
        data_returned=data_returned,
        more_data_available=more_data_available,
        provider=Provider(
            name="AiiDA",
            description="AiiDA: Automated Interactive Infrastructure and Database for Computational Science (http://www.aiida.net)",
            prefix="aiida",
            homepage="http://www.aiida.net",
            index_base_url=None,
        ),
        data_available=data_available,
    )


def update_schema(app):
    """Update OpenAPI schema in file 'local_openapi.json'"""
    with open("local_openapi.json", "w") as f:
        json.dump(app.openapi(), f, indent=2)


@app.get(
    "/structures",
    response_model=Union[StructureResponseMany, Failure],
    response_model_skip_defaults=True,
    tags=["Structure"],
)
def get_structures(request: Request, params: EntryListingQueryParams = Depends()):
    results, more_data_available, data_available = structures.find(params)
    parse_result = urllib.parse.urlparse(str(request.url))
    if more_data_available:
        query = urllib.parse.parse_qs(parse_result.query)
        query["page_offset"] = int(query.get("page_offset", ["0"])[0]) + len(results)
        urlencoded = urllib.parse.urlencode(query, doseq=True)
        links = ToplevelLinks(
            next=Link(
                href=f"{parse_result.scheme}://{parse_result.netloc}{parse_result.path}?{urlencoded}"
            )
        )
    else:
        links = ToplevelLinks(next=None)
    return StructureResponseMany(
        links=links,
        data=results,
        meta=meta_values(
            str(request.url), len(results), data_available, more_data_available
        ),
    )


@app.get(
    "/info",
    response_model=Union[InfoResponse, Failure],
    response_model_skip_defaults=True,
    tags=["Info"],
)
def get_info(request: Request):
    print(request.url)
    return InfoResponse(
        meta=meta_values(str(request.url), 1, 1, more_data_available=False),
        data=BaseInfoResource(
            attributes=BaseInfoAttributes(
                api_version="v0.10",
                available_api_versions=[
                    {"url": "http://localhost:5000/", "version": "0.10.0"}
                ],
            )
        ),
    )


@app.get(
    "/info/structures",
    response_model=Union[EntryInfoResponse, Failure],
    response_model_skip_defaults=True,
    tags=["Structure", "Info"],
)
def get_structures_info(request: Request):
    fields = StructureResource.schema()["properties"]
    properties = {
        field: {"description": value.get("description", "")}
        for field, value in fields.items()
    }

    del properties["attributes"]
    fields = StructureResourceAttributes.schema()["properties"]
    properties = {
        field: {"description": value.get("description", "")}
        for field, value in fields.items()
    }

    return EntryInfoResponse(
        meta=meta_values(str(request.url), 1, 1, more_data_available=False),
        data=EntryInfoResource(
            description="Endpoint to represent AiiDA StructureData Nodes in the OPTiMaDe format",
            properties=properties,
            output_fields_by_format={"json": list(fields.keys())},
        ),
    )


@app.on_event("startup")
async def startup_event():
    update_schema(app)
