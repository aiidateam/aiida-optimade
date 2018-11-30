# -*- coding: utf-8 -*-

# from optimade.filter import Parser
# from transformers import TreeToPy
import common.config as config
from common.utils import common_response, baseurl_info, entry_listing_infos, all_info, query_parameters, json_error,\
    get_structure_properties, get_dt_format
from flask import request, jsonify
from flask_restful import Resource

from aiida.backends.utils import is_dbenv_loaded, load_dbenv
if not is_dbenv_loaded():
    load_dbenv()

from aiida.orm.querybuilder import QueryBuilder


class Info(Resource):
    def __init__(self, **kwargs):
        self.prefix = kwargs["PREFIX"]
        # self.response_limit_default = kwargs["RESPONSE_LIMIT_DEFAULT"]
        # self.db_max_limit = kwargs["DB_MAX_LIMIT"]

    def get(self, endpoint='info'):
        # Decode url-path
        path = request.path
        # endpoint = path.split('/')[2]  # Get 'endpoint' from: /optimade/<endpoint>
        base_url = request.url_root + self.prefix[1:]
        full_path = request.full_path.split('/')
        full_path = '/'.join([''] + full_path[2:])

        if endpoint == 'info':
            # /info or /
            response = common_response(full_path, base_url)
            response = baseurl_info(response)
            return jsonify(response)

        elif endpoint == 'all':
            # /all/info
            response = common_response(full_path, base_url)
            response = all_info(response)
            return jsonify(response)

        elif endpoint in config.ENTRY_LISTINGS:
            # /<entry_listing>/info
            response = common_response(full_path, base_url)
            response = entry_listing_infos[endpoint](response)
            return jsonify(response)

        else:
            # Not valid path
            msg = "Bad request. Endpoint '{}' not recognized.".format(endpoint)
            response = dict(errors=[json_error(status=400, title="InputError", detail=msg, pointer=path)])
            return response, response["errors"][0]["status"]


class All(Resource):
    def __init__(self, **kwargs):
        self.prefix = kwargs["PREFIX"]
        self.response_limit_default = kwargs["RESPONSE_LIMIT_DEFAULT"]
        self.db_max_limit = kwargs["DB_MAX_LIMIT"]

    def get(self, id=None, page=None):
        # Get possible queries
        # queries = request.args
        base_url = request.url_root + self.prefix[1:]
        path_elems = request.path.split('/')
        full_path = request.full_path.split('/')
        full_path = '/'.join([''] + full_path[2:])

        if 'info' in path_elems[-2:]:
            return Info(PREFIX=self.prefix).get(endpoint='all')

        # BASE response
        response = common_response(full_path, base_url)

        return jsonify(response)


