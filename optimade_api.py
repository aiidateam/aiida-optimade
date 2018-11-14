# -*- coding: utf-8 -*-
from optimade.filter import Parser
from lark import Transformer
from datetime import datetime
import re

"""
OPTiMaDe
"""

# Default / config
# api_versions = ["v0.9.5", "v1", "v0.8.5", "v0.9.4", "v1.1"]
api_versions = ["v0.9.5"]
api_version_latest = sorted(api_versions)[-1]
base_url = "http://127.0.0.1:5000/optimade/"

response_limit_default = 100
response_format_default = 'json'
response_fields_default = ['type', 'id', 'attributes', 'links', 'meta', 'relationships']

response_limit = response_limit_default
db_max_limit = 1000

formats = ['json']
response_format = response_format_default

user_email_address = 'anonymous@optimade.com'

response_fields = response_fields_default

# Endpoints
entry_listings = ['computers', 'nodes', 'calculations', 'data', 'codes',
                  'structures', 'kpoints', 'bands', 'upfs', 'cifs', 'users', 'groups']
# entry_listings = [ 'structures' ]


################################ FUNCTIONS #####################################

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


def json_error(status=400, title="ValueError", detail=None, pointer="/",
               parameter=None):
    """
    JSON API Error Object
    https://jsonapi.org/format/#error-objects


    """

    error = {
        "status": str(status) ,
        "title": title ,
        "detail": detail ,
        "source": {
            "pointer": pointer ,
            "parameter": parameter
        }
    }

    return error


def common_response(endpoint):
    """
    :endpoint: String with part of URL following the base URL
    """

    endpoint_list = endpoint.split('/')
    if re.match(r'v[\d.?]+', endpoint_list[1]):
        api_version = endpoint_list[1]
        endpoint_list.remove(api_version)
        endpoint = '/'.join(endpoint_list)
    else:
        api_version = api_version_latest

    response = {
        "links": {
            "next": None ,
            "base_url": base_url + api_version + "/"
        },
        "meta": {
            "query": {
                "representation": endpoint
            },
            "api_version": api_version_latest ,
            "time_stamp": datetime.utcnow().strftime( '%Y-%m-%dT%H:%M:%SZ' ) ,
            "data_returned": 1 ,            # General case
            "more_data_available": False ,  # General case
        },
        "data": []
    }

    return response


def baseurl_info(response):
    """
    Return "optimade/info/" endpoint
    ---

    :response: Existing dict of response

    Base URL                            "/"

    # TODO:
    # Extra info concerning either:
    #     o Type-specific entry listing   "/structures" , "/calculations" , ...
    #     o General entry listing         "/all"
    """

    tuple_versions = sorted(api_versions_as_tuples(api_versions), reverse=True)

    # Create "available_api_versions"-dict with latest version
    last_ver = tuple_versions[0]
    if last_ver[0] == "0":
        version_url = '.'.join(last_ver[:2])
    else:
        version_url = last_ver[0]
    available_api_versions = {'.'.join(last_ver): base_url + "v" + version_url + "/"}

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
        available_api_versions['.'.join(cur_ver)] = base_url + "v" + version_url + "/"

        # Update previously added version
        last_ver = cur_ver

    # Base URL "/info"-response
    data = {
        "type": "info",
        "id": "/",
        "attributes": {
            "api_version": api_version_latest,
            "available_api_versions": available_api_versions,
            "formats": formats,
            "entry_types_by_format": {
                "json": ['structure']
            }
        }
    }

    response["data"].append(data)

    return response


def structure_info(response):
    """
    :response: Existing dict of response
    """

    # /structures "/info"-response
    data = {
        "type": "info",
        "id": "/structures",
        "description": "a structure",
        "properties": {
            "nelements": {
                "description": "number of elements",
                "unit": None
            },
            "elements": {
                "description": "list of elements",
                "unit": None
            }
        },
        "formats": ['json'],
        "output_fields_by_format": {
            "json": ["nelements", "elements"]
        }
    }

    response["data"].append(data)

    return response


def calculation_info(response):
    """
    :response: Existing dict of response
    """

    # /calculation "/info"-response
    data = {
        "type": "info",
        "id": "/calculations",
        "description": "a calculation",
        "properties": {
            "code": {
                "description": "code used for calculation",
                "unit": None
            }
        },
        "formats": ['json'],
        "output_fields_by_format": {
            "json": ["code"]
        }
    }

    response["data"].append(data)

    return response


