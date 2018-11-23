# -*- coding: utf-8 -*-

# Default / config
# API_VERSIONS = ["v0.9.5", "v1", "v0.9.6a", "v0.9.6", "v0.9.7a", "v0.9.7"]
API_VERSIONS = ["v0.9.5", "v0.9.7a"]  # alpha-versions are equivalent to the develop branch on GitHub
API_VERSION_LATEST = sorted(API_VERSIONS)[-1]
PREFIX = "/optimade"
BASE_URL = "http://127.0.0.1:5000" + PREFIX

RESPONSE_LIMIT_DEFAULT = 10
RESPONSE_FORMAT_DEFAULT = 'json'
RESPONSE_FIELDS_DEFAULT = ['type', 'id', 'attributes', 'links', 'meta', 'relationships']

RESPONSE_LIMIT = RESPONSE_LIMIT_DEFAULT
DB_MAX_LIMIT = 1000

# FORMATS = ['json', 'xml']
FORMATS = ['json']
RESPONSE_FORMAT = RESPONSE_FORMAT_DEFAULT

USER_EMAIL_ADDRESS = 'anonymous@optimade.com'

RESPONSE_FIELDS = RESPONSE_FIELDS_DEFAULT

# Endpoints
ENTRY_LISTINGS = ['computers', 'nodes', 'calculations', 'data', 'codes',
                  'structures', 'kpoints', 'bands', 'upfs', 'cifs', 'users', 'groups']
# ENTRY_LISTINGS = [ 'structures' ]