class Structure(Resource):
    def __init__(self, **kwargs):
        self.prefix = kwargs["PREFIX"]
        self.response_limit_default = kwargs["RESPONSE_LIMIT_DEFAULT"]
        self.db_max_limit = kwargs["DB_MAX_LIMIT"]
        self.db_prefix = kwargs["DB_PREFIX"]

        self._label = "structures"
        self._type = "structure"

        # basic query_help object (from aiida-restapi)
        self._query_help = {
            "path": [{
                "type": "data.structure.StructureData.",
                "label": self._label
            }],
            "filters": {},
            "project": {self._label: [  # ['**']},
                "id", "label", "ctime", "mtime", "uuid", "user_id", "user_email", "attributes", "extras"
            ]},
            "order_by": {}
        }

        self.qbobj = QueryBuilder()

    def get(self, id=None, page=None):
        # Get possible queries
        queries = request.args  # Immutabable dict of (k,v) queries
        base_url = request.url_root + self.prefix[1:]
        # api_version = request.base_url.split('/')[-2]
        path_elems = request.path.split('/')
        full_path = request.full_path.split('/')
        full_path = '/'.join([''] + full_path[2:])

        # Info-endpoint
        if 'info' in path_elems[2:]:
            return Info(PREFIX=self.prefix).get(endpoint=self._label)

        # Common response
        response = common_response(full_path, base_url)

        # Handle possible present queries
        for query in queries:
            # Get value of query
            query_value = queries[query]

            if query in query_parameters:
                # Valid query key

                if query != "filter":  # Filter query is treated separately below
                    status = query_parameters[query](query_value)

                    # Error
                    if isinstance(status, dict) and status["status"]:
                        status["source"]["pointer"] = "/{}/".format(self._label)
                        if "errors" in response:
                            response["errors"].append(status)
                        else:
                            response["errors"] = [status]
                    # Success
                    elif isinstance(status, str) and status == "200":
                        pass
                # ?filter=
                elif query == "filter":
                    pass
                    # TODO: Finish writing filter. Should contain filters for:
                    #       Date-time queries.
                    #       elements
                    #       nelements

                else:
                    msg = "Unknown error during query evaluation. Query: " + \
                          query + "=" + query_value
                    error = json_error(status=404, detail=msg, pointer="/{}/".format(self._label), parameter=query)
                    if "errors" in response:
                        response["errors"].append(error)
                    else:
                        response["errors"] = [error]

                continue

            else:
                msg = "Invalid query parameter: '" + query + "'. Legal query parameters: "
                for param in query_parameters: msg += "'" + param + "',"
                msg = msg[:-1]
                error = json_error(status=418, detail=msg, pointer="/{}/".format(self._label), parameter=query)
                if "errors" in response:
                    response["errors"].append(error)
                else:
                    response["errors"] = [error]

        # TODO: Use queries
        """ Retrieve and return structures """
        # Initialize QueryBuilder-object
        if id is not None:
            # Single-entry from id
            id_filter = {self._label: {'id': {'==': id}}}
            self._query_help["filters"].update(id_filter)

        self.qbobj.__init__(**self._query_help)

        # Count results and retrieve them
        total_count = self.qbobj.count()
        results = [res[self._label] for res in self.qbobj.dict()]

        # Check if any results are found
        if total_count == 0:
            pointer = '/' + '/'.join(path_elems[2:])
            if id is not None:
                msg = "Id: '{}' could not be found in the database".format(id)
            else:
                msg = "No {} were found in the database".format(self._label)
            error = json_error(status=404, title="ValueError", detail=msg, pointer=pointer)
            if "errors" in response:
                response["errors"].append(error)
            else:
                response["errors"] = [error]

        # Update meta in response
        if total_count is not None and total_count != 0:
            response["meta"]["data_returned"] = total_count
        else:
            response["meta"]["data_returned"] = 0

        for entry in results:
            # Update type and id for entry
            entry["type"] = self._type
            entry["id"] = str(entry["id"])

            # Add base property attributes
            add_attr = dict(
                local_id=entry["id"],
                last_modified=get_dt_format(entry.pop("mtime")),
                immutable_id=entry["uuid"],
            )

            # Add entry-specific property attributes
            attr = entry["attributes"]

            structure_attr = dict(
                dimension_types=[int(attr.pop("pbc" + str(i+1))) for i in range(3)],
                lattice_vectors=attr.pop("cell"),
            )

            # Update attributes
            attr.update(add_attr)
            attr.update(structure_attr)
            attr.update(get_structure_properties(attr.pop("sites"), attr.pop("kinds")))

            # Add entry-specific meta-info
            entry_meta = dict()

            entry_keys = [k for k in entry]
            for key in entry_keys:
                # Skip valid OPTiMaDe JSON values/dict keys
                if key in ["attributes", "id", "type"]:
                    continue

                # Extract nested JSON Objects/Python dicts from AiiDA query out into meta
                elif key in ["extras"]:
                    extra_prefix = "{}_".format(key)  # Additional prefix after db_prefix

                    entry_extra_keys = [k for k in entry[key]]
                    for extra_key in entry_extra_keys:
                        if extra_key.startswith(self.db_prefix):
                            new_key = extra_key[len(self.db_prefix):]
                            new_key = ''.join([self.db_prefix, extra_prefix, new_key])
                            entry_meta[new_key] = entry[key].pop(extra_key)
                        else:
                            new_key = ''.join([self.db_prefix, extra_prefix, extra_key])
                            entry_meta[new_key] = entry[key].pop(extra_key)

                    # Remove nested JSON Object/Python dict
                    if not entry[key]:
                        entry.pop(key)
                    else:
                        raise KeyError

                # Append database prefix to JSON values/dict keys
                else:
                    if key.startswith(self.db_prefix):
                        entry_meta[key] = entry.pop(key)
                    else:
                        entry_meta[self.db_prefix + key] = entry.pop(key)

            entry["meta"] = entry_meta

        # Update data in response
        response["data"] = results

        """ Check for errors in response """
        if "errors" in response:
            if len(response["errors"]) > 1:
                # Returning most generally applicable HTTP error according to JSON
                # API Error Objects description. Here: 4xx errors
                response = jsonify(response)
                response.status_code = 400
            else:
                status = int(response["errors"][0]["status"])
                response = jsonify(response)
                response.status_code = status
        else:
            response = jsonify(response)
            response.status_code = 200

        """ Return final response """
        return response


