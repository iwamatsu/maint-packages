#!/usr/bin/env python3

# apt-get install python3-git python3-docopt git-buildpackage

import os
import json
from docopt import docopt

__doc__ = """{f}

Usage:
{f} <fname> [-v | --verbose] \
[-a | --add] \
[-c | --change] \
[-d | --delete] \
[-b | --build] \
[-p | --package <package_name>] \
[-s | --section <section_name>] \
[-r | --repo <debian_repo>] \
[-u | --upstream <upstream_repo>]
{f} -h | --help

Options:
    -a --add                        Add data 
    -c --change                     Change data
    -d --delete                     Delete data
    -b --build                      Build environment
    -s --section <SECTION_NAME>     Section name
    -p --package <PACKAGE_NAME>     Package name
    -r --repo <DEBIAN_REPO>         Debian repository
    -u --upstream <UPSTREAM_REPO>   Upstream repository
    -h --help                       Show this screen and exit.
""".format(f=__file__)

def arg_parse():
    set_data = {}

    args = docopt(__doc__)

    if args['--add'] and args['--change'] and args['--delete'] and args['--build']:
        return {}

    if args['--add']:
        set_data.setdefault("action", "add")
    elif args['--change']:
        set_data.setdefault("action", "change")
    elif args['--delete']:
        set_data.setdefault("action", "delete")
    elif args['--build']:
        set_data.setdefault("action", "build")
    else:
        return {}

    if args['<fname>']:
        set_data.setdefault("config_file", args['<fname>'])
    
    if args['--section']:
        set_data.setdefault("section", args['--section'][0])
    
    if args['--package']:
        set_data.setdefault("package", args['--package'][0])

    if args['--repo']:
        set_data.setdefault("debian_repo", args['--repo'][0])

    if args['--upstream']:
        set_data.setdefault("upstream_repo", args['--upstream'][0])

    return set_data

def build_world(base_dir, maint_data):
    import subprocess

    if os.path.isdir(base_dir) is False :
        os.makedirs(base_dir)

    os.chdir(base_dir)

    packages = maint_data['packages']
    for group in packages:
        for pkg in packages[group]:
            pj_dir = base_dir + '/' + group + '/' + pkg
            if os.path.isdir(pj_dir) is False:
                os.makedirs(pj_dir)

            os.chdir(pj_dir)
            print ("%s: %s" % (group, pkg))
    
            # debian repo
            try:
                deb_repo = packages[group][pkg]['debian-repo']
                cmd = "gbp clone --pristine-tar %s" % deb_repo
                subprocess.call(cmd.split())
            except:
                print ('No Debian repo.')
                continue
    
            # upstream
            try:
                upstream_repo = packages[group][pkg]['upstream-repo']
                # move to directory
                os.chdir(pkg)
                cmd = "git remote add upstream %s" % upstream_repo
                subprocess.call(cmd.split())
                cmd = "git remote update upstream"
                subprocess.call(cmd.split())
            except:
                print ('No upstream repo. tar ball only?')


if __name__ == '__main__':
    arg_result = arg_parse()

    if len(arg_result) == 0:
        exit()

    if "config_file" in arg_result:
        filename = arg_result['config_file']

    maint_data = {}
    with open(filename, 'r') as conf:
        maint_data = json.load(conf)

    base_dir = maint_data['config']['base_dir']
    user_name = maint_data['config']['user_name']
    user_email = maint_data['config']['user_email']

    if arg_result['action'] == 'build':
        build_world(base_dir, maint_data)
        exit()

    section = ""
    package_name = ""
    debian_repo = ""
    upstream_repo = ""
    package_data = {}

    if "section" in arg_result:
        section = arg_result["section"]

    if "package" in arg_result:
        package_name = arg_result["package"]

    if "debian_repo" in arg_result:
        debian_repo = arg_result['debian_repo']

    if 'upstream_repo' in arg_result:
        upstream_repo = arg_result['upstream_repo']

    # check section in data
    if 'packages' not in maint_data:
        maint_data['packages'] = {}

    if arg_result['action'] == 'delete':
        if len(package_name) == 0:
            exit()

        if len(section):
            packages_data = maint_data["packages"][section].pop(package_name)
        else:
            for __section in maint_data["packages"]:
                for __package_name in maint_data["packages"][__section]:
                    if __package_name == package_name:
                         maint_data["packages"][section].pop(package_name)

    elif arg_result['action'] == 'add':
        if len(section) == 0:
            section = "unknown"
        if len(package_name) == 0:
            exit()
        if len(debian_repo) == 0:
            exit()

        # check section in data
        if section not in maint_data["packages"]:
            maint_data["packages"][section] = {}

        if len(upstream_repo):
            d = {'debian-repo': debian_repo, 'upstream-repo': arg_result['upstream_repo']}
        else:
            d = {'debian-repo': debian_repo}

        maint_data["packages"][section][package_name] = d

    else: #update
        if len(package_name) == 0:
            exit()
        if len(debian_repo) == 0:
            exit()

        if len(section):
            packages_data = maint_data["packages"][section]
        else:
            for __section in maint_data["packages"]:
                for __package_name in maint_data["packages"][__section]:
                    if __package_name == package_name:
                         section = __section
                         packages_data = maint_data["packages"][section]

        package_data = packages_data[package_name]
        package_data['debian-repo'] = debian_repo
        if len(upstream_repo):
            package_data['upstream-repo'] = upstream_repo

    # save to file
    import shutil
    copy_filename = filename + ".old"
    shutil.copyfile(filename, copy_filename)

    __conf = open(filename, 'w')
    json.dump(maint_data, __conf, indent = 4) 
