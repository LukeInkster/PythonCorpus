from getpass import getpass
from ncclient.transport.errors import AuthenticationError
from paramiko import AuthenticationException

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from dcim.models import Device, Module, Site


class Command(BaseCommand):
    help = "Update inventory information for specified devices"
    username = settings.NETBOX_USERNAME
    password = settings.NETBOX_PASSWORD

    def add_arguments(self, parser):
        parser.add_argument('-u', '--username', dest='username', help="Specify the username to use")
        parser.add_argument('-p', '--password', action='store_true', default=False, help="Prompt for password to use")
        parser.add_argument('-s', '--site', dest='site', action='append',
                            help="Filter devices by site (include argument once per site)")
        parser.add_argument('-n', '--name', dest='name', help="Filter devices by name (regular expression)")
        parser.add_argument('--full', action='store_true', default=False, help="For inventory update for all devices")
        parser.add_argument('--fake', action='store_true', default=False, help="Do not actually update database")

    def handle(self, *args, **options):

        def create_modules(modules, parent=None):
            for module in modules:
                m = Module(device=device, parent=parent, name=module['name'], part_id=module['part_id'],
                           serial=module['serial'], discovered=True)
                m.save()
                create_modules(module.get('modules', []), parent=m)

        # Credentials
        if options['username']:
            self.username = options['username']
        if options['password']:
            self.password = getpass("Password: ")

        # Attempt to inventory only active devices
        device_list = Device.objects.filter(status=True)

        # --site: Include only devices belonging to specified site(s)
        if options['site']:
            sites = Site.objects.filter(slug__in=options['site'])
            if sites:
                site_names = [s.name for s in sites]
                self.stdout.write("Running inventory for these sites: {}".format(', '.join(site_names)))
            else:
                raise CommandError("One or more sites specified but none found.")
            device_list = device_list.filter(rack__site__in=sites)

        # --name: Filter devices by name matching a regex
        if options['name']:
            device_list = device_list.filter(name__iregex=options['name'])

        # --full: Gather inventory data for *all* devices
        if options['full']:
            self.stdout.write("WARNING: Running inventory for all devices! Prior data will be overwritten. (--full)")

        # --fake: Gathering data but not updating the database
        if options['fake']:
            self.stdout.write("WARNING: Inventory data will not be saved! (--fake)")

        device_count = device_list.count()
        self.stdout.write("** Found {} devices...".format(device_count))

        for i, device in enumerate(device_list, start=1):

            self.stdout.write("[{}/{}] {}: ".format(i, device_count, device.name), ending='')

            # Skip inactive devices
            if not device.status:
                self.stdout.write("Skipped (inactive)")
                continue

            # Skip devices without primary_ip set
            if not device.primary_ip:
                self.stdout.write("Skipped (no primary IP set)")
                continue

            # Skip devices which have already been inventoried if not doing a full update
            if device.serial and not options['full']:
                self.stdout.write("Skipped (Serial: {})".format(device.serial))
                continue

            RPC = device.get_rpc_client()
            if not RPC:
                self.stdout.write("Skipped (no RPC client available for platform {})".format(device.platform))
                continue

            # Connect to device and retrieve inventory info
            try:
                with RPC(device, self.username, self.password) as rpc_client:
                    inventory = rpc_client.get_inventory()
            except KeyboardInterrupt:
                raise
            except (AuthenticationError, AuthenticationException):
                self.stdout.write("Authentication error!")
                continue
            except Exception as e:
                self.stdout.write("Error: {}".format(e))
                continue

            if options['verbosity'] > 1:
                self.stdout.write("")
                self.stdout.write("\tSerial: {}".format(inventory['chassis']['serial']))
                self.stdout.write("\tDescription: {}".format(inventory['chassis']['description']))
                for module in inventory['modules']:
                    self.stdout.write("\tModule: {} / {} ({})".format(module['name'], module['part_id'],
                                                                      module['serial']))
            else:
                self.stdout.write("{} ({})".format(inventory['chassis']['description'], inventory['chassis']['serial']))

            if not options['fake']:
                with transaction.atomic():
                    # Update device serial
                    if device.serial != inventory['chassis']['serial']:
                        device.serial = inventory['chassis']['serial']
                        device.save()
                    Module.objects.filter(device=device, discovered=True).delete()
                    create_modules(inventory.get('modules', []))

        self.stdout.write("Finished!")
