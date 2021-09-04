# Web Recon using Digital Ocean and Ansible
The purpose of this repository is exploring the idea of scaling web reconnaisance using Digital Ocean and Ansible. In my case, I wanted something where I can distribute the load of bruteforcing of web directories at scale to finish as fast as possible and avoidance of IP being constantly blackholed. After diving into months of researching this idea, there are some limitations with Ansible that I've encountered and seemed clunkly for implementation especially with clobbering together a manual playbook file. There are better and more simplistic ways to perform effective recon without spinning up a full VPS instance such as using GitHub Actions or even experimental services such as serverless or lambada. However, this repository does show that scalability is possible using the `doctl` and `ansible-playbook` commands to automate deployment and command execution across instances.

## How does this Digital Ocean + Ansible stuff work
`doctl` interacts with Digital Ocean's API service which will send commands to add/remove instances. If running this script the very first time, it will create a droplet instance and start installation of web recon tools. When it's finished, it will perform a snapshot of the droplet and delete when it's ready. The reason is because we want a fresh image each time we run a command and creating a droplet directly from snapshots is a clean way to do it. When the instances are ready to be connected, the SSH information is pulled from the API and populated into Ansible's host inventory file. From there, `ansible-playbook` commands such as running `amass` or `massdns` can be issued to execute recon tasks at scale. How this works on Ansible side is the utilization of Ansible Roles functionality which can organize the playbooks in a project.

## Create initial snapshot
```
python3 beta.py --initial -n recon-snapshot
```

## View current digital ocean instances
```
python3 beta.py -c
```

## Delete all digital ocean instances
```
python3 beta.py -x
```