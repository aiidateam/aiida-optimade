# -*- coding: utf-8 -*-

from flask import Flask
from flask_restful import Api
from resources import *
import config

"""
Flask app - OPTiMaDe
"""

app = Flask(__name__)
# app.config['APPLICATION_ROOT'] = '/optimade/'
api = Api(app, prefix=config.PREFIX)

api.add_resource(
    Optimade,
    '/',
    endpoint='optimade'
)

api.add_resource(
    ApiVersion,
    '/v<string:api_version>/',
    endpoint='api_version'
)

api.add_resource(
    Info,
    '/info',
    endpoint='info'
)

api.add_resource(
    All,
    '/all/',
    endpoint='all'
)

api.add_resource(
    Structure,
    '/structures',
    '/structures/info',
    endpoint='structures'
)


# def handle_error(self, e):
#     """
#     this method handles the 404 "URL not found" exception and return custom message
#     :param e: raised exception
#     :return: list of available endpoints
#     """
#
#     if isinstance(e, HTTPException):
#         if e.code == 404:
#             from utils import list_routes
#
#             response = dict()
#
#             response["status"] = "404 Not Found"
#             response["message"] = "The requested URL is not found on the server."
#
#             response["available_endpoints"] = list_routes()
#
#             return jsonify(response)
#
#     raise e


if __name__ == '__main__':
    app.run(debug=True)
