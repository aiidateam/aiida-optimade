# -*- coding: utf-8 -*-

from flask import Flask
from flask_restful import Api
from resources import *
import common.config as config

"""
Flask app - OPTiMaDe
"""


class OptimadeApi(Api):

    def __init__(self, app=None, **kwargs):

        self.app = app

        super(OptimadeApi, self).__init__(app=app, prefix=kwargs['PREFIX'], catch_all_404s=False)

        # self.add_resource(
        #     ApiVersion,
        #     '/v<string:api_version>/',
        #     strict_slashes=False,
        #     endpoint='api_version'
        # )

        self.add_resource(
            Info,
            '/',
            '/info/',
            endpoint='info',
            strict_slashes=False,           # Does not force the last '/' on URLs
            resource_class_kwargs=kwargs
        )

        self.add_resource(
            All,
            '/all/',
            '/all/info/',
            '/all/page/',
            '/all/page/<int:page>/',
            endpoint='all',
            strict_slashes=False,
            resource_class_kwargs=kwargs
        )

        """ Resources and endpoints specific to AiiDA """
        self.add_resource(
            Structure,
            '/structures/',
            '/structures/info/',
            '/structures/page/',
            '/structures/page/<int:page>/',
            endpoint='structures',
            strict_slashes=False,
            resource_class_kwargs=kwargs
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
    app = Flask(__name__)

    api_kwargs = dict(PREFIX=config.PREFIX, RESPONSE_LIMIT_DEFAULT=config.RESPONSE_LIMIT_DEFAULT,
                      DB_MAX_LIMIT=config.DB_MAX_LIMIT)

    api = OptimadeApi(app, **api_kwargs)
    api.app.run(debug=True)
