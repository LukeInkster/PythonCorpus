#!/bin/bash
# This script will prepare NetBox to run after the code has been upgraded to
# its most recent release.
#
# Once the script completes, remember to restart the WSGI service (e.g.
# gunicorn or uWSGI).

# Optionally use sudo if not already root, and always prompt for password
# before running the command
PREFIX="sudo -k "
if [ "$(whoami)" = "root" ]; then
	# When running upgrade as root, ask user to confirm if they wish to
	# continue
	read -n1 -rsp $'Running NetBox upgrade as root, press any key to continue or ^C to cancel\n'
	PREFIX=""
fi

# Install any new Python packages
COMMAND="${PREFIX}pip install -r requirements.txt --upgrade"
echo "Updating required Python packages ($COMMAND)..."
eval $COMMAND

# Apply any database migrations
./netbox/manage.py migrate

# Collect static files
./netbox/manage.py collectstatic --noinput
