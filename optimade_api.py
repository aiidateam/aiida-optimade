# -*- coding: utf-8 -*-
from optimade.filter import Parser
from lark import Transformer
import re
import config
from utils import valid_version, legacy_version, common_response, baseurl_info, entry_listing_infos, query_parameters, json_error

"""
OPTiMaDe
"""

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
    base_api_url = config.BASE_URL.split('/')[-2]

    endpoint = endpoint.split('/')

    if endpoint[0] != base_api_url:
        # error
        return '/'.join(endpoint) + "/info" + nl + "Error 400: Bad request", 400

    elif len(endpoint) == 1:
        # /optimade/info
        response = common_response("/info/")
        response = baseurl_info(response)
        return jsonify(response)

    elif len(endpoint) == 2 and endpoint[-1] in config.ENTRY_LISTINGS:
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
            and endpoint[-1] in config.ENTRY_LISTINGS:
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
