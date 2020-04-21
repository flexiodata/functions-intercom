
# ---
# name: intercom-contacts
# deployed: true
# title: Intercom Contacts
# description: Returns a list of contacts from Intercom
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
#     description: The unique identifier for the contact which is given by Intercom
#   - name: workspace_id
#     type: string
#     description: The id of the workspace which the contact belongs to
#   - name: external_id
#     type: string
#     description: A unique identifier for the contact which is given to Intercom
#   - name: role
#     type: string
#     description: The role of the contact (either user or lead)
#   - name: email
#     type: string
#     description: The email for the contact
#   - name: phone
#     type: string
#     description: The phone for the contact
#   - name: name
#     type: string
#     description: The name of the contact
#   - name: avatar
#     type: string
#     description: An image URL containing the avatar of a contact
#   - name: owner_id
#     type: string
#     description: The id of an administrator that has been assigned account ownership of the contact
#   - name: has_hard_bounced
#     type: boolean
#     description: Whether the contact has had an email sent to them hard bounce
#   - name: marked_email_as_spam
#     type: boolean
#     description: Whether the contact has marked an email sent to them as spam
#   - name: unsubscribed_from_emails
#     type: boolean
#     description: Whether the contact is unsubscribed from emails
#   - name: created_at
#     type: string
#     description: The time when the contact was created
#   - name: updated_at
#     type: string
#     description: The time when the contact was last updated
#   - name: signed_up_at
#     type: string
#     description: The time specified for when a contact signed up
#   - name: last_seen_at
#     type: string
#     description: The time when the contact was last seen (either where the Intercom Messenger was installed or when specified manually)
#   - name: last_replied_at
#     type: string
#     description: The time when the contact last messaged in
#   - name: last_contacted_at
#     type: string
#     description: The time when the contact was last messaged
#   - name: last_email_opened_at
#     type: string
#     description: The time when the contact last opened an email
#   - name: last_email_clicked_at
#     type: string
#     description: The time when the contact last clicked a link in an email
#   - name: language_override
#     type: string
#     description: A preferred language setting for the contact, used by the Intercom Messenger even if their browser settings change
#   - name: browser
#     type: string
#     description: The name of the browser which the contact is using
#   - name: browser_version
#     type: string
#     description: The version of the browser which the contact is using
#   - name: browser_language
#     type: string
#     description: The language set by the browser which the contact is using
#   - name: os
#     type: string
#     description: The operating system which the contact is using
#   - name: location_country
#     type: string
#     description: The country location of the contact
#   - name: location_region
#     type: string
#     description: The region location of the contact
#   - name: location_city
#     type: string
#     description: The city location of the contact
#   - name: android_app_name
#     type: string
#     description: The name of the Android app which the contact is using
#   - name: android_app_version
#     type: string
#     description: The version of the Android app which the contact is using
#   - name: android_device
#     type: string
#     description: The Android device which the contact is using
#   - name: android_os_version
#     type: string
#     description: The version of the Android OS which the contact is using
#   - name: android_sdk_version
#     type: string
#     description: The version of the Android SDK which the contact is using
#   - name: android_last_seen_at
#     type: string
#     description: The last time the contact used the Android app
#   - name: ios_app_name
#     type: string
#     description: The name of the iOS app which the contact is using
#   - name: ios_app_version
#     type: string
#     description: The version of the iOS app which the contact is using
#   - name: ios_device
#     type: string
#     description: The iOS device which the contact is using
#   - name: ios_os_version
#     type: string
#     description: The version of iOS which the contact is using
#   - name: ios_sdk_version
#     type: string
#     description: The version of the iOS SDK which the contact is using
#   - name: ios_last_seen_at
#     type: string
#     description: The last time the contact used the iOS app
# examples:
#   - '*'
#   - '"email, name"'
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
    # https://developers.intercom.com/intercom-api-reference/reference#contacts-model
    # https://developers.intercom.com/intercom-api-reference/reference#pagination

    headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer ' + auth_token,
        'Intercom-Version': '2.0' # api version
    }
    url = 'https://api.intercom.io/contacts'

    page_size = 50
    page_cursor_id = None

    while True:

        url_query_params = {"per_page": page_size}
        if page_cursor_id is not None:
            url_query_params['starting_after'] = page_cursor_id
        url_query_str = urllib.parse.urlencode(url_query_params)
        page_url = url + '?' + url_query_str

        response = requests_retry_session().get(page_url, headers=headers)
        response.raise_for_status()
        content = response.json()
        data = content.get('data',[])

        if len(data) == 0: # sanity check in case there's an issue with cursor
            break

        for item in data:
            yield get_item_info(item)

        page_cursor_id = content.get('pages',{}).get('next',{}).get('starting_after')
        if page_cursor_id is None:
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

def to_date(value):
    # TODO: convert to date string format
    return value

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
    info['workspace_id'] = item.get('workspace_id')
    info['external_id'] = item.get('external_id')
    info['role'] = item.get('role')
    info['email'] = item.get('email')
    info['phone'] = item.get('phone')
    info['name'] = item.get('name')
    info['avatar'] = item.get('avatar')
    info['owner_id'] = item.get('owner_id')
    info['has_hard_bounced'] = item.get('has_hard_bounced')
    info['marked_email_as_spam'] = item.get('marked_email_as_spam')
    info['unsubscribed_from_emails'] = item.get('unsubscribed_from_emails')
    info['created_at'] = to_date(item.get('created_at'))
    info['updated_at'] = to_date(item.get('updated_at'))
    info['signed_up_at'] = to_date(item.get('signed_up_at'))
    info['last_seen_at'] = to_date(item.get('last_seen_at'))
    info['last_replied_at'] = to_date(item.get('last_replied_at'))
    info['last_contacted_at'] = to_date(item.get('last_contacted_at'))
    info['last_email_opened_at'] = to_date(item.get('last_email_opened_at'))
    info['last_email_clicked_at'] = to_date(item.get('last_email_clicked_at'))
    info['language_override'] = item.get('language_override')
    info['browser'] = item.get('browser')
    info['browser_version'] = item.get('browser_version')
    info['browser_language'] = item.get('browser_language')
    info['os'] = item.get('os')
    info['location_country'] = item.get('location',{}).get('country')
    info['location_region'] = item.get('location',{}).get('region')
    info['location_city'] = item.get('location',{}).get('city')
    info['android_app_name'] = item.get('android_app_name')
    info['android_app_version'] = item.get('android_app_version')
    info['android_device'] = item.get('android_device')
    info['android_os_version'] = item.get('android_os_version')
    info['android_sdk_version'] = item.get('android_sdk_version')
    info['android_last_seen_at'] = to_date(item.get('android_last_seen_at'))
    info['ios_app_name'] = item.get('ios_app_name')
    info['ios_app_version'] = item.get('ios_app_version')
    info['ios_device'] = item.get('ios_device')
    info['ios_os_version'] = item.get('ios_os_version')
    info['ios_sdk_version'] = item.get('ios_sdk_version')
    info['ios_last_seen_at'] = to_date(item.get('ios_last_seen_at'))

    return info
