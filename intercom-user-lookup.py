
# ---
# name: intercom-user-lookup
# deployed: true
# title: Intercom User Lookup
# description: Looks up information about a user from Intercom
# params:
# - name: email
#   type: string
#   description: Email of the user for which to get information
#   required: true
# examples:
# - '"helen.c.spencer@dodgit.com"'
# notes:
# ---

import json
import requests
from cerberus import Validator
from collections import OrderedDict

# main function entry point
def flexio_handler(flex):

    # get the api key from the variable input
    auth_token = dict(flex.vars).get('intercom_api_key')
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
    input = dict(zip(params.keys(), input))

    # validate the mapped input against the validator
    # if the input is valid return an error
    v = Validator(params, allow_unknown = True)
    input = v.validated(input)
    if input is None:
        raise ValueError

    try:

        # see here for more info: https://developers.intercom.com/intercom-api-reference/reference
        url = 'https://api.intercom.io/users?email=' + input.get('email','')
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + auth_token
        }

        response = requests.get(url, headers=headers)
        content = response.json()

        user_list = content.get('users',[])
        if len(user_list) == 0:
            flex.output.content_type = "application/json"
            flex.output.write([['']])

        # return the info for the first user
        result = user_list[0].get('name','')
        flex.output.content_type = "application/json"
        flex.output.write([[result]])

    except:
        raise RuntimeError

