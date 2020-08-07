
# ---
# name: intercom-conversations
# deployed: true
# config: index
# title: Intercom Conversations
# description: Returns a list of conversations from Intercom
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
#     description: The id of conversation
#   - name: created_at
#     type: string
#     description: The time the conversation was created
#   - name: updated_at
#     type: string
#     description: The last time the conversation was updated
#   - name: waiting_since
#     type: string
#     description: The last time a contact responded to an admin
#   - name: snoozed_until
#     type: string
#     description: The time in the future when the conversation will be marked as open
#   - name: source_type
#     type: string
#     description: The type of conversation
#   - name: source_id
#     type: string
#     description: The id of the conversation
#   - name: source_delivered_as
#     type: string
#     description: The message subject
#   - name: source_subject
#     type: string
#     description: The message subject
#   - name: source_body
#     type: string
#     description: The message body
#   - name: source_author_type
#     type: string
#     description: The type of author who intiated the conversation
#   - name: source_author_id
#     type: string
#     description: The id of the author who initiated the conversation
#   - name: source_author_name
#     type: string
#     description: The name of the author who initiated the conversation
#   - name: source_author_email
#     type: string
#     description: The email address of the author who initiated the conversation
#   - name: source_url
#     type: string
#     description: The url where the conversation was started
#   - name: first_contact_reply_created_at
#     type: string
#     description: The time the contact replied
#   - name: first_contact_reply_type
#     type: string
#     description: The channel which the first reply occured over
#   - name: first_contact_reply_url
#     type: string
#     description: The URL where the first reply originated from
#   - name: assignee_type
#     type: string
#     description: The type of the assignee to the conversation
#   - name: assignee_id
#     type: string
#     description: The id of the assignee to the conversation
#   - name: open
#     type: boolean
#     description: Whether a conversation is open or closed
#   - name: state
#     type: string
#     description: State of the conversation
#   - name: read
#     type: boolean
#     description: Whether a conversation as been read or not
#   - name: priority
#     type: string
#     description: Whether a conversation is a priority
#   - name: sla_applied
#     type: string
#     description: The SLA applied to the conversation
#   - name: time_to_assignment
#     type: integer
#     description: Duration until last assignment before first admin reply
#   - name: time_to_admin_reply
#     type: integer
#     description: Duration until first admin reply
#   - name: time_to_first_close
#     type: integer
#     description: Duration until conversation was first closed
#   - name: time_to_last_close
#     type: integer
#     description: Duration until conversation was last closed
#   - name: median_time_to_reply
#     type: integer
#     description: Median based on all admin replies after a contact reply
#   - name: first_contact_reply_at
#     type: string
#     description: Time of first text conversation part from a contact
#   - name: first_assignment_at
#     type: string
#     description: Time of first assignment after first_contact_reply_at
#   - name: first_admin_reply_at
#     type: string
#     description: Time of first admin reploy after first_contact_reply_at
#   - name: first_close_at
#     type: string
#     description: Time of first close after first_contact_reply_at
#   - name: last_assignment_at
#     type: string
#     description: Time of last assignment after first_contact_reply_at
#   - name: last_assignment_admin_reply_at
#     type: string
#     description: Time of last assignment before first_admin_reply_at
#   - name: last_contact_reply_at
#     type: string
#     description: Time of the last conversation part from a contact
#   - name: last_admin_reply_at
#     type: string
#     description: Time of the last conversation part from an admin
#   - name: last_close_at
#     type: string
#     description: Time of the last conversation close
#   - name: last_closed_by_id
#     type: string
#     description: The id of the admin who closed the conversation
#   - name: count_reopens
#     type: integer
#     description: The number of reopens after first_contact_reply_at
#   - name: count_assignments
#     type: integer
#     description: The number of assignments after first_contact_reply_at
#   - name: count_conversation_parts
#     type: integer
#     description: The total number of conversation parts
# examples:
#   - '""'
#   - '"id, source_subject, state, created_at"'
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
    for data in get_data(flex.vars):
        flex.output.write(data)

