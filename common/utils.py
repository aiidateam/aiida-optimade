# -*- coding: utf-8 -*-

import re
import common.config as config
from datetime import datetime

""" 
Utils

Utility functions

TODO: Should be updated so that it only contains utility functions
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

    # endpoint_list = endpoint.split('/')
    # if re.match(r'v(\d.){0,2}\d[a]?', endpoint_list[1]):
    #     api_version = endpoint_list[1]
    #     endpoint_list.remove(api_version)
    #     endpoint = '/'.join(endpoint_list)
    # else:
    #     api_version = config.API_VERSION_LATEST

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
            formats=config.RESPONSE_FORMATS,
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
            id=dict(
                description="A structure entry's ID"
            ),
            modification_date=dict(
                description="A date representing when the structure entry was last modified"
            ),
            elements=dict(
                description="Names of elements found in a structure"
            ),
            nelements=dict(
                description="Number of elements found in a structure"
            ),
            chemical_formula=dict(
                description="The chemical formula for a structure"
            ),
            formula_prototype=dict(
                description="The formula prototype obtained by sorting elements by the occurrence number in the "
                            "reduced chemical formular and replace them with subsequent alphabet letters A, B, "
                            "C and so on"
            ),
            dimension_types=dict(
                description="A list of three integers. For each of the three directions indicated by the three "
                            "lattice vectors this list indicates if that direction is periodic (value 1) or "
                            "non-periodic (value 0)"
            ),
            lattice_vectors=dict(
                description="The three lattice vectors in Cartesian coordinates",
                unit="Angstrom"
            ),
            cartesian_site_positions=dict(
                description="Cartesian positions of each site. A site is an atom, a site potentially occupied by an "
                            "atom, or a placeholder for a virtual mixture of atoms (e.g. in a virtual crystal "
                            "approximation"
            ),
            species_at_sites=dict(
                description="Name of the species at each site (where values for sites are specified with the same "
                            "order of the cartesian_site_positions properly)"
            ),
            species=dict(
                description="A dictionary describing the species of the sites of this structure. Species can be pure "
                            "chemical elements or virtual-crystal atoms representing a statistical occupation of a "
                            "given site by multiple chemical elements. Keys: 'chemical_symbols', 'concentration', "
                            "'mass', 'original_name'"
            ),
            assemblies=dict(
                description="A description of groups of sites that are statistically correlated. A list of "
                            "dictionaries with keys: 'sites_in_group', 'group_probabilities'"
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
            id=dict(
                description="An calculation entry's ID"
            ),
            modification_date=dict(
                description="A date representing when the calculation entry was last modified"
            ),
            _aiida_code=dict(
                description="The code used by the calculation"
            )
        ),
        formats=["json"],
        output_fields_by_format=dict()
    )

    data['output_fields_by_format'] = dict(json=[p for p in data['properties']])

    response["data"].append(data)

    return response


def valid_version(api_version):
    """
    :param api_version: string of single api_version, ex.: "v0.9.5" or "1.1" or "v2" or "0.9.5"

    :return: boolean
    """

    if re.match(r'v(\d.){0,2}\d[a]?', api_version):  # Does not check if MINOR ver is present when MAJOR ver = 0
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
    :return: integer: response limit of data to be returned
        or   dict: JSON Error Object
    """

    try:
        limit = int(limit)
    except ValueError:
        msg = "response_limit must be an integer"
        return json_error(detail=msg, parameter="response_limit")

    # Check that limit is not larger than allowed by DB
    if limit <= config.DB_MAX_LIMIT:
        return limit
    else:
        msg = "Request not allowed by database. Max response_limit = {}".format(config.DB_MAX_LIMIT)
        return json_error(status=403, detail=msg, parameter="response_limit")


def query_response_format(format_):
    """
    Default response format: JSON (see config for actual default)

    :param format_: string, new queried response_format
             if format=default, response_format will be reset to default
    :return: string: response format to be returned
        or   dict: JSON Error Object
    """

    if format_ == "default":
        return config.RESPONSE_FORMAT
    elif format_ in config.RESPONSE_FORMATS:
        return format_
    else:
        # Not (yet) allowed format
        msg = "Requested format '{}' is not allowed or not yet implemented." \
              "Implemented formats: ".format(format_)
        for f in config.RESPONSE_FORMATS:
            msg += "'{}',".format(f)
        msg = msg[:-1]

        return json_error(status=418, detail=msg, parameter="response_format")


