 # Licensed to CRATE Technology GmbH ("Crate") under one or more contributor
 # license agreements.  See the NOTICE file distributed with this work for
 # additional information regarding copyright ownership.  Crate licenses
 # this file to you under the Apache License, Version 2.0 (the "License");
 # you may not use this file except in compliance with the License.  You may
 # obtain a copy of the License at
 #
 #   http://www.apache.org/licenses/LICENSE-2.0
 #
 # Unless required by applicable law or agreed to in writing, software
 # distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 # WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
 # License for the specific language governing permissions and limitations
 # under the License.
 #
 # However, if you have executed another commercial license agreement
 # with Crate these terms will supersede the license and you may use the
 # software solely pursuant to the terms of the relevant commercial agreement.


from __future__ import print_function
import json
import argparse
import httplib
import urllib
import uuid
import datetime
import sys


RESULT_TABLE_NAME = 'bench.results'

epoch = datetime.datetime.utcfromtimestamp(0)


def timestamp():
    return int((datetime.datetime.utcnow() - epoch).total_seconds() * 1000)


parser = argparse.ArgumentParser(description='Push-based insert benchmarking.')
parser.add_argument('payload', help='the payload file')
parser.add_argument('number_of_requests', type=int,
                    help='how many requests to make (number_of_requests * bulksize = nr of rows inserted)')
parser.add_argument('url', help='server address, use url:port')
parser.add_argument('--runs', type=int, default=1,
                    help='number of times to repeat the inserts')
parser.add_argument('--create', default='', help='path to create table script')
parser.add_argument('--drop', default='', help='path to drop table script')
parser.add_argument('--result-crate', default='',
                    help='url:port to Crate for saving results instead of STDOUT')


class SimpleCrate(object):

    def __init__(self, url):
        self.connection = httplib.HTTPConnection(url)
        self.headers = {"Content-type": "application/json"}

    def req(self, sql, bulk_args=None):
        obj = {"stmt": sql}
        if bulk_args:
            obj.update({"bulk_args": bulk_args})
        return self.req_raw(json.dumps(obj))

    def req_raw(self, payload):
        self.connection.request('POST', '/_sql', payload, self.headers)
        return self.connection.getresponse().read()

    def fetch_version(self):
        response = json.loads(
            self.req("select version['number'] from sys.nodes"))
        return response["rows"][0][0]

def run_sql_script(driver, script):
    with open(script, 'r') as s:
        driver.req(s.read())


if __name__ == '__main__':
    args = parser.parse_args()
    payload = ''
    with open(args.payload, 'r') as pl_file:
        payload = pl_file.read()
    raw_results = []
    crate = SimpleCrate(args.url)
    version = crate.fetch_version()

    # actual benchmarking
    for run in xrange(args.runs):
        if args.create: run_sql_script(crate, args.create)

        run_id = uuid.uuid4().hex # random run id

        for request in xrange(args.number_of_requests):
            raw_results.append((run_id, crate.req_raw(payload)))

        if args.drop: run_sql_script(crate, args.drop)


    results = []
    for run_id, result in raw_results:
        response = json.loads(result)
        try:
            results.append({
                "timestamp": timestamp(),
                "version": version,
                "duration": response["duration"],
                "run_id": run_id,
                "rows": reduce(lambda p, x: p + x["rowcount"], response["results"], 0)
            })
        except KeyError as e:
            print("Key Error: %s" % (e, ), response, file=sys.stderr)
            exit(1)

    if args.result_crate:
        result_crate = SimpleCrate(args.result_crate)
        table_headers = ("timestamp", "version", "duration", "run_id", "rows")
        stmt = "insert into %s (%s) values (%s)" % (RESULT_TABLE_NAME, ",".join(
            table_headers), ",".join("?" * len(table_headers)))

        bulk_args = []

        for row in results:
            bulk_args.append([row[h] for h in table_headers if h in row])

        result_crate.req(stmt, bulk_args)
    else:
        for result in results:
            print(json.dumps(result))
