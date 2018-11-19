# -*- coding: utf-8 -*-

from optimade.filter import Parser
from transformers import TreeToPy
import re
import common.config as config
from common.utils import valid_version, legacy_version, common_response, baseurl_info, entry_listing_infos, query_parameters, \
    json_error, all_info
from flask import url_for, request, redirect, jsonify
from flask_restful import Resource

nl = '<br/>'


class Optimade(Resource):
    def get(self):
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


class ApiVersion(Resource):
    def get(self, api_version):
        if re.match(r'[\d.?]+', api_version):  # TODO: Make regexp better to determine version syntax
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


class Info(Resource):
    def get(self):

        # Decode url-path
        path = request.path
        endpoint = path.split('/')[3]

        # base_api_url = config.PREFIX.split('/')[1]

        # endpoint = request.path.split('/')
        # endpoint = endpoint[1:-1]

        # if endpoint[0] != base_api_url:
        #     # error
        #     return '/'.join(endpoint) + "/info" + nl + "Error 400: Bad request, no optimade", 400

        if endpoint == 'info':
            # /info
            response = common_response("/info", config.BASE_URL)
            response = baseurl_info(response)
            return jsonify(response)

        elif endpoint == 'all':
            # /all/info
            response = common_response("/all/info", config.BASE_URL)
            response = all_info(response)
            return jsonify(response)

        elif endpoint in config.ENTRY_LISTINGS:
            # /<entry_listing>/info
            response = common_response("/" + endpoint + "/info", config.BASE_URL)
            response = entry_listing_infos[endpoint](response)
            return jsonify(response)

        else:
            # Not valid path
            msg="Bad request. Endpoint '{}' not recognized.".format(endpoint)
            response = dict(errors=[json_error(status=400, title="InputError", detail=msg, pointer=path)])
            return response, response["errors"][0]["status"]


class All(Resource):
    def get(self):
        # Get possible queries
        queries = request.args
        base_url = request.url_root + config.PREFIX[1:]

        # BASE response
        response = common_response(request.full_path, base_url)

        return jsonify(response)


class Structure(Resource):
    def get(self):
        # Get possible queries
        queries = request.args
        base_url = request.url_root + config.PREFIX[1:]

        # BASE response
        response = common_response(request.full_path, base_url)

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
