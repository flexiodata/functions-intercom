
# ---
# name: intercom-event-list
# deployed: true
# title: Intercom Event List
# description: Lists all the events for a given user
# params:
# - name: user_id
#   type: string
#   description: The id of the user to list the events for
#   required: true
# examples:
# - '1234'
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
    params['user_id'] = {'required': True, 'type': 'string', 'coerce': str}
    input = dict(zip(params.keys(), input))

    # validate the mapped input against the validator
    # if the input is valid return an error
    v = Validator(params, allow_unknown = True)
    input = v.validated(input)
    if input is None:
        raise ValueError

    try:

        # see here for more info: https://developers.intercom.com/intercom-api-reference/reference
        url = 'https://api.intercom.io/events?type=user&user_id='+input['user_id']
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
            {'name':'event_name', 'func': lambda item: item.get('event_name','')},
            {'name':'created_at', 'func': lambda item: item.get('created_at','')}
        ]

        results = []

        row = []
        for c in columns:
            row.append(c['name'])
        results.append(row)

        events = content.get('events',[])
        for item in events:
            row = []
            for c in columns:
                value = c.get('func')(item)
                row.append(value)
            results.append(row)

        flex.output.content_type = "application/json"
        flex.output.write(results)

    except:
        raise RuntimeError