def query_email_address(email):
    """
    :param email: string, new specified user e-mail-address
    :return: string: e-mail-address for user querying DB
        or   dict: JSON Error Object
    """

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        # Not proper e-mail-format
        msg = "E-mail-address format not correct. Example: user@example.com"
        return json_error(status=400, detail=msg, parameter="email_address")
    else:
        return email


def query_response_fields(fields):
    """
    :param fields: comma-separated string, queried response_fields
             if fields=default, response_fields will be reset to default
    :return: list of strings: requested response fields to be returned in data
        or   dict: JSON Error Object
    """

    valid_response_fields = ['type', 'id', 'attributes', 'local_id', 'last_modified',
                             'immutable_id', 'links', 'meta', 'relationships']

    fields = fields.split(',')

    false_fields = list()
    true_fields = list()

    for field in fields:
        if field not in valid_response_fields:
            # Requested field not part of valid fields
            false_fields.append(field)
        else:
            # Requested field is OK
            true_fields.append(field)

    if len(false_fields) > 1:
        msg = "Requested fields are not valid: "
        for field in false_fields:
            msg += "'{}',".format(field)
            msg = msg[:-1]
        error = json_error(status=418, detail=msg, parameter="response_fields")
        true_fields.append(error)
    elif len(false_fields) == 1:
        msg = "Requested field '{}' is not valid".format(field)
        error = json_error(status=418, detail=msg, parameter="response_fields")
        true_fields.append(error)

    return true_fields


def get_structure_properties(attr_sites, attr_kinds):
    """
    Translate AiiDA query results to OPTiMaDe JSON Object entries

    :param attr_sites: list of sites from query of StructureData in AiiDA DB under "attributes"
    :param attr_kinds: list of element kinds from query of StructureData in AiiDA DB under "attributes"
    :return: dict that will be updated in attributes-dict
    """

    # Type check(s)
    if not isinstance(attr_sites, list):
        raise TypeError
    if not isinstance(attr_kinds, list):
        raise TypeError

    # Initiate
    sites = dict()
    site_positions = list()
    site_species = list()
    chemical_content = dict()
    elements = list()
    chemical_formula = ""
    species = dict()

    # Retrieve sites
    for site in attr_sites:
        kind_name = site["kind_name"]
        position = site["position"]

        # Count number of sites for 'kind'
        if kind_name in sites:
            sites[kind_name] += 1
        else:
            sites[kind_name] = 1

        site_positions.append(position)
        site_species.append(kind_name)

    # Retrieve 'kinds'
    for kind in attr_kinds:
        kind_name = kind["name"]
        kind_sites = sites[kind_name]
        kind_weight_sum = 0

        # Retrieve elements in 'kind'
        for i in range(len(kind["symbols"])):
            element = kind["symbols"][i]
            weight = kind["weights"][i]

            # Accumulating sum of weights
            kind_weight_sum += weight

            # Calculate content of element
            if element in chemical_content:
                chemical_content[element] += weight * kind_sites
            else:
                chemical_content[element] = weight * kind_sites

            # Determine unique elements
            if element not in elements:
                elements.append(element)

        # Create 'species' entry
        species[kind_name] = dict(
            chemical_symbols=kind["symbols"],
            concentration=kind["weights"],
            mass=kind["mass"],
            original_name=kind_name
        )

        if re.match(r'[\w]*X[\d]*', kind_name):
            # Species includes vacancy
            species[kind_name]["chemical_symbols"].append("vacancy")

            # Calculate vacancy concentration
            if 0. < kind_weight_sum < 1.:
                species[kind_name]["concentration"].append(1.-kind_weight_sum)
            else:
                raise ValueError

    # Parse chem_form dict to a string with format example "Si24Al2O72Cu1.03"
    # TODO: Calculate the REDUCED chemical formula to return
    for element, nelement in chemical_content.items():
        # nelement = int(nelement * 10) / 10
        if nelement == 1.:
            chemical_formula += "{}".format(element)
        else:
            chemical_formula += "{}{:n}".format(element, nelement)

    # Collect data in dict-to-be-returned
    data = dict(
        elements=','.join([element for element in chemical_content]),
        nelements=len(chemical_content),
        chemical_formula=chemical_formula,
        cartesian_site_positions=site_positions,
        species_at_sites=site_species,
        species=species
    )

    return data


