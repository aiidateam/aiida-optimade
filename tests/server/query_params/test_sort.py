"""Test sort query parameter"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from typing import Any, Callable, Dict, List, Union

    from requests import Response


def fmt_datetime(object_: "datetime") -> str:
    """Parse datetime into pydantic's JSON encoded datetime string"""
    from datetime import timezone

    return object_.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_int_asc(
    get_good_response: "Callable[[str, bool], Union[Dict[str, Any], Response]]",
) -> None:
    """Ascending sort (integer)"""
    from aiida import orm
    from optimade.server.config import CONFIG, SupportedBackend

    limit = 5

    request = f"/structures?sort=nelements&page_limit={limit}"

    if CONFIG.database_backend == SupportedBackend.MONGODB:
        from aiida_optimade.routers.structures import STRUCTURES_MONGO

        expected_nelements = [
            _["nelements"]
            for _ in STRUCTURES_MONGO.collection.find(
                filter={},
                projection=["nelements"],
                sort=[("nelements", 1)],
                limit=limit,
            )
        ]
    else:
        builder = (
            orm.QueryBuilder(limit=5)
            .append(orm.Node, project="extras.optimade.nelements")
            .order_by(
                {
                    orm.Node: [
                        {"extras.optimade.nelements": {"order": "asc", "cast": "i"}}
                    ]
                }
            )
        )
        expected_nelements = [nelement for nelement, in builder.all()]

    response: "Dict[str, Any]" = get_good_response(request, False)
    nelements_list = [
        struct.get("attributes", {}).get("nelements") for struct in response["data"]
    ]
    assert nelements_list == expected_nelements


def test_int_desc(
    get_good_response: "Callable[[str, bool], Union[Dict[str, Any], Response]]",
) -> None:
    """Descending sort (integer)"""
    from aiida import orm
    from optimade.server.config import CONFIG, SupportedBackend

    limit = 5

    request = f"/structures?sort=-nelements&page_limit={limit}"

    if CONFIG.database_backend == SupportedBackend.MONGODB:
        from aiida_optimade.routers.structures import STRUCTURES_MONGO

        expected_nelements = [
            _["nelements"]
            for _ in STRUCTURES_MONGO.collection.find(
                filter={},
                projection=["nelements"],
                sort=[("nelements", -1)],
                limit=limit,
            )
        ]
    else:
        builder = (
            orm.QueryBuilder(limit=limit)
            .append(orm.Node, project="extras.optimade.nelements")
            .order_by(
                {
                    orm.Node: [
                        {"extras.optimade.nelements": {"order": "desc", "cast": "i"}}
                    ]
                }
            )
        )
        expected_nelements = [nelement for nelement, in builder.all()]

    response: "Dict[str, Any]" = get_good_response(request, False)
    nelements_list = [
        struct.get("attributes", {}).get("nelements") for struct in response["data"]
    ]
    assert nelements_list == expected_nelements


def test_str_asc(
    check_response: "Callable[[str, List[str], int, bool, bool], None]",
) -> None:
    """Ascending sort (string)"""
    from aiida import orm
    from optimade.server.config import CONFIG, SupportedBackend

    request = "/structures?sort=immutable_id&page_limit=5"

    if CONFIG.database_backend == SupportedBackend.MONGODB:
        from aiida_optimade.routers.structures import STRUCTURES_MONGO

        expected_ids = [
            _["id"]
            for _ in STRUCTURES_MONGO.collection.find(
                filter={},
                projection=["id"],
                sort=[("immutable_id", 1)],
            )
        ]
    else:
        builder = (
            orm.QueryBuilder()
            .append(orm.Node, project="id")
            .order_by({orm.Node: [{"uuid": {"order": "asc", "cast": "t"}}]})
        )
        expected_ids = [str(_[0]) for _ in builder.all()]
    check_response(
        request,
        expected_uuid=expected_ids,
        expect_id=True,
        expected_as_is=True,
        page_limit=5,
    )


def test_str_desc(
    check_response: "Callable[[str, List[str], int, bool, bool], None]",
) -> None:
    """Descending sort (string)"""
    from aiida import orm
    from optimade.server.config import CONFIG, SupportedBackend

    request = "/structures?sort=-immutable_id&page_limit=5"

    if CONFIG.database_backend == SupportedBackend.MONGODB:
        from aiida_optimade.routers.structures import STRUCTURES_MONGO

        expected_ids = [
            _["id"]
            for _ in STRUCTURES_MONGO.collection.find(
                filter={},
                projection=["id"],
                sort=[("immutable_id", -1)],
            )
        ]
    else:
        builder = (
            orm.QueryBuilder()
            .append(orm.Node, project="id")
            .order_by({orm.Node: [{"uuid": {"order": "desc", "cast": "t"}}]})
        )
        expected_ids = [str(_[0]) for _ in builder.all()]
    check_response(
        request,
        expected_uuid=expected_ids,
        expect_id=True,
        expected_as_is=True,
        page_limit=5,
    )


def test_datetime_asc(
    get_good_response: "Callable[[str, bool], Union[Dict[str, Any], Response]]",
) -> None:
    """Ascending sort (datetime)"""
    from aiida import orm
    from optimade.server.config import CONFIG, SupportedBackend

    request = "/structures?sort=last_modified&page_limit=5"

    if CONFIG.database_backend == SupportedBackend.MONGODB:
        from aiida_optimade.routers.structures import STRUCTURES_MONGO

        expected_mtime = [
            fmt_datetime(_["last_modified"])
            for _ in STRUCTURES_MONGO.collection.find(
                filter={},
                projection=["last_modified"],
                sort=[("last_modified", 1)],
                limit=5,
            )
        ]
    else:
        builder = (
            orm.QueryBuilder(limit=5)
            .append(orm.Node, project="mtime")
            .order_by({orm.Node: [{"mtime": {"order": "asc", "cast": "i"}}]})
        )
        expected_mtime = [fmt_datetime(mtime) for mtime, in builder.all()]

    response: "Dict[str, Any]" = get_good_response(request, False)
    last_modified_list = [
        struct.get("attributes", {}).get("last_modified") for struct in response["data"]
    ]
    assert last_modified_list == expected_mtime


def test_datetime_desc(
    get_good_response: "Callable[[str, bool], Union[Dict[str, Any], Response]]",
) -> None:
    """Descending sort (datetime)"""
    from aiida import orm
    from optimade.server.config import CONFIG, SupportedBackend

    request = "/structures?sort=-last_modified&page_limit=5"

    if CONFIG.database_backend == SupportedBackend.MONGODB:
        from aiida_optimade.routers.structures import STRUCTURES_MONGO

        expected_mtime = [
            fmt_datetime(_["last_modified"])
            for _ in STRUCTURES_MONGO.collection.find(
                filter={},
                projection=["last_modified"],
                sort=[("last_modified", -1)],
                limit=5,
            )
        ]
    else:
        builder = (
            orm.QueryBuilder(limit=5)
            .append(orm.Node, project="mtime")
            .order_by({orm.Node: [{"mtime": {"order": "desc", "cast": "i"}}]})
        )
        expected_mtime = [fmt_datetime(mtime) for mtime, in builder.all()]

    response: "Dict[str, Any]" = get_good_response(request, False)
    last_modified_list = [
        struct.get("attributes", {}).get("last_modified") for struct in response["data"]
    ]
    assert last_modified_list == expected_mtime
