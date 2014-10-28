python-boxview
==============

Python client library for Box View API (http://developers.box.com/view/)

Installation
------------
The easiest way to install the latest version
is by using pip/easy_install to pull it from PyPI:

    pip install python-boxview

You may also use Git to clone the repository from
Github and install it manually:

    git clone https://github.com/caxap/python-boxview.git
    python setup.py install

Usage
-----
```python
import os
from boxview import boxview

token = '<your box view api key>'

api = boxview.BoxView(token)

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

# And delete document
api.delete_document(doc_id)
```

License
-------

The MIT License (MIT)

Contributed by [Maxim Kamenkov](https://github.com/caxap/), [PandaDoc.com](http://pandadoc.com/)
