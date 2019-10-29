
# ---
# name: intercom-enrich-users
# deployed: true
# title: Intercom Enrich Users
# description: Returns profile information of an intercom user based on email address
# params:
#   - name: email
#     type: string
#     description: User email address used in Intercom
#     required: true
#   - name: properties
#     type: array
#     description: |
#       The properties to return (defaults to 'name'). The following properties are allowed:
#         * user_id (The user id for the user)
#         * email (The email for the user)
#         * phone (The phone number for the user)
#         * name (The full name for the user)
#         * pseudonym (The pseudonym used if the user was previously list as an Intercom lead)
#         * referrer (The url of the page the user was last on)
#         * created_at (The time the user was added to Intercom)
#         * signed_up_at (The time the user signed up)
#         * updated_at (The time the user was last updated)
#         * last_request_at (The time the user was last recorded as making a request)
#         * session_count (The number of sessions the user is recorded as having made)
#         * location_postal (The postal code for the user location)
#         * location_city (The city for the user location)
#         * location_region (The region for the user location)
#         * location_country (The country for the user location)
#         * location_country_code (The country code for the user location)
#         * location_continent_code (The continent code for the user location)
#         * location_timezone (The timezone for the user location)
#     default_value: '"name"'
#     required: false
# examples:
#   - '"helen.c.spencer@dodgit.com"'
#   - '"helen.c.spencer@dodgit.com", "user_id, name, phone"'
#   - '$A2, C$1:E$1'
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
    params['email'] = {'required': True, 'type': 'string'}
    params['properties'] = {'required': False, 'validator': validator_list, 'coerce': to_list, 'default': 'name'}
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
        url_query_params = {"email": input["email"]}
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
            'pseudonym': lambda item: item.get('pseudonym',''),
            'referrer': lambda item: item.get('referrer',''),
            'created_at': lambda item: item.get('created_at',''),
            'signed_up_at': lambda item: item.get('signed_up_at',''),
            'updated_at': lambda item: item.get('updated_at',''),
            'last_request_at': lambda item: item.get('last_request_at',''),
            'session_count': lambda item: item.get('session_count',''),
            'location_postal': lambda item: item.get('location_data',{}).get('postal_code',''),
            'location_city': lambda item: item.get('location_data',{}).get('city_name',''),
            'location_region': lambda item: item.get('location_data',{}).get('region_name',''),
            'location_country': lambda item: item.get('location_data',{}).get('country_name',''),
            'location_country_code': lambda item: item.get('location_data',{}).get('country_code',''),
            'location_continent_code': lambda item: item.get('location_data',{}).get('continent_code',''),
            'location_timezone': lambda item: item.get('location_data',{}).get('timezone','')
        }

        # get the user info for the first matching user
        user_info = {}
        user_list = content.get('users',[])

        if len(user_list) > 0:
            user_info = user_list[0]
        result = [[property_map.get(p, lambda item: '')(user_info) for p in properties]]

        # return the results
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

