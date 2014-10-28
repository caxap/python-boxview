#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
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
from urlparse import urljoin

__all__ = ['BoxView', 'BoxViewError']


API_VERSION = '1'
BASE_API_URL = 'https://view-api.box.com/'
BASE_UPLOAD_URL = 'https://upload.view-api.box.com/'

API_URL = '{}{}/'.format(BASE_API_URL, API_VERSION)
UPLOAD_URL = '{}{}/'.format(BASE_UPLOAD_URL, API_VERSION)

QUEUED, PROCESSING, DONE, ERROR = ('queued', 'processing', 'done', 'error')


def add_to_url(url, **params):
    parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qsl(parts[4]), **params)
    parts[4] = urllib.urlencode(query)
    return urlparse.urlunparse(parts)


def get_mimetype_from_headers(headers):
    content_type = headers.get('Content-Type', '')
    if content_type:
        return cgi.parse_header(content_type)[0]


def format_date(value):
    if isinstance(value, six.string_types):
        return value
    if isinstance(value, datetime.datetime):
        return value.replace(microsecond=0).isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()

    raise ValueError("Invalid date: {}".format(value))


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


class BoxViewError(Exception):

    def __init__(self, response):
        Exception.__init__(self)
        self.response = response

    def _get_error(self):
        if self.response.headers.get('Content-Type') == 'application/json':
            error = json.dumps(self.response.json(),
                               sort_keys=True,
                               indent=4,
                               separators=(',', ': '))
            return '\n{}'.format(error)
        return self.response.reason or ''

    def __str__(self):
        return "HTTP Status: {} {}".format(
            self.response.status_code,
            self._get_error())


def _get_box_view_api_key():
    api_key = os.environ.get('BOX_VIEW_API_KEY')
    if not api_key:
        raise ValueError("Box View api key is required")
    return api_key


class TokenAuth(object):

    def __init__(self, token):
        self.token = token

    def authorization_header(self):
        return 'Token {}'.format(self.token)

    def populate_to_headers(self, headers):
        headers['Authorization'] = self.authorization_header()

    def __str__(self):
        return self.token


