
# ---
# name: intercom-companies
# deployed: true
# title: Intercom Companies
# description: Returns a list of companies from Intercom
# params:
#   - name: properties
#     type: array
#     description: The properties to return (defaults to all properties). See "Returns" for a listing of the available properties.
#     required: false
#   - name: filter
#     type: string
#     description: Filter to apply with key/values specified as a URL query string where the keys correspond to the properties to filter.
#     required: false
# returns:
#   - name: id
#     type: string
#     description: The unique identifier for the company which is given by Intercom
#   - name: company_id
#     type: string
#     description: The company id you have defined for the company
#   - name: name
#     type: string
#     description: The name of the company
#   - name: created_at
#     type: string
#     description: The time the company was added to Intercom
#   - name: remote_created_at
#     type: string
#     description: The time the company was created by the user business
#   - name: updated_at
#     type: string
#     description: The last time the company was updated
#   - name: last_request_at
#     type: string
#     description: The time the company last recorded making a request
#   - name: session_count
#     type: integer
#     description: How many sessions the company has recorded
#   - name: monthly_spend
#     type: integer
#     description: How much revenue the company generates for the user business
#   - name: user_count
#     type: integer
#     description: The number of users in the company
#   - name: size
#     type: integer
#     description: The number of employees in the company
#   - name: website
#     type: string
#     description: The URL for the company website
#   - name: industry
#     type: string
#     description: The industry that the company operates in
# examples:
#   - '*'
#   - '"compay_id, name"'
# ---

import json
import urllib
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from datetime import *
from decimal import *
from collections import OrderedDict

# main function entry point
def flexio_handler(flex):

    flex.output.content_type = 'application/x-ndjson'
    for item in get_data(flex.vars):
        result = json.dumps(item, default=to_string) + "\n"
        flex.output.write(result)

def get_data(params):

    # get the api key from the variable input
    auth_token = dict(params).get('intercom_connection',{}).get('access_token')

    # see here for more info:
    # https://developers.intercom.com/intercom-api-reference/reference#company-model
    # https://developers.intercom.com/intercom-api-reference/reference#pagination

    headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer ' + auth_token,
        'Intercom-Version': '2.0' # api version
    }
    url = 'https://api.intercom.io/companies'

    page_size = 50
    url_query_params = {"per_page": page_size}
    url_query_str = urllib.parse.urlencode(url_query_params)
    page_url = url + '?' + url_query_str

    while True:

        response = requests_retry_session().get(page_url, headers=headers)
        response.raise_for_status()
        content = response.json()
        data = content.get('data',[])

        if len(data) == 0: # sanity check in case there's an issue with cursor
            break

        for item in data:
            yield get_item_info(item)

        page_url = content.get('pages',{}).get('next')
        if page_url is None:
            break

def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def to_date(ts):
    if ts is None or ts == '':
        return ''
    return datetime.utcfromtimestamp(int(ts)/1000).strftime('%Y-%m-%d %H:%M:%S')

def to_string(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (Decimal)):
        return str(value)
    return value

def get_item_info(item):

    # map this function's property names to the API's property names
    info = OrderedDict()

    info['id'] = item.get('id')
    info['company_id'] = item.get('company_id')
    info['name'] = item.get('name')
    info['created_at'] = to_date(item.get('created_at'))
    info['remote_created_at'] = to_date(item.get('remote_created_at'))
    info['updated_at'] = to_date(item.get('updated_at'))
    info['last_request_at'] = to_date(item.get('last_request_at'))
    info['session_count'] = item.get('session_count')
    info['monthly_spend'] = item.get('monthly_spend')
    info['user_count'] = item.get('user_count')
    info['size'] = item.get('size')
    info['website'] = item.get('website')
    info['industry'] = item.get('industry')

    return info