def get_dt_format(dt):
    """
    Reformat AiiDA query datetime object to OPTiMaDe datetime format standard

    Since AiiDA datetime objects are produced using psycopg2, they should all include a tzinfo object as well,
    and thus be 'aware' datetime objects.
    So dt.utcoffset() should never be None for a true AiiDA query datetime object.

    :param dt: AiiDA query datetime as datetime.datetime
    :return: Reformatted OPTiMaDe datetime as datetime.datetime
    """

    # Type check
    if not isinstance(dt, datetime):
        raise TypeError

    if dt.utcoffset() is None:
        raise TypeError
    else:
        dt = dt - dt.utcoffset()

    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')


def handle_queries(queries):
    """
    :param queries: dict: Query keyword and values
    :return: Valid query values
    """

    # Initialize
    filter_ = queries['filter'] if 'filter' in queries else None
    format_ = queries['response_format'] if 'response_format' in queries else None
    email   = queries['email_address'] if 'email_address' in queries else None
    limit   = queries['response_limit'] if 'response_limit' in queries else None
    fields  = queries['response_fields'] if 'response_fields' in queries else None

    # Get query values
    # TODO: Add 'filter'
    if format_:
        format_ = QUERY_PARAMETERS['response_format'](format_)
    if email:
        email = QUERY_PARAMETERS['email_address'](email)
    if limit:
        limit = QUERY_PARAMETERS['response_limit'](limit)
    if fields:
        fields = QUERY_PARAMETERS['response_fields'](fields)

    return (filter_, format_, email, limit, fields)


# Function mapping for queries
QUERY_PARAMETERS = {
    'filter': None,
    'response_format': query_response_format,
    'email_address': query_email_address,
    'response_limit': query_response_limit,
    'response_fields': query_response_fields
}

# Function mapping for <entry_listing>/info/
ENTRY_LISTING_INFOS = {
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


def paginate(self, page, perpage, total_count):
        """
        Calculates limit and offset for the reults of a query,
        given the page and the number of restuls per page.
        Moreover, calculates the last available page and raises an exception
        if the required page exceeds that limit.
        If number of rows==0, only page 1 exists
        :param page: integer number of the page that has to be viewed
        :param perpage: integer defining how many results a page contains
        :param total_count: the total number of rows retrieved by the query
        :return: integers: limit, offset, rel_pages
        """
        from math import ceil

        """ Type checks """
        # Mandatory params
        try:
            page = int(page)
        except ValueError:
            raise ValueError("page number must be an integer")
        try:
            total_count = int(total_count)
        except ValueError:
            raise ValueError("total_count must be an integer")
        # Non-mandatory params
        if perpage is not None:
            try:
                perpage = int(perpage)
            except ValueError:
                raise ValueError("perpage must be an integer")
        else:
            perpage = self.perpage_default

        # First_page is anyway 1
        first_page = 1

        # Calculate last page
        if total_count == 0:
            last_page = 1
        else:
            last_page = int(ceil(total_count / perpage))

        # Check validity of required page and calculate limit, offset, previous, and next page
        if page > last_page or page < 1:
            raise ValueError("Non existent page requested."
                             "The page range is [{} : {}]".format(first_page, last_page))

        limit = perpage
        offset = (page - 1) * perpage
        prev_page = None
        if page > 1:
            prev_page = page - 1

        next_page = None
        if page < last_page:
            next_page = page + 1

        rel_pages = dict(prev=prev_page, next=next_page, first=first_page, last=last_page)

        return (limit, offset, rel_pages)
