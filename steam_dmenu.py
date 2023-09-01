#!/usr/bin/env python

import argparse
import sys
import vdf
from os import chmod
from os import stat as os_stat
from os.path import expanduser, isdir, isfile
import stat
from subprocess import Popen, PIPE

# For larger libraries
app_name_cache: dict[int, str] = {}

# Configurable

# Blocked AppIds, like tools
# If not given as argument, the default is used, else the provided one
blocked_appids: list[int] = []


def default_blocked_appids() -> list[int]:
    # Steamworks
    blocked_appids = [228980]
    # Proton
    blocked_appids += [2348590, 1887720, 858280, 961940, 1054830, 1113280, 1245040, 1493710, 1580130]
    # Steam Linux Runtime
    blocked_appids += [1070560]
    # Steam Linux Runtime - Soldier
    blocked_appids += [1391110]
    # Steam Linux Runtime - Sniper
    blocked_appids += [1628350]
    # Proton EasyAntiCheat Runtime
    blocked_appids += [1826330]
    return blocked_appids


def main() -> None:
    global blocked_appids

    args = parse_arguments()

    library = get_libraryfolders_vdf(args.library)

    if library is None:
        print('Path does not exist or does not contain the libraryfolder.vdf!')
    else:
        vdf_dict = get_vdf_dict(library)

        if args.blocked_appids is None:
            blocked_appids = default_blocked_appids()
        else:
            blocked_appids = args.blocked_appids.split(',')
            blocked_appids = [int(x) for x in blocked_appids]

        libraries = parse_libraries(vdf_dict)

        if 0 < args.mode:
            generate_start_scripts(args.output, args.launcher_prefix)

        if 0 == args.mode or 2 == args.mode:
            start_steam_dmenu(libraries, args.dmenu, args.launcher_prefix)


def generate_start_scripts(gen_path: str, dmenu_prefix: str, use_block_list: bool = True) -> None:
    global app_name_cache, blocked_appids

    if isdir(gen_path):
        base_path = to_full_userpath(gen_path)

        for appid in app_name_cache:
            if use_block_list and (appid in blocked_appids):
                continue

            script_path = '{}/{}{}'.format(base_path, dmenu_prefix, app_name_cache[appid])

            script_file = open(script_path, 'w')
            command = '#!/bin/bash\nsteam steam://rungameid/{:d}\n'.format(appid)
            script_file.write(command)
            script_file.close()

            # Make script executable
            st = os_stat(script_path)
            chmod(script_path, st.st_mode | stat.S_IEXEC)
    else:
        print('Path does not exist or is not a directory!')


def start_steam_dmenu(libraries: dict, args_dmenu: str, dmenu_prefix: str) -> None:
    apps = parse_apps_for_dmenu(libraries, dmenu_prefix)
    dmenu = to_full_userpath(args_dmenu)

    returncode, stdout = open_dmenu(dmenu, apps)
    appid = stdout.decode().split(':')[0]

    if returncode == 1 or not appid or not appid.isdigit():
        sys.exit()
    launch_game(appid)


# Utility functions

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Launch installed Steam games using dmenu'
    )
    parser.add_argument(
        '--dmenu',
        '-d',
        dest='dmenu',
        default='dmenu -i',
        help='Custom dmenu command (default is \'dmenu -i\')'
    )
    parser.add_argument(
        '--mode',
        '-m',
        dest='mode',
        default=0,
        type=int,
        choices=range(0, 3),
        help='If it should just launch and/or generate scripts (default is 0, just launching)'
    )
    parser.add_argument(
        '--library',
        '-l',
        dest='library',
        default='~/.local/share/Steam/steamapps/libraryfolders.vdf',
        help='libraryfolder.vdf location'
    )
    parser.add_argument(
        '--blocked'
        '-b',
        dest='blocked_appids',
        nargs='*',
        help='Blocked AppId\'s, such as tools like Proton'
    )
    parser.add_argument(
        '--prefix'
        '-p',
        dest='launcher_prefix',
        default='play ',
        help='Prefix to be used in dmenu (play Team Fortress 2)'
    )
    parser.add_argument(
        '--output',
        '-o',
        dest='output',
        help='Path to generate the script for showing entries in your dmenu'
    )
    parsed_args = parser.parse_args()

    return parsed_args


