# -*- coding: utf-8 -*-

from flask import Flask
from flask_restful import Api
from resources import Info, All, Structure, Calculation
import common.config as config


class OptimadeApi(Api):
    """
    Flask-RESTful API - OPTiMaDe
    """

    def __init__(self, app=None, **kwargs):

        self.app = app

        super(OptimadeApi, self).__init__(app=app, prefix=kwargs['PREFIX'], catch_all_404s=False)

        self.add_resource(
            Info,
            '/info/',
            endpoint='info',
            strict_slashes=False,           # Does not force the last '/' on URLs
            resource_class_kwargs=kwargs
        )

        self.add_resource(
            All,
            '/all/',
            '/all/<int:id>/',
            '/all/info/',
            '/all/page/',
            '/all/page/<int:page>/',
            endpoint='all',
            strict_slashes=False,
            resource_class_kwargs=kwargs
        )

        # """ Resources and endpoints specific to AiiDA """
        self.add_resource(
            Structure,
            '/structures/',
            '/structures/<int:id>/',
            '/structures/info/',
            '/structures/page/',
            '/structures/page/<int:page>/',
            endpoint='structures',
            strict_slashes=False,
            resource_class_kwargs=kwargs
        )

        self.add_resource(
            Calculation,
            '/calculations/',
            '/calculations/<int:id>/',
            '/calculations/info/',
            '/calculations/page/',
            '/calculations/page/<int:page>/',
            endpoint='calculations',
            strict_slashes=False,
            resource_class_kwargs=kwargs
        )

    # """ From AiiDA REST-API """
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

    # TODO: Implement way of handling versioning.

    opt_app = Flask(__name__)

    api_kwargs = dict(PREFIX=config.PREFIX, RESPONSE_LIMIT=config.RESPONSE_LIMIT,
                      DB_MAX_LIMIT=config.DB_MAX_LIMIT, DB_PREFIX=config.DB_PREFIX)

    api = OptimadeApi(opt_app, **api_kwargs)

    # Add redirect rules for base_url to /optimade/info/
    api.app.add_url_rule('/', endpoint='optimade', redirect_to='/optimade/')
    api.app.add_url_rule('/optimade/', endpoint='optimade', redirect_to='/optimade/info/')

    # Add rule for latest version to be used as default
    api.app.add_url_rule('/optimade/' + config.API_VERSION_LATEST + '/', endpoint='optimade', \
        redirect_to='/optimade/')

    api.app.run(debug=True)
