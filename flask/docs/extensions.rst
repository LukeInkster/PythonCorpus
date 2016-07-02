.. _extensions:

Flask Extensions
================

Flask extensions extend the functionality of Flask in various different
ways.  For instance they add support for databases and other common tasks.

Finding Extensions
------------------

Flask extensions are listed on the `Flask Extension Registry`_ and can be
downloaded with :command:`easy_install` or :command:`pip`.  If you add a Flask extension
as dependency to your :file:`requirements.txt` or :file:`setup.py` file they are
usually installed with a simple command or when your application installs.

Using Extensions
----------------

Extensions typically have documentation that goes along that shows how to
use it.  There are no general rules in how extensions are supposed to
behave but they are imported from common locations.  If you have an
extension called ``Flask-Foo`` or ``Foo-Flask`` it should be always
importable from ``flask_foo``::

    import flask_foo

Building Extensions
-------------------

While `Flask Extension Registry`_ contains many Flask extensions, you may not find
an extension that fits your need. If this is the case, you can always create your own. 
Consider reading :ref:`extension-dev` to develop your own Flask extension.

Flask Before 0.8
----------------

If you are using Flask 0.7 or earlier the :data:`flask.ext` package will not
exist, instead you have to import from ``flaskext.foo`` or ``flask_foo``
depending on how the extension is distributed.  If you want to develop an
application that supports Flask 0.7 or earlier you should still import
from the :data:`flask.ext` package.  We provide you with a compatibility
module that provides this package for older versions of Flask.  You can
download it from GitHub: `flaskext_compat.py`_

And here is how you can use it::

    import flaskext_compat
    flaskext_compat.activate()

    from flask.ext import foo

Once the ``flaskext_compat`` module is activated the :data:`flask.ext` will
exist and you can start importing from there.


.. _Flask Extension Registry: http://flask.pocoo.org/extensions/
.. _flaskext_compat.py: https://raw.githubusercontent.com/pallets/flask/master/scripts/flaskext_compat.py