class BoxView(object):

    def __init__(self,
                 api_key=None,
                 headers=None,
                 session=None,
                 timeout=None,
                 base_url=API_URL):
        if not api_key:
            api_key = _get_box_view_api_key()

        self.token = TokenAuth(api_key)
        self.timeout = timeout
        self.base_url = base_url

        if session is None:
            session = default_session()

        if headers is None:
            headers = default_headers()

        self.token.populate_to_headers(headers)
        session.headers = headers

        self.session = session

    def request(self, method, url, **kwargs):
        url = urljoin(self.base_url, url)

        kwargs.setdefault('timeout', self.timeout)
        kwargs.setdefault('allow_redirects', method.upper() == 'GET')

        response = self.session.request(method, url, **kwargs)
        if not response.ok:
            raise BoxViewError(response)

        return response

    def create_document(self,
                        url=None,
                        file=None,
                        name='',
                        thumbnails='',
                        non_svg=False):
        if not url and not file:
            raise ValueError("Document url or file is required")

        data = {}
        if name:
            data['name'] = name
        if thumbnails:
            data['thumbnails'] = thumbnails
        if non_svg:
            data['non_svg'] = bool(non_svg)

        if url:
            return self.create_document_from_url(url, **data)
        else:
            return self.create_document_from_file(file, **data)

    def create_document_from_file(self, file, **data):

        def _create_from_file(file):
            url = urljoin(UPLOAD_URL, 'documents')
            files = {'file': file}
            response = self.request('POST',
                                    url,
                                    data=data,
                                    files=files)
            return response.json()

        if hasattr(file, 'read'):
            return _create_from_file(file)
        else:
            with open(file, 'rb') as file:
                return _create_from_file(file)

    def create_document_from_url(self, url, **data):
        data['url'] = url
        headers = {'Content-type': 'application/json'}
        response = self.request('POST',
                                'documents',
                                data=json.dumps(data),
                                headers=headers)
        return response.json()

    def get_document(self, document_id, fields=None):
        url = 'documents/{}'.format(document_id)
        if fields:
            params = {'fields': fields}
        else:
            params = None
        return self.request('GET', url, params=params).json()

    def delete_document(self, document_id):
        url = 'documents/{}'.format(document_id)
        self.request('DELETE', url)

    def update_document(self, document_id, name):
        url = 'documents/{}'.format(document_id)
        data = {'name': name}
        headers = {'Content-type': 'application/json'}
        response = self.request('PUT',
                                url,
                                data=json.dumps(data),
                                headers=headers)
        return response.json()

    def get_documents(self,
                      limit=None,
                      created_before=None,
                      created_after=None):
        params = {}
        if limit:
            params['limit'] = limit
        if created_after:
            params['created_after'] = format_date(created_after)
        if created_before:
            params['created_before'] = format_date(created_before)

        return self.request('GET', 'documents', params=params).json()

    def get_thumbnail(self, stream, document_id, width, height):
        url = 'documents/{}/thumbnail'.format(document_id)
        params = {
            'width': width,
            'height': height,
        }
        response = self.request('GET', url, params=params)

        for chunk in response.iter_content():
            stream.write(chunk)

        return get_mimetype_from_headers(response.headers)

    def get_thumbnail_to_file(self, filename, document_id, width, height):
        with open(filename, 'wb') as fp:
            return self.get_thumbnail(fp, document_id, width, height)

    def get_thumbnail_to_string(self, document_id, width, height):
        fp = six.BytesIO()
        mimetype = self.get_thumbnail(fp, document_id, width, height)
        return fp.getvalue(), mimetype

    def get_document_content(self, stream, document_id, extension=None):
        url = 'documents/{}/content'.format(document_id)

        allowed_extensions = ['.pdf', '.zip']
        if extension:
            if extension in allowed_extensions:
                url = '{0}{1}'.format(url, extension)
            else:
                raise ValueError(
                    "Invalid extension '{0}'; choose one of {1}".format(
                        extension, ', '.join(allowed_extensions)))

        response = self.request('GET', url, stream=True)

        for chunk in response.iter_content():
            stream.write(chunk)

        return get_mimetype_from_headers(response.headers)

    def get_document_content_to_file(self,
                                     filename,
                                     document_id,
                                     extension=None):
        with open(filename, 'wb') as fp:
            return self.get_document_content(fp, document_id, extension)

    def get_document_content_to_string(self, document_id, extension=None):
        fp = six.BytesIO()
        mimetype = self.get_document_content(fp, document_id, extension)
        return fp.getvalue(), mimetype

    def get_document_content_mimetype(self, document_id):
        url = 'documents/{}/content'.format(document_id)
        response = self.request('HEAD', url)
        return get_mimetype_from_headers(response.headers)

    def create_session(self,
                       document_id,
                       duration=None,
                       expires_at=None,
                       is_downloadable=False,
                       is_text_selectable=True):
        data = {'document_id': document_id}
        if duration:
            data['duration'] = duration
        if expires_at:
            data['expires_at'] = format_date(expires_at)
        if is_downloadable:
            data['is_downloadable'] = bool(is_downloadable)
        if is_text_selectable:
            data['is_text_selectable'] = bool(is_text_selectable)
        headers = {'Content-type': 'application/json'}

        response = self.request('POST',
                                'sessions',
                                data=json.dumps(data),
                                headers=headers)
        return response.json()

    def ready_to_view(self, document_id):
        document = self.get_document(document_id)
        if document['status'] == DONE:
            return document

    def get_document_status(self, document_id):
        document = self.get_document(document_id)
        return document['status']

    @staticmethod
    def get_session_url(session_id, type='view', **params):
        """ Allowed types are: `view`, `assets`, `download`. """
        url = 'sessions/{}/{}'.format(session_id, type)
        url = urljoin(API_URL, url)
        return add_to_url(url, **params)

    @staticmethod
    def get_realtime_url(session_id):
        url = 'sse/{}'.format(session_id)
        return urljoin(BASE_API_URL, url)
