# -*- coding: utf-8 -*-

import re
import common.config as config
from datetime import datetime


""" 
Utils

Utility functions

TODO: Should be updated so that it ONLY contains utility functions
"""


def api_versions_as_tuples(api_versions, cut="PATCH"):
    """
    :api_versions: list of strings with api versions of the format: "vMAJOR.MINOR.PATCH"
    :cut: string, must be either "MAJOR", "MINOR", or "PATCH".
          Decides length of tuples, i.e. 1, 2, or 3. Default: "PATCH", i.e. 3
    """

    if cut not in ["MAJOR", "MINOR", "PATCH"]:
        raise ValueError

    version_tuple_list = []
    for version in api_versions:
        ver_list = version[1:].split('.')
        ver_tuple = tuple(ver_list)

        if len(ver_tuple) == 1:
            ver_tuple = (ver_tuple[0], '0', '0')
        elif len(ver_tuple) == 2:
            ver_tuple = (ver_tuple[0], ver_tuple[1], '0')
        elif len(ver_tuple) > 3:
            raise ValueError

        if cut == "MAJOR":
            ver_tuple = ver_tuple[:1]
        elif cut == "MINOR":
            ver_tuple = ver_tuple[:2]

        version_tuple_list.append(ver_tuple)

    return version_tuple_list


def json_error(status=400, title="ValueError", detail=None, pointer="/", parameter=None):
    """
    JSON API Error Object
    https://jsonapi.org/format/#error-objects
    """

    error = {
        "status": str(status),
        "title": title,
        "detail": detail,
        "source": {
            "pointer": pointer,
            "parameter": parameter
        }
    }

    return error


def common_response(endpoint, base_url):
    """
    :endpoint: String with part of URL following the base URL
    """

    endpoint_list = endpoint.split('/')
    if re.match(r'v[\d.?]+', endpoint_list[1]):
        api_version = endpoint_list[1]
        endpoint_list.remove(api_version)
        endpoint = '/'.join(endpoint_list)
    else:
        api_version = config.API_VERSION_LATEST

    response = dict(
        links=dict(
            next=None,
            base_url=base_url  # config.BASE_URL + api_version + "/"
        ),
        meta=dict(
            query=dict(
                representation=endpoint
            ),
            api_version=config.API_VERSION_LATEST,
            time_stamp=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            data_returned=1,            # General case
            more_data_available=False,  # General case
        ),
        data=[]
    )

    return response


def baseurl_info(response):
    """
    Return "optimade/info/" endpoint
    ---

    :response: Existing dict of response

    Base URL                            "/"

    # TODO:
    # Extra info concerning either:
    #     o Type-specific entry listing   "/structures", "/calculations" , ...
    #     o General entry listing         "/all/", "/info"
    """

    tuple_versions = sorted(api_versions_as_tuples(config.API_VERSIONS), reverse=True)

    base_url_no_ver = config.BASE_URL + '/'

    # Create "available_api_versions"-dict with latest version
    last_ver = tuple_versions[0]
    if last_ver[0] == "0":
        version_url = '.'.join(last_ver[:2])
    else:
        version_url = last_ver[0]
    available_api_versions = {'.'.join(last_ver): base_url_no_ver + "v" + version_url + "/"}

    # Add legacy versions to "available_api_versions"
    for cur_ver in tuple_versions[1:]:
        if cur_ver[:2] == last_ver[:2]:
            # Same MAJOR.MINOR as previously added version,
            # but current is an older PATCH
            version_url = '.'.join(cur_ver)
        elif cur_ver[0] == last_ver[0] or cur_ver[0] == "0":
            # Same MAJOR as previously added version,
            # but current is an older MINOR
            version_url = '.'.join(cur_ver[:2])
        else:
            # Lower MAJOR than previously added version and NOT "0"
            version_url = cur_ver[0]

        # Add current legacy version to "available_api_versions"
        available_api_versions['.'.join(cur_ver)] = base_url_no_ver + "v" + version_url + "/"

        # Update previously added version
        last_ver = cur_ver

    # Base URL "/info"-response
    data = dict(
        type="info",
        id="/",
        attributes=dict(
            api_version=config.API_VERSION_LATEST,
            available_api_versions=available_api_versions,
            formats=config.FORMATS,
            entry_types_by_format=dict(
                json=['structure']
            )
        )
    )

    response["data"].append(data)

    return response


def all_info(response):
    """

    :param response:
    :return:
    """

    # "/all/info"-response
    data = dict(
        type="info",
        id="/all/",
        description="general entry listing endpoint",
        properties=dict(
            filter=dict(
                description="Filter all entries by separate entry-listing properties"
            ),
            response_fields=dict(
                description="Comma-delimited set of fields to be provided in the output"
            ),
            response_format=dict(
                description="Requested output format. Standard: 'jsonapi'"
            ),
            response_limit=dict(
                description="Numerical limit on the number of entries returned"
            ),
            email_address=dict(
                description="E-mail address of user making the request"
            )
        ),
        formats=["json"],
        output_fields_by_format=dict()
    )

    data["output_fields_by_format"] = dict(json=[key for key in data["properties"]])

    response["data"].append(data)

    return response


