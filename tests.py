#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import six
import json
import datetime
import unittest
from mock import patch
from urlparse import urljoin
from requests.models import Response
from requests.sessions import Session
from boxview.boxview import BoxView, BoxViewError, RetryAfter, API_URL
from boxview.utils import format_date, get_mimetype_from_headers


test_url = 'https://cloud.box.com/shared/static/4qhegqxubg8ox0uj5ys8.pdf'

test_document = {
    "type": "document",
    "id": "2da6cf9261824fb0a4fe532f94d14625",
    "status": "done",
    "name": "Leaves of Grass",
    "created_at": "2013-08-30T00:17:37Z",
    "modified_at": "2013-08-30T00:17:37Z"
}

test_document_list = {
    "document_collection": {
        "total_count": 1,
        "entries": [test_document],
    }
}

test_session = {
    'type': 'session',
    'id': '4fba9eda0dd745d491ad0b98e224aa25',
    'expires_at': '3915-10-29T01:31:48.677Z',
    'urls': {
        'view': 'https://view-api.box.com/1/sessions/4fba9eda0dd745d491ad0b98e224aa25/view',
        'assets': 'https://view-api.box.com/1/sessions/4fba9eda0dd745d491ad0b98e224aa25/assets/',
        'realtime': 'https://view-api.box.com/sse/4fba9eda0dd745d491ad0b98e224aa25',
    },
}