def valid_version(api_version):
    """
    :api_version: string of single api_version, ex.: "0.9.5" or "1.1" or "2"

    return boolean
    """

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
    :api_version: string of single api_version, ex.: "0.9.5" or "1.1" or "2"

    return boolean
    """

    if not valid_version(api_version): raise ValueError

    api_version_list = api_version.split('.')
    api_version_latest_list = list(api_versions_as_tuples([api_version_latest])[0])

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
    :limit: integer as string, new queried response_limit
            if limit=default, response_limit will be reset to default
    """

    global response_limit

    if limit == "default":
        response_limit = response_limit_default
        return "200"

    try:
        limit = int(limit)
    except ValueError:
        msg = "response_limit must be 'default' or an integer"
        error = json_error(detail=msg, parameter="response_limit")
        return error

    if limit <= db_max_limit:
        response_limit = limit
        return "200"
    else:
        msg = "Request not allowed by database. Max response_limit = " + str(db_max_limit)
        error = json_error(status=403, detail=msg, parameter="response_limit")
        return error


def query_response_format(format):
    """
    Only allowed formats: jsonapi / json

    :format: string, new queried response_format
             if format=default, response_format will be reset to default
    """

    global response_format

    if format in [ "default", "jsonapi", "json" ]:
        response_format = response_format_default
        return "200"
    elif format in formats:
        response_format = format
        return "200"
    else:
        # Not (yet) allowed format
        msg = "Requested format '" + format + \
              "' not allowed or not yet implemented. Implemented formats: "
        for format in formats: msg += "'" + format + "',"
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
            response_fields = response_fields_default
            return "200"
        elif field not in response_fields_default:
            # Not valid field
            msg = "Requested field '" + field + "' is not valid"
            error = json_error(status=418, detail=msg, parameter="response_fields")
            return error

    response_fields = fields
    return "200"


