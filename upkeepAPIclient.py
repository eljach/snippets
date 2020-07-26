import requests
import logging
import json
from django.conf import settings

logger = logging.getLogger(__name__)

class UpkeepAPI():
    update_create_fields_map = {
            'name': 'display_name',
            'address': '',
            'longitude': '',
            'latitude': '',
            'hideMap': '',
    }

    def __init__(self, email=None, password=None,):
        if email is None:
            self.email = settings.UPKEEP_EMAIL
        else:
            self.email = email
        if password is None:
            self.password = settings.UPKEEP_PASSWORD
        else:
            self.password = password
        self.token = None
        self.session = requests.Session()
        self._get_auth_token(3)
        self._set_requests_session()

    def _get_auth_token(self, retries=1):
        url = 'https://api.onupkeep.com/api/v2/auth/'
        email = self.email
        password = self.password

        payload = {
            'email': email,
            'password': password
        }
        headers = {
            'Content-Type': "application/json",
            'Cache-Control': "no-cache"
        }
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code >= 200 and response.status_code <= 299:
            self.token = json.loads(response.text)['result']['sessionToken']
        else:
            if retries == 0:
                exception_string = "Could not authenticate to Upkeep API: Error {}".format(
                    response.status_code)
                logger.error(exception_string)
                raise Exception(exception_string)
            else:
                self._get_auth_token(retries=retries-1)

    def _set_requests_session(self):
        common_headers = {
            'Cache-Control': "no-cache",
            "Session-Token": self.token
        }
        self.session.headers.update(common_headers)

    def _get_response(self, method, url, data=None, parameters=None):
        request = requests.Request(method, url, data=data, params=parameters)
        prepped_request = self.session.prepare_request(request)
        response = self.session.send(prepped_request)
        if response.status_code >= 200 and response.status_code <= 299:
            return json.loads(response.text)
        else:
            exception_string = "Unable to retrieve data from {}. Error {} - {}".format(
                url, response.status_code, response.text)
            logger.error(exception_string)
            raise Exception(exception_string)

    def get_all_locations(self):
        url = 'https://api.onupkeep.com/api/v2/locations'
        response = self._get_response('GET', url)
        return response['results']

    def get_location(self, upkeep_code):
        url = 'https://api.onupkeep.com/api/v2/locations/{}'.format(upkeep_code)
        response = self._get_response('GET', url)
        return response['result']

    def update_location(self, location, **kwargs):
        url= 'https://api.onupkeep.com/api/v2/locations/{}'.format(location.upkeep_code)
        data = {}
        for key,value in kwargs.items():
            if key in self.update_create_fields_map.keys():
                data[key] = value
        response = self._get_response('PATCH', url, data)
        return response['result']

    def create_location(self, location):
        url = 'https://api.onupkeep.com/api/v2/locations/'
        data = {}
        for upkeep_field, local_field in self.update_create_fields_map.items():
            try:
                data[upkeep_field] = getattr(location, local_field)
            except AttributeError:
                continue
        response = self._get_response('POST', url, data)
        return response['result']

    def create_asset(self, payload):
        url = 'https://api.onupkeep.com/api/v2/assets/'
        response = self._get_response('POST', url, payload)
        return response['result']

    def update_asset(self, upkeep_code, payload):
        url = 'https://api.onupkeep.com/api/v2/assets/{}'.format(upkeep_code)
        response = self._get_response('PATCH', url, payload)
        return response['result']

    def create_asset_meter(self, payload):
        url = 'https://api.onupkeep.com/api/v2/meters/'
        response = self._get_response('POST', url, payload)
        return response['result']

    def update_asset_meter(self, meter_upkeep_id, payload):
        url = 'https://api.onupkeep.com/api/v2/meters/{}'.format(meter_upkeep_id)
        response = self._get_response('PATCH', url, payload)
        return response['result']

    def update_asset_meter_reading(self, meter):
        url = 'https://api.onupkeep.com/api/v2/meters/{}/readings'.format(meter.upkeep_id)
        response = self._get_response('POST', url, {'value':meter.transactions_counter})
        return response['result']

    def create_work_order(self, payload):
        url = 'https://api.onupkeep.com/api/v2/work-orders/'
        response = self._get_response('POST', url, payload)
        return response['result']
