import json

import requests

try:
    import Image
except ImportError:
    from PIL import Image

"""

Utils functions to work with NaviAddress API

"""


def get_token(email, password):
    url = 'https://staging-api.naviaddress.com/api/v1.5/Sessions'

    payload = {'email': email, 'password': password}
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    r = requests.post(url, json=payload, headers=headers)
    return json.loads(r.text).get('token')


def create_naviaddress(token, lat, long):
    url = 'https://staging-api.naviaddress.com/api/v1.5/addresses/'

    payload = {'lat': lat, 'lng': long, 'address_type': 'free', 'default_lang': 'ru'}
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'auth-token': token}

    r = requests.post(url, json=payload, headers=headers)
    return r.json().get('result').get('container'), r.json().get('result').get('naviaddress')


def accept_naviaddress(token, container, naviaddress):
    url = 'https://staging-api.naviaddress.com/api/v1.5/addresses/accept/' + container + '/' + naviaddress

    payload = {}
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'auth-token': token}

    r = requests.post(url, json=payload, headers=headers)
    return r.text


def put_naviadress(token, container, naviaddress, params):
    url = 'https://staging-api.naviaddress.com/api/v1.5/addresses/' + container + '/' + naviaddress + '?lang=ru'
    payload = params
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'auth-token': token}

    r = requests.put(url, json=payload, headers=headers)
    return r


def get_naviadress(token, container, naviaddress):
    url = 'https://staging-api.naviaddress.com/api/v1.5/addresses/' + container + '/' + naviaddress + '?lang=ru'
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'auth-token': token}

    r = requests.get(url, headers=headers)
    return r.text
