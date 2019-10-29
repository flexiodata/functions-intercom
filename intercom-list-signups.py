
# ---
# name: intercom-list-signups
# deployed: true
# title: Intercom List Signups
# description: Returns a list of the most recently created user profiles
# params:
#   - name: days
#     type: number
#     description: Number of days to search for most recently created profiles
#     required: true
#   - name: properties
#     type: array
#     description: |
#       The properties to return (defaults to 'email'). The following properties are allowed:
#         * name (The full name of the user)
#         * email (The email of the user)
#         * phone (The phone number of the user)
#         * sessions ()
#         * last seen ()
#         * first seen ()
#         * signed up ()
#         * city and country ()
#         * last contacted ()
#         * last heard from ()
#         * last opened email ()
#         * twitter followers ()
#         * unsubscribed ()
#         * browser language ()
#     default_value: '"email"'
#     required: false
# examples:
# - '10'
# notes:
# ---

import json
import requests
import urllib
import itertools
from datetime import *
from decimal import *
from cerberus import Validator
from collections import OrderedDict

# main function entry point
def flexio_handler(flex):

    # get the api key from the variable input
    auth_token = dict(flex.vars).get('intercom_connection')
    if auth_token is None:
        flex.output.content_type = "application/json"
        flex.output.write([[""]])
        return

    # get the input
    input = flex.input.read()
    try:
        input = json.loads(input)
        if not isinstance(input, list): raise ValueError
    except ValueError:
        raise ValueError

    # define the expected parameters and map the values to the parameter names
    # based on the positions of the keys/values
    params = OrderedDict()
    params['days'] = {'required': True, 'type': 'number', 'coerce': int}
    params['properties'] = {'required': False, 'validator': validator_list, 'coerce': to_list, 'default': 'email'}
    input = dict(zip(params.keys(), input))

    # validate the mapped input against the validator
    # if the input is valid return an error
    v = Validator(params, allow_unknown = True)
    input = v.validated(input)
    if input is None:
        raise ValueError

    try:

        # make the request
        # see here for more info: https://developers.intercom.com/intercom-api-reference/reference#list-users
        url_query_params = {"per_page": 50, "page": 1, "created_since": input["days"]}
        url_query_str = urllib.parse.urlencode(url_query_params)

        url = 'https://api.intercom.io/users?' + url_query_str
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + auth_token
        }
        response = requests.get(url, headers=headers)
        content = response.json()

        # get the properties to return and the property map
        properties = [p.lower().strip() for p in input['properties']]
        property_map = {
            'user_id': lambda item: item.get('user_id',''),
            'email': lambda item: item.get('email',''),
            'phone': lambda item: item.get('phone',''),
            'name': lambda item: item.get('name',''),
            'location_postal': lambda item: item.get('location_data',{}).get('postal_code',''),
            'location_city': lambda item: item.get('location_data',{}).get('city_name',''),
            'location_region': lambda item: item.get('location_data',{}).get('region_name',''),
            'location_country': lambda item: item.get('location_data',{}).get('country_name',''),
            'created_at': lambda item: item.get('created_at',''),
            'signed_up_at': lambda item: item.get('signed_up_at',''),
            'referrer': lambda item: item.get('referrer','')
        }

        # build up the result
        result = []

        result.append(properties)
        users = content.get('users',[])
        for item in users:
            row = [property_map.get(p, lambda item: '')(item) for p in properties]
            result.append(row)

        result = json.dumps(result, default=to_string)
        flex.output.content_type = "application/json"
        flex.output.write(result)

    except:
        raise RuntimeError

def validator_list(field, value, error):
    if isinstance(value, str):
        return
    if isinstance(value, list):
        for item in value:
            if not isinstance(item, str):
                error(field, 'Must be a list with only string values')
        return
    error(field, 'Must be a string or a list of strings')

def to_string(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (Decimal)):
        return str(value)
    return value

def to_list(value):
    # if we have a list of strings, create a list from them; if we have
    # a list of lists, flatten it into a single list of strings
    if isinstance(value, str):
        return value.split(",")
    if isinstance(value, list):
        return list(itertools.chain.from_iterable(value))
    return None

