python-boxview
==============

Python client library for [Box View API](https://box-view.readme.io/)

Installation
------------
The easiest way to install the latest version
is by using pip/easy_install to pull it from PyPI:

    pip install python-boxview

You may also use Git to clone the repository from
Github and install it manually:

    git clone https://github.com/caxap/python-boxview.git
    python setup.py install

Authentication
--------------
Box View API uses token-based authentication. You need create application and generate api token at [Box Developes Portal](https://app.box.com/developers/services). Then use the token to create instance of BoxView: 

```python
from boxview import boxview

api = boxview.BoxView('<your box view api key>')
```

Alternatively, token can be set by environment variable `BOX_VIEW_API_KEY`.

Usage
-----
python-boxview supports all methods from Box View API. List of methods and parameters description can be found [here](https://box-view.readme.io/)
```python
import os
from boxview import boxview

api = boxview.BoxView('<your box view api key>')

# upload file to create new document
doc = api.create_document(file='python-boxview.pdf', name='python-boxview')

# create new document from public url
doc = api.create_document(url='https://cloud.box.com/shared/static/4qhegqxubg8ox0uj5ys8.pdf')

doc_id = doc['id']

# retrieve existings document
doc1 = api.get_document(doc_id)

# list all uploaded documents for your api key
all_docs = api.get_documents(limit=10)

# update name of existing document
doc1 = api.update_document(doc_id, name='python-boxview')

# check that document ready to view
bool(api.ready_to_view(doc_id))

# start view session for document
session = api.create_session(doc_id, duration=300)

ses_id = session['id']

# get link to box viewer
api.get_session_url(ses_id)

# retrieve original document content to string 
content, mimetype = api.get_document_content_to_string(doc_id)
len(content)

# retrieve pdf version of document to file
api.get_document_content_to_file('python-boxview.pdf', doc_id, extension='.pdf')
os.path.exists('python-boxview.pdf')

# retrieve mimetype of original document content
mimetype = api.get_document_content_mimetype(doc_id)

# create webhook
api.create_webhook('http://example.com/my-webhook')

# create S3 storage profile
api.create_storage_profile('S3', 'super-awesome-bucket', 'AKIAIOSFODNN7EXAMPLE', 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYzEXAMPLEKEY')

# and delete document
api.delete_document(doc_id)
```

Dealing with Rate Limiting
--------------------------
```python
import time
from boxview import boxview

api = boxview.BoxView('<your box view api key>')

document_id = '2da6cf9261824fb0a4fe532f94d14625'
retry, max_retry = 0, 3
while True:
    try:
        api.get_thumbnail_to_file('thumbnail_100x100.png', document_id, 100, 100)
        break  # ok, thumbnail saved
    except boxview.RetryAfter as e:
        retry += 1
        if retry <= max_retry:
            time.sleep(e.seconds) # waiting for next call
        else:
            raise  # failed after `max_retry` attempts, exit with exception

```

License
-------

The MIT License (MIT)

Contributed by [Maxim Kamenkov](https://github.com/caxap/), [PandaDoc.com](http://pandadoc.com/)
