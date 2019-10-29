
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
#         * name ()
#         * email ()
#         * phone ()
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
#     default_value: '"name"'
#     required: false
# examples:
#   - '"helen.c.spencer@dodgit.com"'
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

        # get the user info for the first matching user
        user_info = {}
        user_list = content.get('users',[])

        if len(user_list) > 0:
            user_info = user_list[0]

        # limit the results to the requested properties
        properties = [p.lower().strip() for p in input['properties']]
        result = [[user_info.get(p,'') for p in properties]]

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