# Function mapping for queries
query_parameters = {
    'filter': None ,
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


################################## CLASSES #####################################

class TreeToPy(Transformer):

    # def VALUE(self, s):
    #     if isinstance(s, str):
    #         return token.value()
    #     elif isinstance(s, int):
    #         return int(s)
    #     elif isinstance(s, float):
    #         return float(s)
    #     else:
    #         raise
    # def OPERATOR(self, o):
    #     return str(o[1:-1])
    # def KEYWORD(self, s):
    #     self.assertEqual(s, "test")
    #     self.assertTrue(1==2)
    #     print("from KEYWORD")
    #     return str(s)
    # def AND(self, o):
    #     return o.value()
    # def OR(self, o):
    #     return str(o)
    # def NOT(self, o):
    #     return str(o)

    start = tuple
    expression = list
    term = list
    atom = list
    andcomparison = list
    comparison = tuple

    null = lambda self, _: None
    true = lambda self, _: True
    false = lambda self, _: False

    # def VALUE(self, )
    #     pass
    # pass

################################################################################


"""
Flask app
"""

from flask import Flask, url_for, request, redirect, jsonify

app = Flask(__name__)

nl = '<br/>'


@app.route('/')
def index():
    # Go to start: /optimade/
    return redirect(url_for('optimade'))


@app.route('/optimade/')
def optimade():
    # Default base_url

    ##### TESTING ######

    p = Parser()
    version = 'v' + '.'.join(str(v) for v in p.version)
    out = 'OPTiMaDe - version: ' + version + 3*nl

    tree = p.parse("filter=a<3 AND (b=true OR c=true)")
    t = TreeToPy()
    out += str(t.transform(tree)) + 2*nl

    filt = t.transform(tree)
    filt = {filt[0]: filt[1]}

    out += str(filt) + 2*nl

    for k in filt:
        out += k + 2*nl

    def get_condition(condition):
        if isinstance(condition, tuple) and len(condition) == 3:
            return ''.join(condition)
        else:
            return condition

    for v in filt['filter=']:
        v = get_condition(v)
        out += str(v) + " - " + "first" + 2*nl
        if isinstance(v, list):
            for i in v:
                i = get_condition(i)
                out += str(i) + " - " + "second" + 2*nl
                if isinstance(i, list):
                    for j in i:
                        j = get_condition(j)
                        out += str(j) + " - " + "third" + 2*nl
                        if isinstance(j, list):
                            for k in j:
                                k = get_condition(k)
                                out += str(k) + " - " + "fourth" + 2*nl
                                if isinstance(k, list):
                                    for lm in k:
                                        lm = get_condition(lm)
                                        out += str(lm) + " - " + "fifth" + 2*nl
    return out


@app.route('/optimade/v<api_version>/')
def vapi_version(api_version):
    if re.match(r'[\d.?]+', api_version): # TODO: Make regexp better to determine version syntax
        if valid_version(api_version) and not legacy_version(api_version):
            #  Latest version
            return redirect(url_for('optimade'))
        elif valid_version(api_version):
            # Valid legacy version
            return 'You are looking at valid legacy OPTiMaDe version: ' + api_version
        else:
            # Invalid version
            return 'You are looking at an INVALID OPTiMaDe version: ' + api_version + ' - last option', 400
    else:
        # InputError
        return "bad request", 400


@app.route('/<path:endpoint>/info/')
def info(endpoint):
    base_api_url = base_url.split('/')[-2]

    endpoint = endpoint.split('/')

    if endpoint[0] != base_api_url:
        # error
        return '/'.join(endpoint) + "/info" + nl + "Error 400: Bad request", 400

    elif len(endpoint) == 1:
        # /optimade/info
        response = common_response("/info/")
        response = baseurl_info(response)
        return jsonify(response)

    elif len(endpoint) == 2 and endpoint[-1] in entry_listings:
        # /optimade/<entry_listing>/info
        entry_listing = endpoint[-1]
        response = common_response("/" + entry_listing + "/info/")
        response = entry_listing_infos[entry_listing](response)
        return jsonify(response)

    elif len(endpoint) == 2 and valid_version(endpoint[-1][1:]):
        # /optimade/v<api_version>/info
        api_version = endpoint[-1][1:]
        if legacy_version(api_version):
            # Legal legacy version
            return "/info of legal legacy version: v" + api_version
        else:
            # Latest version. Equivalent to "/optimade/info"
            response = common_response("/v" + api_version + "/info/")
            response = baseurl_info(response)
            return jsonify(response)

    elif len(endpoint) == 3 and valid_version(endpoint[-2][1:]) \
            and endpoint[-1] in entry_listings:
        # /optimade/v<api_version>/<entry_listing>/info
        api_version = endpoint[1][1:]
        entry_listing = endpoint[-1]

        if legacy_version(api_version):
            # Legal legacy version
            return endpoint[-1] + "/info of legal legacy version: v" + api_version
        else:
            # Latest version. Equivalent to "/optimade/<entry_listing>/info"
            response = common_response("/" + "/".join(endpoint[1:]) + "/info/")
            response = entry_listing_infos[entry_listing](response)
            return jsonify(response)

        # response = common_response("/" + '/'.join(endpoint[1:]) + "/info")
        # TODO: Create func() to return info for each entry_listing with different version
        # return jsonify(response)

    # else not valid path
    return '/'.join(endpoint) + "/info" + nl + "Error 400: Bad request - last else clause", 400


@app.route('/optimade/all')
def all():

    return "Return all entries"


@app.route('/optimade/structures')
def structures():
    # Get possible queries
    queries = request.args

    # BASE response
    representation = "/structures"
    if queries: representation += "?"
    response = common_response(representation)

    for query in queries:
        # Get value of query
        query_value = queries[query]

        # Add query-value-pair to "representation"-url meta-key
        if response["meta"]["query"]["representation"][-1] == "?":
            representation = query + "=" + query_value
        else:
            representation = "&" + query + "=" + query_value
        response["meta"]["query"]["representation"] += representation

        if query in query_parameters:
            # Valid query key

            if query != "filter": # Filter query is treated separately
                eval = query_parameters[query](query_value)

                # Error
                if isinstance(eval, dict) and eval["status"]:
                    eval["source"]["pointer"] = "/structures"
                    if "errors" in response:
                        response["errors"].append(eval)
                    else:
                        response["errors"] = [eval]
                # Success
                elif isinstance(eval, str) and eval == "200":
                    pass
            # ?filter=
            elif query == "filter":
                pass
            else:
                msg = "Unknown error during query evaluation. Query: " + \
                      query + "=" + query_value
                error = json_error(status=404, detail=msg, pointer="/structures", parameter=query)
                if "errors" in response:
                    response["errors"].append(error)
                else:
                    response["errors"] = [error]

            continue

        else:
            msg = "Invalid query parameter: '" + query + "' Legal query parameters: "
            for param in query_parameters: msg += "'" + param + "',"
            msg = msg[:-1]
            error = json_error(status=418, detail=msg, pointer="/structures", parameter=query)
            if "errors" in response:
                response["errors"].append(error)
            else:
                response["errors"] = [error]

    if "errors" in response:
        if len(response["errors"]) > 1:
            # Returning most generally applicable HTTP error according to JSON
            # API Error Objects description. Here: 4xx errors
            return jsonify(response), 400
        else:
            return jsonify(response), int(response["errors"]["status"])
    else:
        return jsonify(response)
