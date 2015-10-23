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


TEST_URL = 'https://cloud.box.com/shared/static/4qhegqxubg8ox0uj5ys8.pdf'

TEST_DOCUMENT = {
    "type": "document",
    "id": "2da6cf9261824fb0a4fe532f94d14625",
    "status": "done",
    "name": "Leaves of Grass",
    "created_at": "2013-08-30T00:17:37Z",
    "modified_at": "2013-08-30T00:17:37Z"
}

TEST_DOCUMENT_LIST = {
    "document_collection": {
        "total_count": 1,
        "entries": [TEST_DOCUMENT],
    }
}

TEST_SESSION = {
    'type': 'session',
    'id': '4fba9eda0dd745d491ad0b98e224aa25',
    'expires_at': '3915-10-29T01:31:48.677Z',
    'urls': {
        'view': 'https://view-api.box.com/1/sessions/4fba9eda0dd745d491ad0b98e224aa25/view',
        'assets': 'https://view-api.box.com/1/sessions/4fba9eda0dd745d491ad0b98e224aa25/assets/',
        'realtime': 'https://view-api.box.com/sse/4fba9eda0dd745d491ad0b98e224aa25',
    },
}

TEST_STORAGE_PROFILE = {
    'provider': 'S3',
    's3_bucket_name': 'super-awesome-bucket',
    's3_access_key_id': 'AKIAIOSFODNN7EXAMPLE',
    's3_secret_access_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYzEXAMPLEKEY',
}

