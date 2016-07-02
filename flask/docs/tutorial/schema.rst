.. _tutorial-schema:

Step 1: Database Schema
=======================

First, we want to create the database schema. Only a single table is needed
for this application and we only want to support SQLite, so creating the
database schema is quite easy. Just put the following contents into a file
named `schema.sql` in the just created `flaskr` folder:

.. sourcecode:: sql

    drop table if exists entries;
    create table entries (
      id integer primary key autoincrement,
      title text not null,
      'text' text not null
    );

This schema consists of a single table called ``entries``. Each row in
this table has an ``id``, a ``title``, and a ``text``.  The ``id`` is an
automatically incrementing integer and a primary key, the other two are
strings that must not be null.

Continue with :ref:`tutorial-setup`.