def structure_info(response):
    """
    :param response: Existing dict of response
    :return:
    """

    # "/structures/info"-response
    data = dict(
        type="info",
        id="/structures/",
        description="a structure",
        properties=dict(
            nelements=dict(
                description="number of elements",
                unit=None
            ),
            elements=dict(
                description="list of elements",
                unit=None
            )
        ),
        formats=["json"],
        output_fields_by_format=dict()
    )

    data["output_fields_by_format"] = dict(json=[key for key in data["properties"]])

    response["data"].append(data)

    return response


def calculation_info(response):
    """
    :response: Existing dict of response
    """

    # "/calculation/info"-response
    data = dict(
        type="info",
        id="/calculations",
        description="a calculation",
        properties=dict(
            code=dict(
                description="code used for calculation",
                unit=None
            )
        ),
        formats=["json"],
        output_fields_by_format=dict(
            json=["code"]
        )
    )

    response["data"].append(data)

    return response


def valid_version(api_version):
    """
    :param api_version: string of single api_version, ex.: "v0.9.5" or "1.1" or "v2" or "0.9.5"

    :return: boolean
    """

    if re.match(r'v[\d.?]+', api_version):
        api_version = api_version[1:]

    chk_version = baseurl_info({"data": []})
    chk_version = chk_version["data"][0]["attributes"]["available_api_versions"]

    valid = False
    for version, url_version in chk_version.items():
        if api_version == version:                          valid = True
        if api_version == url_version.split('/')[-2][1:]:   valid = True
        version_list = version.split('.')
        if version_list[-1] == "0" and \
            api_version == '.'.join(version_list[:-1]):     valid = True

    return valid


def legacy_version(api_version):
    """
    :param api_version: string of single api_version, ex.: "0.9.5" or "1.1" or "2"

    :return: boolean
    """

    if not valid_version(api_version): raise ValueError

    api_version_list = api_version.split('.')
    api_version_latest_list = list(api_versions_as_tuples([config.API_VERSION_LATEST])[0])

    # Latest MAJOR.MINOR.PATCH version chosen
    if len(api_version_list) == 3 and api_version_list == api_version_latest_list:
        return False

    # Latest MAJOR.MINOR version chosen
    elif len(api_version_list) == 2 and api_version_list == api_version_latest_list[:2]:
        return False

    # Latest MAJOR version that is NOT "0"
    elif len(api_version_list) == 1 and api_version_list[0] != "0" \
            and api_version_list[0] == api_version_latest_list[0]:
        return False

    else:
        return True


def query_response_limit(limit):
    """
    :param limit: integer as string, new queried response_limit
                  if limit=default, response_limit will be reset to default
    """

    global response_limit

    if limit == "default":
        response_limit = config.RESPONSE_LIMIT_DEFAULT
        return "200"

    try:
        limit = int(limit)
    except ValueError:
        msg = "response_limit must be 'default' or an integer"
        error = json_error(detail=msg, parameter="response_limit")
        return error

    if limit <= config.DB_MAX_LIMIT:
        response_limit = limit
        return "200"
    else:
        msg = "Request not allowed by database. Max response_limit = " + str(config.DB_MAX_LIMIT)
        error = json_error(status=403, detail=msg, parameter="response_limit")
        return error


def query_response_format(fmt):
    """
    Only allowed formats: jsonapi / json

    :format: string, new queried response_format
             if format=default, response_format will be reset to default
    """

    global response_format

    if fmt in [ "default", "jsonapi", "json" ]:
        response_format = config.RESPONSE_FORMAT_DEFAULT
        return "200"
    elif fmt in config.FORMATS:
        response_format = fmt
        return "200"
    else:
        # Not (yet) allowed format
        msg = "Requested format '" + fmt + \
              "' not allowed or not yet implemented. Implemented formats: "
        for fmt in config.FORMATS: msg += "'" + fmt + "',"
        msg = msg[:-1]
        error = json_error(status=418, detail=msg, parameter=response_format)
        return error


def query_email_address(email):
    """
    :email: string, new specified user e-mail-address
    """

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        # Not proper e-mail-format
        msg = "E-mail-address format not correct. Example: user@example.com"
        error = json_error(status=400, detail=msg, parameter="email_address")
        return error
    else:
        global user_email_address
        user_email_address = email
        return "200"


def query_response_fields(fields):
    """
    :fields: comma-separated string, queried response_fields
             if fields=default, response_fields will be reset to default
    """

    global response_fields

    fields = fields.split(',')
    for field in fields:
        if field == "default":
            # Reset response_fields to default
            response_fields = config.RESPONSE_FIELDS_DEFAULT
            return "200"
        elif field not in config.RESPONSE_FIELDS_DEFAULT:
            # Not valid field
            msg = "Requested field '" + field + "' is not valid"
            error = json_error(status=418, detail=msg, parameter="response_fields")
            return error

    response_fields = fields
    return "200"


# Function mapping for queries
query_parameters = {
    'filter': None,
    'response_format': query_response_format,
    'email_address': query_email_address,
    'response_limit': query_response_limit,
    'response_fields': query_response_fields
}

# Function mapping for <entry_listing>/info/
entry_listing_infos = {
    'structures': structure_info,
    'calculations': calculation_info
}

##### FROM AiiDA CODE #####


def list_routes():
    """List available routes"""
    from six.moves import urllib
    from flask import current_app

    output = []
    for rule in current_app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue

        methods = ','.join(rule.methods)
        line = urllib.parse.unquote("{:15s} {:20s} {}".format(rule.endpoint, methods, rule))
        output.append(line)

    return sorted(set(output))
