.. _tutorial-dbinit:

Step 4: Creating The Database
=============================

As outlined earlier, Flaskr is a database powered application, and more
precisely, it is an application powered by a relational database system.  Such
systems need a schema that tells them how to store that information.
Before starting the server for the first time, it's important to create
that schema.

Such a schema can be created by piping the ``schema.sql`` file into the
`sqlite3` command as follows::

    sqlite3 /tmp/flaskr.db < schema.sql

The downside of this is that it requires the ``sqlite3`` command to be
installed, which is not necessarily the case on every system.  This also
requires that we provide the path to the database, which can introduce
errors.  It's a good idea to add a function that initializes the database
for you to the application.

To do this, we can create a function and hook it into the :command:`flask`
command that initializes the database.  Let me show you the code first.  Just
add this function below the `connect_db` function in :file:`flaskr.py`::

    def init_db():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

    @app.cli.command('initdb')
    def initdb_command():
        """Initializes the database."""
        init_db()
        print 'Initialized the database.'

The ``app.cli.command()`` decorator registers a new command with the
:command:`flask` script.  When the command executes, Flask will automatically
create an application context for us bound to the right application.
Within the function, we can then access :attr:`flask.g` and other things as
we would expect.  When the script ends, the application context tears down
and the database connection is released.

We want to keep an actual function around that initializes the database,
though, so that we can easily create databases in unit tests later on.  (For
more information see :ref:`testing`.)

The :func:`~flask.Flask.open_resource` method of the application object
is a convenient helper function that will open a resource that the
application provides.  This function opens a file from the resource
location (your ``flaskr`` folder) and allows you to read from it.  We are
using this here to execute a script on the database connection.

The connection object provided by SQLite can give us a cursor object.
On that cursor, there is a method to execute a complete script.  Finally, we
only have to commit the changes.  SQLite3 and other transactional
databases will not commit unless you explicitly tell it to.

Now, it is possible to create a database with the :command:`flask` script::

    flask initdb
    Initialized the database.

.. admonition:: Troubleshooting

   If you get an exception later on stating that a table cannot be found, check
   that you did execute the ``initdb`` command and that your table names are
   correct (singular vs. plural, for example).

Continue with :ref:`tutorial-views`
