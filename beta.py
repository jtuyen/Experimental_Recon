import argparse
import json
import ansible_runner
import digitalocean
from colorama import Fore, Back, Style
import emoji
import random
import time

ip_address_list = []
droplet_ids_list = []

parser = argparse.ArgumentParser(description='z2sec Recon')
# group = parser.add_mutually_exclusive_group(required=True)
parser.add_argument('-n', '--name', action='store', dest='instance_name', help='define name for instance(s)' )
# group.add_argument('-n', '--name', action='store', dest='instance_name', help='define name for instance(s)' )
parser.add_argument('-i', '--instances', action='store', dest='number_of_instances', type=int, default=1, help='define number of instance(s) to spin up')
# group.add_argument('-i', '--instances', action='store', dest='number_of_instances', type=int, default=1, help='define number of instance(s) to spin up')
parser.add_argument('-u', '--update', action='store_true', default=False, dest='instance_update', help='update all instances')
parser.add_argument('-d', '--domain', action='store', dest='target_domain', help='define target domain name')
parser.add_argument('--initial', action='store_true', dest='initial_image', default=False, help='create initial image for replication')
parser.add_argument('-m', '--module', choices=['ffuf', 'paramspider'], help='run specific module')
parser.add_argument('-x', '--nuke', action='store_true', dest='delete_all', default=False, help='delete all instances')
parser.add_argument('-c', '--current', action='store_true', dest='show_all_instances', default=False, help='list all instances on DigitalOcean')
parser.add_argument('--ip', action='store_true', dest='show_all_ip_addresses', default=False, help='list all IP addresses on DigitalOcean')

args = parser.parse_args()

# Read Digital Ocean settings file and save into global parameters
with open('./json/digitalocean.json') as f:
    do_settings = json.load(f)
    do_region = do_settings['digitalocean']['region']
    do_size = do_settings['digitalocean']['size']
    do_base_image = do_settings['digitalocean']['base_image']
    do_api_key = do_settings['digitalocean']['api_key']

# Load SSH keys from Digital Ocean
manager = digitalocean.Manager(token = do_api_key)
keys = manager.get_all_sshkeys()

def initial_snapshot():
    print (emoji.emojize(Fore.RED + ':red_circle: Creating droplet base image...' + Style.RESET_ALL))
    droplet = digitalocean.Droplet(token = do_api_key, name = (args.instance_name + str(random.randint(0,9999))), image = do_base_image, region = do_region, size_slug = do_size, ssh_keys = keys)
    droplet.create()
    countdown = 120
    while countdown > 0:
        print (emoji.emojize(Fore.YELLOW + ':yellow_circle: Waiting ' + str(countdown) + ' seconds...' + Style.RESET_ALL), end='\r')
        countdown -= 1
        time.sleep(1)
    actions = droplet.get_actions()
    for action in actions:
        action.load()
        print (emoji.emojize(Fore.GREEN + ':green_circle: Droplet is now ' + action.status + '...' + Style.RESET_ALL))
    start_initial_playbook()
    print (emoji.emojize(Fore.GREEN + ':green_circle: Taking snapshot of droplet...'))
    droplet.take_snapshot(snapshot_name = (args.instance_name + "-automation"))
    countdown = 480
    while countdown > 0:
        print (emoji.emojize(Fore.YELLOW + ':yellow_circle: Waiting ' + str(countdown) + ' seconds...' + Style.RESET_ALL), end='\r')
        countdown -= 1
        time.sleep(1)
    print (emoji.emojize(Fore.GREEN + ':green_circle: Snapshot of base image is now completed...'))
    droplet.destroy()
    print (emoji.emojize(Fore.GREEN + ':green_circle: Base image has been destroyed...'))
    print (emoji.emojize(Fore.GREEN + ':green_circle: Initialization process has been completed...'))

def list_ip_addresses():
    droplet = digitalocean.Manager(token = do_api_key)
    get_info = droplet.get_all_droplets()
    for item in get_info:
        ip_address_list.append(item.ip_address)
    print (ip_address_list)

def list_droplet_ids():
    droplet = digitalocean.Manager(token = do_api_key)
    get_info = droplet.get_all_droplets()
    for item in get_info:
        droplet_ids_list.append(item.id)
    print (droplet_ids_list)

def update_ansible_hosts():
    with open('./inventory/hosts','w+') as hosts_file:
        # write default ansible configuration settings.
        # spacing is very important in the next lines of code
        hosts_file.write('''all:
  vars:
    ansible_python_interpreter: /usr/bin/python3
    ansible_ssh_extra_args: -o StrictHostKeyChecking=no
  hosts:\n''')
        list_ip_addresses()
        for item in ip_address_list:
            hosts_file.write('    ' + item + ':\n')

def delete_all():
    print (emoji.emojize(Fore.RED + ':red_circle: Deleting all droplets...' + Style.RESET_ALL))
    if list_droplet_ids() == []:
        print (emoji.emojize(Fore.GREEN + ':green_circle: No droplets found...' + Style.RESET_ALL))
    else:
        for item in droplet_ids_list:
            droplet = digitalocean.Droplet(token = do_api_key, id = item)
            print(emoji.emojize(Fore.RED + ':red_circle: Deleting Droplet ID: ' + str(item) + '...' + Style.RESET_ALL))
            droplet.destroy()
        print(emoji.emojize(Fore.GREEN + ':green_circle: All Droplets has been deleted...'))

def start_initial_playbook():
    update_ansible_hosts()
    time.sleep(10)
    ansible_run_playbook = ansible_runner.run(private_data_dir = './', host_pattern = 'hosts', playbook = 'setup_instances.yml')

def create_instances():
    do_manager = digitalocean.Manager(token = do_api_key)
    do_snapshot_id = do_manager.get_all_snapshots()
    instances = args.number_of_instances
    while instances > 0:
        droplet = digitalocean.Droplet(token = do_api_key, name = (args.instance_name + str(random.randint(0,9999))), image = str(do_snapshot_id[0].id), region = do_region, size_slug = do_size, ssh_keys = keys)
        droplet.create()
        actions = droplet.get_actions()
        for action in actions:
            action.load()
            print (emoji.emojize(Fore.GREEN + ':green_circle: Droplet #' + str(instances) + ' is now ' + action.status + '...' + Style.RESET_ALL)) 
        instances -= 1

def update_instances():
    print(emoji.emojize(Fore.RED + ':red_circle: Running playbook to update existing instances...' + Style.RESET_ALL))
    start_initial_playbook()
    print(emoji.emojize(Fore.GREEN + ':green_circle: Completed execution of playbook...' + Style.RESET_ALL))

if args.show_all_instances == True:
    list_droplet_ids()
elif args.delete_all == True:
    delete_all()
elif args.show_all_ip_addresses == True:
    list_ip_addresses()
elif args.initial_image == True:
    initial_snapshot()
elif args.number_of_instances >= 1:
    create_instances()
elif args.instance_update == True:
    update_instances()
else:
    print(emoji.emojize(Fore.RED + ':yellow_circle: No arguments has been provided...' + Style.RESET_ALL))