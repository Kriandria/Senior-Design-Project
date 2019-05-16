Flask Install
-------
Install and update using `pip`_:

.. code-block:: text

    pip install -U Flask


A Simple Example
----------------

.. code-block:: python

    from flask import Flask

    app = Flask(__name__)

    @app.route('/')
    def hello():
        return 'Hello, World!'

.. code-block:: text

    $ env FLASK_APP=hello.py flask run
     * Serving Flask app "hello"
     * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)




StUDy Break
======

Install
-------

**Be sure to use the same version of the code as the version of the docs
you're reading.** You probably want the latest tagged version, but the
default Git version is the master branch. ::

    # clone the repository
    $ git clone https://github.com/Kriandria/Senior-Design-Project
    $ cd Senior-Design-Project/Study\ Break

Create a virtualenv and activate it::

    $ python3 -m venv venv
    $ . venv/bin/activate

Or on Windows cmd::

    $ py -3 -m venv venv
    $ venv\Scripts\activate.bat

Run
---

::

    $ export FLASK_APP=studybreak
    $ export FLASK_ENV=development
    $ flask init-db
    $ flask run

Or on Windows cmd::

    > set FLASK_APP=studybreak
    > set FLASK_ENV=development
    > flask init-db
    > flask run

Open http://127.0.0.1:5000 in a browser.