class BoxViewTestCase(unittest.TestCase):

    def setUp(self):
        self.api = BoxView('<box view api key>')

    def test_initials(self):
        # api key is required
        self.assertRaises(ValueError, BoxView)

        now = datetime.datetime.utcnow().replace(microsecond=0)
        dtfiso = now.isoformat()
        dfiso = now.date().isoformat()

        self.assertEqual(dtfiso, format_date(dtfiso))
        self.assertEqual(dtfiso, format_date(now))
        self.assertEqual(dfiso, format_date(now.date()))

        headers = {'Content-Type': 'text/plain'}
        self.assertEqual('text/plain', get_mimetype_from_headers(headers))
        headers = {'Content-Type': 'text/plain; charset=utf-8'}
        self.assertEqual('text/plain', get_mimetype_from_headers(headers))

    @patch.object(Session, 'request')
    def test_crate_document_from_url(self, mock_request):
        response = Response()
        response.status_code = 201
        response._content = json.dumps(test_document)
        mock_request.return_value = response

        result = self.api.create_document(url=test_url,
                                          name='Test Document',
                                          thumbnails='100x100,200x200',
                                          non_svg=False)
        self.assertIsNotNone(result)
        self.assertEqual(result, test_document)

        data = {
            'url': test_url,
            'name': 'Test Document',
            'thumbnails': '100x100,200x200',
        }
        headers = {'Content-Type': 'application/json'}
        url = urljoin(API_URL, 'documents')
        mock_request.assert_called_with('POST', url,
                                        data=json.dumps(data),
                                        headers=headers)

        # url of file param is required
        self.assertRaises(ValueError, self.api.create_document)

    @patch.object(Session, 'request')
    def test_create_document_from_file(self, mock_request):
        response = Response()
        response.status_code = 201
        response._content = json.dumps(test_document)
        mock_request.return_value = response

        stream = six.BytesIO()
        result = self.api.create_document_from_file(stream,
                                                    name='Test Document')
        self.assertEqual(result, test_document)

        result = self.api.create_document_from_file(__file__,
                                                    name='Test Document')
        self.assertEqual(result, test_document)

    @patch.object(Session, 'request')
    def test_get_document(self, mock_request):
        response = Response()
        response.status_code = 200
        response._content = json.dumps(test_document)
        mock_request.return_value = response

        result = self.api.get_document(test_document['id'])
        self.assertIsNotNone(result)
        self.assertEqual(result, test_document)

    @patch.object(Session, 'request')
    def test_get_documents(self, mock_request):
        response = Response()
        response.status_code = 200
        response._content = json.dumps(test_document_list)
        mock_request.return_value = response

        now = datetime.datetime.utcnow()
        result = self.api.get_documents(limit=10, created_before=now)
        self.assertIsNotNone(result)
        self.assertEqual(result, test_document_list)

    @patch.object(Session, 'request')
    def test_update_document(self, mock_request):
        response = Response()
        response.status_code = 200
        response._content = json.dumps(test_document)
        mock_request.return_value = response

        result = self.api.update_document(test_document['id'],
                                          name='TestDocument')
        self.assertIsNotNone(result)
        self.assertEqual(result, test_document)

    @patch.object(Session, 'request')
    def test_delete_document(self, mock_request):
        response = Response()
        response.status_code = 204
        mock_request.return_value = response

        self.api.delete_document(test_document['id'])

    @patch.object(Session, 'request')
    def test_get_document_content(self, mock_request):
        response = Response()
        response.status_code = 200
        response.headers['Content-Type'] = 'text/plain'
        response._content = 'test'
        response.raw = six.BytesIO('test')
        mock_request.return_value = response

        stream = six.BytesIO()
        mimetype = self.api.get_document_content(stream, test_document['id'])
        self.assertEqual(stream.getvalue(), response._content)
        self.assertEqual(mimetype, response.headers['Content-Type'])

        stream = six.BytesIO()
        self.api.get_document_content(stream,
                                      test_document['id'],
                                      extension='.pdf')
        self.assertEqual(stream.getvalue(), response._content)

        stream = six.BytesIO()
        self.api.get_document_content(stream,
                                      test_document['id'],
                                      extension='.zip')
        self.assertEqual(stream.getvalue(), response._content)

        stream = six.BytesIO()
        # allowed only .zip and .pdf extensions
        self.assertRaises(ValueError,
                          self.api.get_document_content,
                          stream,
                          test_document['id'],
                          extension='.docx')

    @patch.object(Session, 'request')
    def test_get_document_content_to_string(self, mock_request):
        response = Response()
        response.status_code = 200
        response.headers['Content-Type'] = 'text/plain'
        response._content = 'test'
        response.raw = six.BytesIO('test')
        mock_request.return_value = response

        doc_id = test_document['id']
        result, mimetype = self.api.get_document_content_to_string(doc_id)
        self.assertIsNotNone(result)
        self.assertEqual(result, response._content)
        self.assertEqual(mimetype, response.headers['Content-Type'])

    @patch.object(Session, 'request')
    def test_get_document_content_to_file(self, mock_request):
        response = Response()
        response.status_code = 200
        response.headers['Content-Type'] = 'text/plain'
        response._content = 'test'
        response.raw = six.BytesIO('test')
        mock_request.return_value = response

        filename = 'boxview.txt'
        mimetype = self.api.get_document_content_to_file(filename,
                                                         test_document['id'])
        self.assertEqual(mimetype, response.headers['Content-Type'])
        self.assertTrue(os.path.exists(filename))
        try:
            os.remove(filename)
        except OSError:
            pass

    @patch.object(Session, 'request')
    def test_get_document_content_mimetype(self, mock_request):
        response = Response()
        response.status_code = 200
        response.headers['Content-Type'] = 'text/plain'
        mock_request.return_value = response

        mimetype = self.api.get_document_content_mimetype(test_document['id'])
        self.assertEqual(mimetype, response.headers['Content-Type'])

    @patch.object(Session, 'request')
    def test_create_session(self, mock_request):
        response = Response()
        response.status_code = 201
        response._content = json.dumps(test_session)
        mock_request.return_value = response

        expires_at = datetime.datetime.utcnow()
        doc_id = test_document['id']
        result = self.api.create_session(doc_id,
                                         duration=600,
                                         expires_at=expires_at,
                                         is_downloadable=True,
                                         is_text_selectable=True)
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], test_session['id'])

        data = {
            'document_id': doc_id,
            'duration': 600,
            'expires_at': expires_at.replace(microsecond=0).isoformat(),
            'is_downloadable': True,
            'is_text_selectable': True
        }
        headers = {'Content-Type': 'application/json'}
        url = urljoin(API_URL, 'sessions')
        mock_request.assert_called_with('POST', url,
                                        data=json.dumps(data),
                                        headers=headers)

    @patch.object(Session, 'request')
    def test_ready_to_view(self, mock_request):
        response = Response()
        response.status_code = 200
        response._content = json.dumps(test_document)
        mock_request.return_value = response

        result = self.api.ready_to_view(test_document['id'])
        self.assertIsNotNone(result)
        self.assertTrue(bool(result))

        response._content = json.dumps(dict(test_document, status='error'))

        result = self.api.ready_to_view(test_document['id'])
        self.assertFalse(bool(result))

    @patch.object(Session, 'request')
    def test_request_error(self, mock_request):
        response = Response()
        response.status_code = 401
        response._content = 'Unauthorized'
        response.reason = 'Unauthorized'
        mock_request.return_value = response

        self.assertRaises(BoxViewError,
                          self.api.get_document,
                          test_document['id'])

    @patch.object(Session, 'request')
    def test_request_retry_after(self, mock_request):
        response = Response()
        response.status_code = 202
        response.headers['Retry-After'] = '100.0'
        mock_request.return_value = response

        try:
            self.api.get_thumbnail_to_string(test_document['id'], 100, 100)
        except RetryAfter as e:
            self.assertEqual(e.seconds, 100.0)
        else:
            self.assertTrue(False)

    @patch.object(Session, 'request')
    def test_get_thumbnail(self, mock_request):
        response = Response()
        response.status_code = 200
        response.headers['Content-Type'] = 'image/png'
        response._content = 'test'
        response.raw = six.BytesIO('test')
        mock_request.return_value = response

        stream = six.BytesIO()
        mimetype = self.api.get_thumbnail(stream, test_document['id'], 100, 100)
        self.assertEqual(stream.getvalue(), response._content)
        self.assertEqual(mimetype, response.headers['Content-Type'])

    @patch.object(Session, 'request')
    def test_get_thumbnail_to_string(self, mock_request):
        response = Response()
        response.status_code = 200
        response.headers['Content-Type'] = 'image/png'
        response._content = 'test'
        response.raw = six.BytesIO('test')
        mock_request.return_value = response

        doc_id = test_document['id']
        result, mimetype = self.api.get_thumbnail_to_string(doc_id, 100, 100)
        self.assertIsNotNone(result)
        self.assertEqual(result, response._content)
        self.assertEqual(mimetype, response.headers['Content-Type'])

    @patch.object(Session, 'request')
    def test_get_thumbnail_to_file(self, mock_request):
        response = Response()
        response.status_code = 200
        response.headers['Content-Type'] = 'image/png'
        response._content = 'test'
        response.raw = six.BytesIO('test')
        mock_request.return_value = response

        filename = 'boxview.png'
        mimetype = self.api.get_thumbnail_to_file(filename,
                                                  test_document['id'],
                                                  100, 100)
        self.assertEqual(mimetype, response.headers['Content-Type'])
        self.assertTrue(os.path.exists(filename))
        try:
            os.remove(filename)
        except OSError:
            pass


if __name__ == '__main__':
    unittest.main()