def get_libraryfolders_vdf(library_arg: str) -> str or None:
    if isfile(library_arg):
        return library_arg
    elif isdir(library_arg):
        library = '{}/libraryfolders.vdf'.format(library_arg)

        if isfile(library):
            return library

        library = '{}/steamapps'.format(library_arg)

        if isdir(library):
            library = '{}/libraryfolders.vdf'.format(library)

            if isfile(library):
                return library
    return None


def parse_apps_for_dmenu(libraries: dict, dmenu_prefix: str, use_block_list: bool = True) -> str:
    global blocked_appids

    apps: list[str] = []

    for lib_id in libraries:
        for appid in libraries[lib_id]['apps']:
            app_name = libraries[lib_id]['apps'][appid]

            if use_block_list and (appid in blocked_appids):
                continue

            app = '{}{:d}: {}'.format(dmenu_prefix, appid, app_name)
            apps.append(app)
    return '\n'.join(apps)


def parse_libraries(lib_dict: vdf.VDFDict) -> dict:
    if type(lib_dict) is not vdf.VDFDict:
        lib_dict = vdf_dict_to_dict(lib_dict)

    libraries = dict()

    for lib_key in lib_dict['libraryfolders'].keys():
        library = dict()

        if isdir(lib_dict['libraryfolders'][lib_key]['path']):
            library['path'] = lib_dict['libraryfolders'][lib_key]['path']
        else:
            continue

        apps = dict()

        for appid in lib_dict['libraryfolders'][lib_key]['apps'].keys():
            appid = int(appid)
            app_name = appid_to_app_name(library['path'], appid)
            apps[appid] = app_name
        library['apps'] = apps
        libraries[lib_key] = library
    return libraries


def appid_to_app_name(library_path: str, appid: int) -> str:
    global app_name_cache

    if app_name_cache.get(appid) is None:
        app_manifest = '{}/steamapps/appmanifest_{:d}.acf'.format(library_path, appid)
        app_manifest = vdf_dict_to_dict(get_vdf_dict(app_manifest))

        app_name = app_manifest['AppState']['name']
        app_name = app_name.encode("ascii", errors="ignore").decode()
        app_name_cache[appid] = app_name
        return app_name
    else:
        return app_name_cache[appid]


def get_vdf_dict(file_path: str) -> vdf.VDFDict:
    file_path = to_full_userpath(file_path)
    d = vdf.load(open(file_path, 'r'), mapper=vdf.VDFDict)
    return d


def vdf_dict_to_dict(vdf_dict: vdf.VDFDict) -> dict:
    vdf_text = vdf.dumps(vdf_dict, pretty=True)
    return vdf.loads(vdf_text)


def dict_to_vdf_dict(vdf_dict: dict) -> vdf.VDFDict:
    vdf_text = vdf.dumps(vdf_dict, pretty=True)
    return vdf.loads(vdf_text, mapper=vdf.VDFDict)


def to_full_userpath(prefixed_path: str) -> str:
    return prefixed_path.replace('$HOME', '~').replace('~', expanduser('~'))


def launch_game(appid: int) -> None:
    Popen(['xdg-open', 'steam://run/{}'.format(appid)])


def open_dmenu(dmenu: str, apps: str) -> tuple[int, bytes]:
    dmenu = Popen(
        dmenu.split(),
        stdin=PIPE,
        stdout=PIPE
    )
    (stdout, _) = dmenu.communicate(input=apps.encode('UTF-8'))
    return dmenu.returncode, stdout


if __name__ == "__main__":
    main()
