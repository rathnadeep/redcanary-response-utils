#!/usr/bin/env python
"""
Requires a valid credentials.psc, the api credential file containing a Cb threathunter server URL and corresponding API token. 
API token should be in the format of TOKEN/ConnecterID.
"""
import argparse
import csv
import os
import sys
from datetime import datetime

# Local helpers
from common import *

# Carbon Black
from cbapi.psc.threathunter import CbThreatHunterAPI, Process, Event, Tree
from cbapi.errors import *
from solrq import Range, Value


if sys.version_info.major >= 3:
    _python3 = True
else:
    _python3 = False


def get_process_details(process):

    timestamp = (process.device_timestamp)
    hostname = process.device_name
    username = process.process_username
    path = process.process_name
    cmdline = process.process_cmdline

    try:
        process_hashes = process.process_hash
    except:
        process_hashes = ''

    return [timestamp,
            hostname,
            username,
            process.process_name,
            cmdline,
            process_hashes,
            process.childproc_count,
            process.filemod_count,
            process.modload_count,
            process.netconn_count,
            process.process_guid,
            process.parent_name
            ]


def process_search(cb_conn, query, query_base=None):
    if query_base != None:
        query += query_base

    query_result = cb_conn.select(Process).where(query)
    query_result_len = len(query_result)
    log_info('Total results: {0}'.format(query_result_len))

    results = []

    try:
        process_counter = 0
        for process in query_result:
            process_counter += 1
            if process_counter % 100 == 0:
                log_info('Processing {0} of {1}'.format(process_counter, query_result_len))

            results.append(get_process_details(process))
    except KeyboardInterrupt:
        log_info("Caught CTRL-C. Returning what we have . . .")

    return tuple(results)


def main():
    parser = build_cli_parser("Process utility")
    args = parser.parse_args()

    # BEGIN Common 
    if args.prefix:
        output_filename = '{0}-processes.csv'.format(args.prefix)
    else:
        output_filename = 'processes.csv'

    if args.append == True or args.queryfile is not None:
        file_mode = 'a'
    else:
        file_mode = 'w'

    if args.days:
        query_base = ' start:-{0}m'.format(args.days*1440)
    elif args.minutes:
        query_base = ' start:-{0}m'.format(args.minutes)
    else:
        query_base = ''

    if args.profile:
        cb = CbThreatHunterAPI(profile=args.profile)
    else:
        cb = CbThreatHunterAPI()

    queries = []
    if args.query:
        queries.append(args.query)
    elif args.queryfile:
        with open(args.queryfile, 'r') as f:
            for query in f.readlines():
                queries.append(query.strip())
        f.close()
    else:
        queries.append('')
    # END Common 

    output_file = open(output_filename, file_mode)
    writer = csv.writer(output_file)
    writer.writerow(["proc_timestamp",
                     "proc_hostname",
                     "proc_username",
                     "proc_path",
                     "proc_cmdline",
                     "proc_hashes",
                     "proc_child_count",
                     "proc_filemod_count",
                     "proc_modload_count",
                     "proc_netconn_count",
                     "proc_url",
                     "parent_name"
                     ])

    for query in queries:
        result_set = process_search(cb, query, query_base)

        for row in result_set:
            if _python3 == False:
                row = [col.encode('utf8') if isinstance(col, unicode) else col for col in row]
            writer.writerow(row)

    output_file.close()


if __name__ == '__main__':

    sys.exit(main())
