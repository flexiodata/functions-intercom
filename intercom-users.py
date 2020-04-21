
# ---
# name: intercom-signups
# deployed: true
# title: IntercomSignups
# description: Returns a list of the most recently created user profiles
# params:
#   - name: days
#     type: number
#     description: Number of days to search for most recently created profiles
#     required: true
#   - name: properties
#     type: array
#     description: The properties to return (defaults to all properties). See "Returns" for a listing of the available properties.
#     required: false
# returns:
#   - name: user_id
#     type: string
#     description: The user id for the user
#   - name: email
#     type: string
#     description: The email for the user
#   - name: phone
#     type: string
#     description: The phone number for the user
#   - name: name
#     type: string
#     description: The full name for the user
#   - name: pseudonym
#     type: string
#     description: The pseudonym used if the user was previously list as an Intercom lead
#   - name: referrer
#     type: string
#     description: The url of the page the user was last on
#   - name: created_at
#     type: string
#     description: The time the user was added to Intercom
#   - name: signed_up_at
#     type: string
#     description: The time the user signed up
#   - name: updated_at
#     type: string
#     description: The time the user was last updated
#   - name: last_request_at
#     type: string
#     description: The time the user was last recorded as making a request
#   - name: session_count
#     type: string
#     description: The number of sessions the user is recorded as having made
#   - name: location_postal
#     type: string
#     description: The postal code for the user location
#   - name: location_city
#     type: string
#     description: The city for the user location
#   - name: location_region
#     type: string
#     description: The region for the user location
#   - name: location_country
#     type: string
#     description: The country for the user location
#   - name: location_country_code
#     type: string
#     description: The country code for the user location
#   - name: location_continent_code
#     type: string
#     description: The continent code for the user location
#   - name: location_timezone
#     type: string
#     description: The timezone for the user location
# examples:
#   - '10'
#   - '20, "user_id, email, name"'
#   - '20, B$1:D$1'
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
    auth_token = dict(flex.vars).get('intercom_connection',{}).get('access_token')
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
    params['properties'] = {'required': False, 'validator': validator_list, 'coerce': to_list, 'default': '*'}
    input = dict(zip(params.keys(), input))

    # validate the mapped input against the validator
    # if the input is valid return an error
    v = Validator(params, allow_unknown = True)
    input = v.validated(input)
    if input is None:
        raise ValueError

    # map this function's property names to the API's property names
    property_map = OrderedDict()
    property_map['user_id'] = lambda item: item.get('user_id','')
    property_map['email'] = lambda item: item.get('email','')
    property_map['phone'] = lambda item: item.get('phone','')
    property_map['name'] = lambda item: item.get('name','')
    property_map['pseudonym'] = lambda item: item.get('pseudonym','')
    property_map['referrer'] = lambda item: item.get('referrer','')
    property_map['created_at'] = lambda item: item.get('created_at','')
    property_map['signed_up_at'] = lambda item: item.get('signed_up_at','')
    property_map['updated_at'] = lambda item: item.get('updated_at','')
    property_map['last_request_at'] = lambda item: item.get('last_request_at','')
    property_map['session_count'] = lambda item: item.get('session_count','')
    property_map['location_postal'] = lambda item: item.get('location_data',{}).get('postal_code','')
    property_map['location_city'] = lambda item: item.get('location_data',{}).get('city_name','')
    property_map['location_region'] = lambda item: item.get('location_data',{}).get('region_name','')
    property_map['location_country'] = lambda item: item.get('location_data',{}).get('country_name','')
    property_map['location_country_code'] = lambda item: item.get('location_data',{}).get('country_code','')
    property_map['location_continent_code'] = lambda item: item.get('location_data',{}).get('continent_code','')
    property_map['location_timezone'] = lambda item: item.get('location_data',{}).get('timezone','')

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

        # if we have a wildcard, get all the properties
        if len(properties) == 1 and properties[0] == '*':
            properties = list(property_map.keys())

        # build up the result
        result = []

        result.append(properties)
        users = content.get('users',[])
        for item in users:
            row = [property_map.get(p, lambda item: '')(item) or '' for p in properties]
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