TEST_WEBHOOK = {
    'url': 'https://wow.such.io/view-api-callback',
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
        response._content = json.dumps(TEST_DOCUMENT)
        mock_request.return_value = response

        result = self.api.create_document(url=TEST_URL,
                                          name='Test Document',
                                          thumbnails='100x100,200x200',
                                          non_svg=False)
        self.assertIsNotNone(result)
        self.assertEqual(result, TEST_DOCUMENT)

        data = {
            'url': TEST_URL,
            'name': 'Test Document',
            'thumbnails': '100x100,200x200',
            'non_svg': False,
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
        response._content = json.dumps(TEST_DOCUMENT)
        mock_request.return_value = response

        stream = six.BytesIO()
        result = self.api.create_document_from_file(stream,
                                                    name='Test Document')
        self.assertEqual(result, TEST_DOCUMENT)

        result = self.api.create_document_from_file(__file__,
                                                    name='Test Document')
        self.assertEqual(result, TEST_DOCUMENT)

    @patch.object(Session, 'request')
    def test_get_document(self, mock_request):
        response = Response()
        response.status_code = 200
        response._content = json.dumps(TEST_DOCUMENT)
        mock_request.return_value = response

        result = self.api.get_document(TEST_DOCUMENT['id'])
        self.assertIsNotNone(result)
        self.assertEqual(result, TEST_DOCUMENT)

    @patch.object(Session, 'request')
    def test_get_documents(self, mock_request):
        response = Response()
        response.status_code = 200
        response._content = json.dumps(TEST_DOCUMENT_LIST)
        mock_request.return_value = response

        now = datetime.datetime.utcnow()
        result = self.api.get_documents(limit=10, created_before=now)
        self.assertIsNotNone(result)
        self.assertEqual(result, TEST_DOCUMENT_LIST)

    @patch.object(Session, 'request')
    def test_update_document(self, mock_request):
        response = Response()
        response.status_code = 200
        response._content = json.dumps(TEST_DOCUMENT)
        mock_request.return_value = response

        result = self.api.update_document(TEST_DOCUMENT['id'],
                                          name='TestDocument')
        self.assertIsNotNone(result)
        self.assertEqual(result, TEST_DOCUMENT)

    @patch.object(Session, 'request')
    def test_delete_document(self, mock_request):
        response = Response()
        response.status_code = 204
        mock_request.return_value = response

        self.api.delete_document(TEST_DOCUMENT['id'])

    @patch.object(Session, 'request')
    def test_get_document_content(self, mock_request):
        response = Response()
        response.status_code = 200
        response.headers['Content-Type'] = 'text/plain'
        response._content = 'test'
        response.raw = six.BytesIO('test')
        mock_request.return_value = response

        stream = six.BytesIO()
        mimetype = self.api.get_document_content(stream, TEST_DOCUMENT['id'])
        self.assertEqual(stream.getvalue(), response._content)
        self.assertEqual(mimetype, response.headers['Content-Type'])

        stream = six.BytesIO()
        self.api.get_document_content(stream,
                                      TEST_DOCUMENT['id'],
                                      extension='.pdf')
        self.assertEqual(stream.getvalue(), response._content)

        stream = six.BytesIO()
        self.api.get_document_content(stream,
                                      TEST_DOCUMENT['id'],
                                      extension='.zip')
        self.assertEqual(stream.getvalue(), response._content)

        stream = six.BytesIO()
        # allowed only .zip and .pdf extensions
        self.assertRaises(ValueError,
                          self.api.get_document_content,
                          stream,
                          TEST_DOCUMENT['id'],
                          extension='.docx')

    @patch.object(Session, 'request')
    def test_get_document_content_to_string(self, mock_request):
        response = Response()
        response.status_code = 200
        response.headers['Content-Type'] = 'text/plain'
        response._content = 'test'
        response.raw = six.BytesIO('test')
        mock_request.return_value = response

        doc_id = TEST_DOCUMENT['id']
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
                                                         TEST_DOCUMENT['id'])
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

        mimetype = self.api.get_document_content_mimetype(TEST_DOCUMENT['id'])
        self.assertEqual(mimetype, response.headers['Content-Type'])

    @patch.object(Session, 'request')
    def test_create_session(self, mock_request):
        response = Response()
        response.status_code = 201
        response._content = json.dumps(TEST_SESSION)
        mock_request.return_value = response

        expires_at = datetime.datetime.utcnow()
        doc_id = TEST_DOCUMENT['id']
        result = self.api.create_session(doc_id,
                                         duration=600,
                                         expires_at=expires_at,
                                         is_downloadable=True,
                                         is_text_selectable=True)
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], TEST_SESSION['id'])

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
        response._content = json.dumps(TEST_DOCUMENT)
        mock_request.return_value = response

        result = self.api.ready_to_view(TEST_DOCUMENT['id'])
        self.assertIsNotNone(result)
        self.assertTrue(bool(result))

        response._content = json.dumps(dict(TEST_DOCUMENT, status='error'))

        result = self.api.ready_to_view(TEST_DOCUMENT['id'])
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
                          TEST_DOCUMENT['id'])

    @patch.object(Session, 'request')
    def test_request_retry_after(self, mock_request):
        response = Response()
        response.status_code = 202
        response.headers['Retry-After'] = '100.0'
        mock_request.return_value = response

        try:
            self.api.get_thumbnail_to_string(TEST_DOCUMENT['id'], 100, 100)
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
        mimetype = self.api.get_thumbnail(stream, TEST_DOCUMENT['id'], 100, 100)
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

        doc_id = TEST_DOCUMENT['id']
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
                                                  TEST_DOCUMENT['id'],
                                                  100, 100)
        self.assertEqual(mimetype, response.headers['Content-Type'])
        self.assertTrue(os.path.exists(filename))
        try:
            os.remove(filename)
        except OSError:
            pass

    @patch.object(Session, 'request')
    def test_create_storage_profile(self, mock_request):
        response = Response()
        response.status_code = 201
        response._content = json.dumps(TEST_STORAGE_PROFILE)
        mock_request.return_value = response

        result = self.api.create_storage_profile(
            'S3', 'bucket', 'key_id', 'secret_key')
        self.assertIsNotNone(result)
        self.assertEqual(result, TEST_STORAGE_PROFILE)

    @patch.object(Session, 'request')
    def test_get_storage_profile(self, mock_request):
        response = Response()
        response.status_code = 200
        response._content = json.dumps(TEST_STORAGE_PROFILE)
        mock_request.return_value = response

        result = self.api.get_storage_profile()
        self.assertIsNotNone(result)
        self.assertEqual(result, TEST_STORAGE_PROFILE)

    @patch.object(Session, 'request')
    def test_delete_storage_profile(self, mock_request):
        response = Response()
        response.status_code = 204
        mock_request.return_value = response

        self.api.delete_storage_profile()

    @patch.object(Session, 'request')
    def test_create_webhook(self, mock_request):
        response = Response()
        response.status_code = 201
        response._content = json.dumps(TEST_WEBHOOK)
        mock_request.return_value = response

        result = self.api.create_webhook('http://example.com/webhook')
        self.assertIsNotNone(result)
        self.assertEqual(result, TEST_WEBHOOK)

    @patch.object(Session, 'request')
    def test_get_webhook(self, mock_request):
        response = Response()
        response.status_code = 200
        response._content = json.dumps(TEST_WEBHOOK)
        mock_request.return_value = response

        result = self.api.get_webhook()
        self.assertIsNotNone(result)
        self.assertEqual(result, TEST_WEBHOOK)

    @patch.object(Session, 'request')
    def test_delete_webhook(self, mock_request):
        response = Response()
        response.status_code = 204
        mock_request.return_value = response

        self.api.delete_webhook()


if __name__ == '__main__':
    unittest.main()