class Calculation(Resource):
    """
    NB!

    For now this resource ONLY serves as a snapshot of how the Structure resource used to be!

    """
    def __init__(self, **kwargs):
        self.prefix = kwargs["PREFIX"]
        self.response_limit_default = kwargs["RESPONSE_LIMIT_DEFAULT"]
        self.db_max_limit = kwargs["DB_MAX_LIMIT"]

    def get(self, id=None, page=None):
        # Get possible queries
        queries = request.args
        base_url = request.url_root + self.prefix[1:]
        # api_version = request.base_url.split('/')[-2]
        path_elems = request.path.split('/')
        full_path = request.full_path.split('/')
        full_path = '/'.join([''] + full_path[2:])

        # Info-endpoint
        if 'info' in path_elems[2:]:
            return Info(PREFIX=self.prefix).get(endpoint='calculations')

        # """ Check if special api_version is chosen / is present in url """
        # if api_version != self.prefix[1:] and re.match(r'v(\d.){0,2}\d[a]?', api_version):
        #     if valid_version(api_version):
        #         base_url += '/' + api_version
        #     else:
        #         # Error: Requested version is not a valid current or legacy version
        #         msg = "Bad request. Version '{}' is not a valid current or legacy version.".format(api_version)
        #         response = dict(errors=[json_error(status=400, title="InputError", detail=msg, pointer=request.path)])
        #         return response, response["errors"][0]["status"]
        # elif api_version != self.prefix[1:]:
        #     # Error: Requested version is not of a valid format
        #     msg = "Bad request. Version should be of the format 'v0.9.5' or left out."
        #     response = dict(errors=[json_error(status=400, title="InputError", detail=msg, pointer=request.path)])
        #     return response, response["errors"][0]["status"]

        # Common response
        response = common_response(full_path, base_url)

        for query in queries:
            # Get value of query
            query_value = queries[query]

            # # Add query-value-pair to "representation"-url meta-key
            # if response["meta"]["query"]["representation"][-1] == "?":
            #     representation = query + "=" + query_value
            # else:
            #     representation = "&" + query + "=" + query_value
            # response["meta"]["query"]["representation"] += representation

            if query in query_parameters:
                # Valid query key

                if query != "filter":  # Filter query is treated separately below
                    # Do the thing
                    status = query_parameters[query](query_value)

                    # Catch error(s)
                    if isinstance(status, dict) and status["status"]:
                        status["source"]["pointer"] = "/calculations/"
                        if "errors" in response:
                            response["errors"].append(status)
                        else:
                            response["errors"] = [status]
                    # Success
                    elif isinstance(status, str) and status == "200":
                        pass
                # ?filter=
                elif query == "filter":
                    pass
                else:
                    msg = "Unknown error during query evaluation. Query: " + \
                          query + "=" + query_value
                    error = json_error(status=404, detail=msg, pointer="/calculations/", parameter=query)
                    if "errors" in response:
                        response["errors"].append(error)
                    else:
                        response["errors"] = [error]

                continue

            else:
                msg = "Invalid query parameter: '" + query + "'. Legal query parameters: "
                for param in query_parameters: msg += "'" + param + "',"
                msg = msg[:-1]
                error = json_error(status=418, detail=msg, pointer="/calculations/", parameter=query)
                if "errors" in response:
                    response["errors"].append(error)
                else:
                    response["errors"] = [error]

        if "errors" in response:
            if len(response["errors"]) > 1:
                # Returning most generally applicable HTTP error according to JSON
                # API Error Objects description. Here: 4xx errors
                response = jsonify(response)
                response.status_code = 400
            else:
                status = int(response["errors"][0]["status"])
                response = jsonify(response)
                response.status_code = status
        else:
            response = jsonify(response)
            response.status_code = 200

        print(config.RESPONSE_FORMAT)

        return response
