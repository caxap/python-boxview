#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import six
import datetime
import unittest
import simplejson as json
from mock import patch
from requests.models import Response
from requests.sessions import Session
from boxview import BoxView, BoxViewError
from boxview.boxview import format_date


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
    "type": "session",
    "id": "IyA4Ij8IzE_Wih20hML3ihxEOul1T4rxHLBtwa4IRg9m-FApz80OtEwst_RmnGq8SzJRsGaEU0UWSotJCW33KUeJ0Ah5uQ",
    "expires_at": "2013-09-11T19:52:09Z"
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

    @patch.object(Session, 'request')
    def test_crate_document(self, mock_request):
        response = Response()
        response.status_code = 201
        response._content = json.dumps(test_document)
        mock_request.return_value = response

        result = self.api.create_document(url=test_url, name='Test Document')
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], test_document['id'])

        # TODO: test for file param.

        # url of file param is required
        self.assertRaises(ValueError, self.api.create_document)

    @patch.object(Session, 'request')
    def test_create_document_from_url(self, mock_request):
        response = Response()
        response.status_code = 201
        response._content = json.dumps(test_document)
        mock_request.return_value = response

        result = self.api.create_document_from_url(url=test_url,
                                                   name='Test Document')
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], test_document['id'])

    @patch.object(Session, 'request')
    def test_create_document_from_file(self, mock_request):
        response = Response()
        response.status_code = 201
        response._content = json.dumps(test_document)
        mock_request.return_value = response

        self.assertRaises(NotImplementedError,
                          self.api.create_document_from_file,
                          file='',
                          name='Test Document')

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

        result = self.api.get_documents()
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
        response._content = 'test'
        response.raw = six.StringIO('test')
        mock_request.return_value = response

        stream = six.StringIO()
        self.api.get_document_content(stream, test_document['id'])
        self.assertEqual(stream.getvalue(), response._content)

        stream = six.StringIO()
        self.api.get_document_content(stream,
                                      test_document['id'],
                                      extension='.pdf')
        self.assertEqual(stream.getvalue(), response._content)

        stream = six.StringIO()
        self.api.get_document_content(stream,
                                      test_document['id'],
                                      extension='.zip')
        self.assertEqual(stream.getvalue(), response._content)

        stream = six.StringIO()
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
        response._content = 'test'
        response.raw = six.StringIO('test')
        mock_request.return_value = response

        result = self.api.get_document_content_to_string(test_document['id'])
        self.assertIsNotNone(result)
        self.assertEqual(result, response._content)

    @patch.object(Session, 'request')
    def test_get_document_content_to_file(self, mock_request):
        response = Response()
        response.status_code = 200
        response._content = 'test'
        response.raw = six.StringIO('test')
        mock_request.return_value = response

        filename = 'boxview.txt'
        self.api.get_document_content_to_file(filename, test_document['id'])

        self.assertTrue(os.path.exists(filename))
        try:
            os.remove(filename)
        except OSError:
            pass

    @patch.object(Session, 'request')
    def test_create_session(self, mock_request):
        response = Response()
        response.status_code = 201
        response._content = json.dumps(test_session)
        mock_request.return_value = response

        expires_at = datetime.datetime.utcnow()
        result = self.api.create_session(test_document['id'],
                                         duration=600,
                                         expires_at=expires_at)
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], test_session['id'])

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


if __name__ == '__main__':
    unittest.main()
