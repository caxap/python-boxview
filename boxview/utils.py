#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cgi
import six
import json
import datetime
import urllib
import urlparse
import requests
from requests.structures import CaseInsensitiveDict
from requests.adapters import HTTPAdapter
from requests.utils import default_user_agent


__all__ = ['default_headers', 'default_session', 'add_to_url', 'format_date',
           'get_mimetype_from_headers', 'format_error_response']


def default_headers():
    return CaseInsensitiveDict({
        'User-Agent': ' '.join(['python-boxview/1.0', default_user_agent()]),
        'Accept': '*/*',
        'Accept-Encoding': ', '.join(('gzip', 'deflate', 'compress')),
    })


def default_session(max_retries=3):
    session = requests.Session()
    session.mount('http://', HTTPAdapter(max_retries=max_retries))
    session.mount('https://', HTTPAdapter(max_retries=max_retries))
    return session


def add_to_url(url, **params):
    parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qsl(parts[4]), **params)
    parts[4] = urllib.urlencode(query)
    return urlparse.urlunparse(parts)


def pretty_json(data):
    return json.dumps(data,
                      sort_keys=True,
                      indent=4,
                      separators=(',', ': '))


def get_mimetype_from_headers(headers):
    content_type = headers.get('Content-Type')
    if content_type:
        return cgi.parse_header(content_type)[0].lower()


def format_error_response(response):
    content_type = get_mimetype_from_headers(response.headers)
    if content_type == 'application/json':
        error = '\n{}'.format(pretty_json(response.json()))
    else:
        error = response.reason or ''
    return "HTTP Status: {} {}".format(response.status_code, error)


def format_date(value):
    if isinstance(value, six.string_types):
        return value
    if isinstance(value, datetime.datetime):
        return value.replace(microsecond=0).isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()

    raise ValueError("Invalid date: {}".format(value))
