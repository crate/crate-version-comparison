import json
import argparse
import httplib
import urllib
import uuid
import datetime

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
                    help='server address, use url:port')
parser.add_argument('--create', default='', help='path to create table script')
parser.add_argument('--drop', default='', help='path to drop table script')
parser.add_argument('--result-crate', default='',
                    help='url to Crate for saving results')


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


if __name__ == '__main__':
    args = parser.parse_args()
    payload = ''
    with open(args.payload, 'r') as pl_file:
        payload = pl_file.read()
    raw_results = []
    crate = SimpleCrate(args.url)
    version = crate.fetch_version()

    if args.create:
        with open(args.create, 'r') as create_script:
            crate.req(create_script.read())

    # WARMUP Request
    crate.req_raw(payload)

    # actual benchmarking
    for run in xrange(args.runs):
        run_id = uuid.uuid4().hex
        for request in xrange(args.number_of_requests):
            raw_results.append((run_id, crate.req_raw(payload)))

    if args.drop:
        with open(args.drop, 'r') as drop_script:
            crate.req(drop_script.read())

    results = []
    for run_id, result in raw_results:
        response = json.loads(result)
        results.append({
            "timestamp": timestamp(),
            "version": version,
            "duration": response["duration"],
            "run_id": run_id,
            "rows": reduce(lambda p, x: p + x["rowcount"], response["results"], 0)
        })
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