# -*- coding: utf-8 -*-

# Default / config
API_VERSIONS = ["v0.9.5", "v0.9.7a"]  # alpha-versions are equivalent to the develop branch on GitHub
API_VERSION_LATEST = sorted(API_VERSIONS)[-1]
PREFIX = "/optimade"
BASE_URL = "http://127.0.0.1:5000" + PREFIX

RESPONSE_LIMIT = 10
RESPONSE_FORMAT = 'json'

RESPONSE_LIMIT = RESPONSE_LIMIT_DEFAULT
DB_MAX_LIMIT = 1000
DB_PREFIX = "_aiida_"

# FORMATS = ['json', 'xml']
RESPONSE_FORMATS = ['json', 'jsonapi']

USER_EMAIL_ADDRESS = 'anonymous@optimade.com'

# Endpoints
ENTRY_LISTINGS = ['structures', 'calculations']
