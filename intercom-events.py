
# ---
# name: intercom-events
# deployed: true
# title: Intercom Events
# description: Returns events for a given user email
# params:
#   - name: email
#     type: string
#     description: User email address used in Intercom
#     required: true
#   - name: properties
#     type: array
#     description: The properties to return (defaults to all properties). See "Returns" for a listing of the available properties.
#     required: false
# returns:
#   - name: user_id
#     type: string
#     description: The user id of the user associated with the event
#   - name: email
#     type: string
#     description: The email of the user associated with the event
#   - name: event_name
#     type: string
#     description: The name of the event that occurred
#   - name: created_at
#     type: string
#     description: The time the event occurred
# examples:
#   - '"bbaggins@shire.com"'
#   - '"bbaggins@shire.com", "event_name, created_at"'
#   - '$A2, B$1:C$1'
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
    params['email'] = {'required': True, 'type': 'string', 'coerce': str}
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
    property_map['event_name'] = lambda item: item.get('event_name','')
    property_map['created_at'] = lambda item: item.get('created_at','')

    try:

        # make the request
        # see here for more info: https://developers.intercom.com/intercom-api-reference/reference#list-user-events
        url_query_params = {"type": "user", "email": input["email"]}
        url_query_str = urllib.parse.urlencode(url_query_params)

        url = 'https://api.intercom.io/events?' + url_query_str
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
        events = content.get('events',[])
        for item in events:
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
