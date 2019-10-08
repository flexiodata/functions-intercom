
# ---
# name: intercom-user-list
# deployed: true
# title: Intercom User List
# description: Lists all users created since a specified number of days ago
# params:
# - name: date
#   type: string
#   description: Number of days ago to use to determine users that should be returned
#   required: true
# examples:
# - '10'
# notes:
# ---

import json
import requests
from cerberus import Validator
from collections import OrderedDict

# main function entry point
def flexio_handler(flex):

    # get the api key from the variable input
    auth_info = flex.connections['intercom'].get_credentials()
    auth_token = auth_info.get('access_token','')
    # auth_token = dict(flex.vars).get('intercom_connection')
    # if auth_token is None:
    #     flex.output.content_type = "application/json"
    #     flex.output.write([[""]])
    #     return

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
    input = dict(zip(params.keys(), input))

    # validate the mapped input against the validator
    # if the input is valid return an error
    v = Validator(params, allow_unknown = True)
    input = v.validated(input)
    if input is None:
        raise ValueError

    try:

        # see here for more info: https://developers.intercom.com/intercom-api-reference/reference
        url = 'https://api.intercom.io/users?per_page=50&page=1&created_since='+str(input['days'])
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + auth_token
        }

        response = requests.get(url, headers=headers)
        content = response.json()

        # return the info
        columns = [
            {'name':'user_id', 'func': lambda item: item.get('user_id','')},
            {'name':'email', 'func': lambda item: item.get('email','')},
            {'name':'phone', 'func': lambda item: item.get('phone','')},
            {'name':'name', 'func': lambda item: item.get('name','')},
            {'name':'location_postal', 'func': lambda item: item.get('location_data',{}).get('postal_code','')},
            {'name':'location_city', 'func': lambda item: item.get('location_data',{}).get('city_name','')},
            {'name':'location_region', 'func': lambda item: item.get('location_data',{}).get('region_name','')},
            {'name':'location_country', 'func': lambda item: item.get('location_data',{}).get('country_name','')},
            {'name':'created_at', 'func': lambda item: item.get('created_at','')},
            {'name':'signed_up_at', 'func': lambda item: item.get('signed_up_at','')},
            {'name':'referrer', 'func': lambda item: item.get('referrer','')}
        ]

        results = []

        row = []
        for c in columns:
            row.append(c['name'])
        results.append(row)

        users = content.get('users',[])
        for item in users:
            row = []
            for c in columns:
                value = c.get('func')(item)
                row.append(value)
            results.append(row)

        flex.output.content_type = "application/json"
        flex.output.write(results)

    except:
        raise RuntimeError

