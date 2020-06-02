from datetime import datetime
from aiida import orm


def fmt_datetime(object_: datetime) -> str:
    """Parse datetime into pydantic's JSON encoded datetime string"""
    as_string = object_.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
    return f"{as_string[:-2]}:{as_string[-2:]}"


def test_int_asc(get_good_response):
    """Ascending sort (integer)"""
    limit = 5

    request = f"/structures?sort=nelements&page_limit={limit}"
    builder = (
        orm.QueryBuilder(limit=5)
        .append(orm.StructureData, project="extras.optimade.nelements")
        .order_by(
            {
                orm.StructureData: [
                    {"extras.optimade.nelements": {"order": "asc", "cast": "i"}}
                ]
            }
        )
    )
    expected_nelements = [nelement for nelement, in builder.all()]

    response = get_good_response(request)
    nelements_list = [
        struct.get("attributes", {}).get("nelements") for struct in response["data"]
    ]
    assert nelements_list == expected_nelements


def test_int_desc(get_good_response):
    """Descending sort (integer)"""
    limit = 5

    request = f"/structures?sort=-nelements&page_limit={limit}"
    builder = (
        orm.QueryBuilder(limit=limit)
        .append(orm.StructureData, project="extras.optimade.nelements")
        .order_by(
            {
                orm.StructureData: [
                    {"extras.optimade.nelements": {"order": "desc", "cast": "i"}}
                ]
            }
        )
    )
    expected_nelements = [nelement for nelement, in builder.all()]

    response = get_good_response(request)
    nelements_list = [
        struct.get("attributes", {}).get("nelements") for struct in response["data"]
    ]
    assert nelements_list == expected_nelements


def test_str_asc(check_response):
    """Ascending sort (string)"""
    request = "/structures?sort=immutable_id&page_limit=5"
    builder = (
        orm.QueryBuilder()
        .append(orm.StructureData, project="id")
        .order_by({orm.StructureData: [{"uuid": {"order": "asc", "cast": "t"}}]})
    )
    expected_ids = [str(id_) for id_, in builder.all()]
    check_response(request=request, expected_id=expected_ids, page_limit=5)


def test_str_desc(check_response):
    """Descending sort (string)"""
    request = "/structures?sort=-immutable_id&page_limit=5"
    builder = (
        orm.QueryBuilder()
        .append(orm.StructureData, project="id")
        .order_by({orm.StructureData: [{"uuid": {"order": "desc", "cast": "t"}}]})
    )
    expected_ids = [str(id_) for id_, in builder.all()]
    check_response(request=request, expected_id=expected_ids, page_limit=5)


def test_datetime_asc(get_good_response):
    """Ascending sort (datetime)"""
    limit = 5

    request = f"/structures?sort=last_modified&page_limit={limit}"
    builder = (
        orm.QueryBuilder(limit=5)
        .append(orm.StructureData, project="mtime")
        .order_by({orm.StructureData: [{"mtime": {"order": "asc", "cast": "i"}}]})
    )
    expected_mtime = [fmt_datetime(mtime) for mtime, in builder.all()]

    response = get_good_response(request)
    last_modified_list = [
        struct.get("attributes", {}).get("last_modified") for struct in response["data"]
    ]
    assert last_modified_list == expected_mtime


def test_datetime_desc(get_good_response):
    """Descending sort (datetime)"""
    limit = 5

    request = f"/structures?sort=-last_modified&page_limit={limit}"
    builder = (
        orm.QueryBuilder(limit=limit)
        .append(orm.StructureData, project="mtime")
        .order_by({orm.StructureData: [{"mtime": {"order": "desc", "cast": "i"}}]})
    )
    expected_mtime = [fmt_datetime(mtime) for mtime, in builder.all()]

    response = get_good_response(request)
    last_modified_list = [
        struct.get("attributes", {}).get("last_modified") for struct in response["data"]
    ]
    assert last_modified_list == expected_mtime
