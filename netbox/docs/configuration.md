<h1>Configuration</h1>

NetBox's local configuration is held in `netbox/netbox/configuration.py`. An example configuration is provided at `netbox/netbox/configuration.example.py`. You may copy or rename the example configuration and make changes as appropriate. NetBox will not run without a configuration file.

[TOC]

# Mandatory Settings

---

#### ALLOWED_HOSTS

This is a list of valid fully-qualified domain names (FQDNs) for the NetBox server. NetBox will not permit write access to the server via any other hostnames. The first FQDN in the list will be treated as the preferred name.

Example:

```
ALLOWED_HOSTS = ['netbox.example.com', '192.0.2.123']
```

---

#### DATABASE

NetBox requires access to a PostgreSQL database service to store data. This service can run locally or on a remote system. The following parameters must be defined within the `DATABASE` dictionary:

* NAME - Database name
* USER - PostgreSQL username
* PASSWORD - PostgreSQL password
* HOST - Name or IP address of the database server (use `localhost` if running locally)
* PORT - TCP port of the PostgreSQL service; leave blank for default port (5432)

Example:

```
DATABASE = {
    'NAME': 'netbox',               # Database name
    'USER': 'netbox',               # PostgreSQL username
    'PASSWORD': 'J5brHrAXFLQSif0K', # PostgreSQL password
    'HOST': 'localhost',            # Database server
    'PORT': '',                     # Database port (leave blank for default)
}
```

---

#### SECRET_KEY

This is a secret cryptographic key is used to improve the security of cookies and password resets. The key defined here should not be shared outside of the configuration file. `SECRET_KEY` can be changed at any time, however be aware that doing so will invalidate all existing sessions.

Please note that this key is **not** used for hashing user passwords or for the encrypted storage of secret data in NetBox.

`SECRET_KEY` should be at least 50 characters in length and contain a random mix of letters, digits, and symbols. The script located at `netbox/generate_secret_key.py` may be used to generate a suitable key.

# Optional Settings

---

#### ADMINS

NetBox will email details about critical errors to the administrators listed here. This should be a list of (name, email) tuples. For example:

```
ADMINS = [
    ['Hank Hill', 'hhill@example.com'],
    ['Dale Gribble', 'dgribble@example.com'],
]
```

---

#### DEBUG

Default: False

This setting enables debugging. This should be done only during development or troubleshooting. Never enable debugging on a production system, as it can expose sensitive data to unauthenticated users. 

---

#### EMAIL

In order to send email, NetBox needs an email server configured. The following items can be defined within the `EMAIL` setting:

* SERVER - Host name or IP address of the email server (use `localhost` if running locally)
* PORT - TCP port to use for the connection (default: 25)
* USERNAME - Username with which to authenticate
* PASSSWORD - Password with which to authenticate
* TIMEOUT - Amount of time to wait for a connection (seconds)
* FROM_EMAIL - Sender address for emails sent by NetBox

---

#### LOGIN_REQUIRED

Default: False,

Setting this to True will permit only authenticated users to access any part of NetBox. By default, anonymous users are permitted to access most data in NetBox (excluding secrets) but not make any changes.

---

#### MAINTENANCE_MODE

Default: False

Setting this to True will display a "maintenance mode" banner at the top of every page.

---

#### NETBOX_USERNAME

#### NETBOX_PASSWORD

If provided, NetBox will use these credentials to authenticate against devices when collecting data.

---

#### PAGINATE_COUNT

Default: 50

Determine how many objects to display per page within each list of objects.

---

#### TIME_ZONE

Default: UTC

The time zone NetBox will use when dealing with dates and times. It is recommended to use UTC time unless you have a specific need to use a local time zone. [List of available time zones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

---

#### Date and Time Formatting

You may define custom formatting for date and times. For detailed instructions on writing format strings, please see [the Django documentation](https://docs.djangoproject.com/en/dev/ref/templates/builtins/#date).

Defaults:

```
DATE_FORMAT = 'N j, Y'               # June 26, 2016
SHORT_DATE_FORMAT = 'Y-m-d'          # 2016-06-27
TIME_FORMAT = 'g:i a'                # 1:23 p.m.
SHORT_TIME_FORMAT = 'H:i:s'          # 13:23:00
DATETIME_FORMAT = 'N j, Y g:i a'     # June 26, 2016 1:23 p.m.
SHORT_DATETIME_FORMAT = 'Y-m-d H:i'  # 2016-06-27 13:23
```