def get_data(params):

    # get the api key from the variable input
    auth_token = dict(params).get('intercom_connection',{}).get('access_token')

    # see here for more info:
    # https://developers.intercom.com/intercom-api-reference/reference#conversation-model
    # https://developers.intercom.com/intercom-api-reference/reference#pagination

    headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer ' + auth_token,
        'Intercom-Version': '2.0' # api version
    }
    url = 'https://api.intercom.io/conversations'

    page_size = 50
    url_query_params = {"per_page": page_size}
    url_query_str = urllib.parse.urlencode(url_query_params)
    page_url = url + '?' + url_query_str

    while True:

        response = requests_retry_session().get(page_url, headers=headers)
        response.raise_for_status()
        content = response.json()
        data = content.get('conversations',[])

        if len(data) == 0: # sanity check in case there's an issue with cursor
            break

        buffer = ''
        for item in data:
            item = get_item_info(item)
            buffer = buffer + json.dumps(item, default=to_string) + "\n"
        yield buffer

        page_url = content.get('pages',{}).get('next')
        if page_url is None:
            break

def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(429, 500, 502, 503, 504),
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
    return datetime.utcfromtimestamp(int(ts)/1000).strftime('%Y-%m-%dT%H:%M:%S')

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
    info['created_at'] = to_date(item.get('created_at'))
    info['updated_at'] = to_date(item.get('updated_at'))
    info['waiting_since'] = to_date(item.get('waiting_since'))
    info['snoozed_until'] = to_date(item.get('waiting_since'))
    info['source_type'] = item.get('source',{}).get('type')
    info['source_id'] = item.get('source',{}).get('id')
    info['source_delivered_as'] = item.get('source',{}).get('delivered_as')
    info['source_subject'] = item.get('source',{}).get('subject')
    info['source_body'] = item.get('source',{}).get('body')
    info['source_author_type'] = item.get('source',{}).get('author',{}).get('type')
    info['source_author_id'] = item.get('source',{}).get('author',{}).get('id')
    info['source_author_name'] = item.get('source',{}).get('author',{}).get('name')
    info['source_author_email'] = item.get('source',{}).get('author',{}).get('email')
    info['source_url'] = item.get('source',{}).get('url')
    info['first_contact_reply_created_at'] = to_date(item.get('first_contact_reply',{}).get('created_at'))
    info['first_contact_reply_type'] = item.get('first_contact_reply',{}).get('type')
    info['first_contact_reply_url'] = item.get('first_contact_reply',{}).get('url')
    info['assignee_type'] = item.get('assignee',{}).get('type')
    info['assignee_id'] = item.get('assignee',{}).get('id')
    info['open'] = item.get('open')
    info['state'] = item.get('state')
    info['read'] = item.get('read')
    info['priority'] = item.get('priority')
    info['sla_applied'] = item.get('sla_applied')
    info['time_to_assignment'] = item.get('statistics',{}).get('time_to_assignment')
    info['time_to_admin_reply'] = item.get('statistics',{}).get('time_to_admin_reply')
    info['time_to_first_close'] = item.get('statistics',{}).get('time_to_first_close')
    info['time_to_last_close'] = item.get('statistics',{}).get('time_to_last_close')
    info['median_time_to_reply'] = item.get('statistics',{}).get('median_time_to_reply')
    info['first_contact_reply_at'] = to_date(item.get('statistics',{}).get('first_contact_reply_at'))
    info['first_assignment_at'] = to_date(item.get('statistics',{}).get('first_assignment_at'))
    info['first_admin_reply_at'] = to_date(item.get('statistics',{}).get('first_admin_reply_at'))
    info['first_close_at'] = to_date(item.get('statistics',{}).get('first_close_at'))
    info['last_assignment_at'] = to_date(item.get('statistics',{}).get('last_assignment_at'))
    info['last_assignment_admin_reply_at'] = to_date(item.get('statistics',{}).get('last_assignment_admin_reply_at'))
    info['last_contact_reply_at'] = to_date(item.get('statistics',{}).get('last_contact_reply_at'))
    info['last_admin_reply_at'] = to_date(item.get('statistics',{}).get('last_admin_reply_at'))
    info['last_close_at'] = to_date(item.get('statistics',{}).get('last_close_at'))
    info['last_closed_by_id'] = item.get('statistics',{}).get('last_closed_by_id')
    info['count_reopens'] = item.get('statistics',{}).get('count_reopens')
    info['count_assignments'] = item.get('statistics',{}).get('count_assignments')
    info['count_conversation_parts'] = item.get('statistics',{}).get('count_conversation_parts')

    return info
