#!/usr/bin/env python3
"""
Dirwatcher - A long-running program
"""

__author__ = "Robert Havelaar"

import sys
import os
import argparse
import signal
import logging
import time
import datetime

start_time = time.time()
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s:%(msecs)d  %(name)s  %(levelname)s \
%(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)
starting_banner = '\n' + '-' * 80 + '\n' + \
    f'\n\t{__name__} started at {time.ctime()}' +\
    '\n\n' + '-' * 80 + '\n'

exit_flag = False
previous_files = {}


def search_for_magic(file_dict, magic_string):
    '''Searches a dictionary of files for a magic string
        logging only once when the magic string is found'''
    for k, v in previous_files.items():
        with open(k) as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if i >= v:
                if magic_string in line:
                    logger.info(
                        f'Magic string: {magic_string} \
found in {k} at line {i+1}')
                previous_files[k] += 1
    return


def check_added_files(old_file_dict, new_file_dict):
    '''Returns a list of newly added files'''
    new_files = []
    for f in new_file_dict.keys():
        if f not in old_file_dict:
            new_files.append(f)
    return new_files


def check_deleted_files(old_file_dict, new_file_dict):
    '''Retruns a list of deleted files'''
    deleted_files = []
    for f in old_file_dict.keys():
        if f not in new_file_dict:
            deleted_files.append(f)
    return deleted_files


def search_for_files(path, extension):
    '''Returns a dictionary of files with the designated extension'''
    files_dict = {}
    for f in os.listdir(path):
        if not extension and os.path.join(path, f) not in files_dict:
            files_dict[os.path.join(path, f)] = 0
        elif os.path.splitext(f)[1][1:] == extension\
                and os.path.join(path, f) not in files_dict:
            files_dict[os.path.join(path, f)] = 0
    return files_dict


def watch_directory(path, magic_string, extension):
    '''Call check add and delete func for files in a given path
    and calls search string func'''
    global previous_files
    file_dict = search_for_files(os.path.abspath(path), extension)
    added_files = check_added_files(previous_files, file_dict)
    for f in added_files:
        logger.info(f'File {f} added')
        previous_files[f] = 0
    deleted_files = check_deleted_files(previous_files, file_dict)
    for f in deleted_files:
        logger.info(f'File {f} deleted')
        del previous_files[f]
    search_for_magic(previous_files, magic_string)
    return


def create_parser():
    '''Creates a command line parser with 4 argument definitions'''
    parser = argparse.ArgumentParser(
        description='Monitors "magic text" in a given directory')
    parser.add_argument(
        'magic_text', help='Text to search for in specified directory')
    parser.add_argument('-d', '--dir',
                        help='Directory to search for\'magic text\'',
                        required=True)
    parser.add_argument('-e', '--extension', default='txt',
                        help='Filters specific type of files to search')
    parser.add_argument('-p', '--polling_time', default=1.0,
                        help='Polling interval in seconds', type=float)
    return parser


def signal_handler(sig_num, frame):
    logger.warning(f'Received {signal.Signals(sig_num).name}')
    logger.info('\n' + '-' * 80 + '\n' + '\tStopped dirwatcher.py'
                f'\n\tUptime was\
    {datetime.timedelta(seconds=(time.time() - start_time))}' +
                '\n\n' + '-' * 80 + '\n')
    raise SystemExit()
    return


def main(args):
    parser = create_parser()
    if not args:
        parser.print_usage()
        sys.exit(1)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    ns = parser.parse_args(args)
    logger.info(starting_banner)
    while not exit_flag:
        try:
            watch_directory(ns.dir, ns.magic_text,
                            ns.extension)
        except Exception:
            global previous_files
            deleted_files = check_deleted_files(previous_files, {})
            for f in deleted_files:
                logger.info(f'File {f} deleted')
                del previous_files[f]
            logger.error(f'Directory {ns.dir} does not exist')
        time.sleep(ns.polling_time)
    return


if __name__ == '__main__':
    main(sys.argv[1:])
