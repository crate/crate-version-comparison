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

import json
import random
import string
import sys
import argparse

parser = argparse.ArgumentParser(description='Data payload generation.')
parser.add_argument('--unnest', default=False, action='store_true',
                    help='Instead of bulk requests use insert into UNNEST')

BATCH_SIZE = 1000   # rows
PAYLOAD_SIZE = 512  # bytes
COLUMN_NAME = 't'
TABLE_NAME = 'bench.t1'
SQL = 'insert into %s (%s) values (?)' % (TABLE_NAME, COLUMN_NAME)
SQL_UNNEST = 'insert into %s (%s) ' % (TABLE_NAME, COLUMN_NAME)
SQL_UNNEST_SUB = "select * from unnest([%s])"


def payload():
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(PAYLOAD_SIZE))


if __name__ == '__main__':
    args = parser.parse_args()
    rq = {}

    if args.unnest:
        p = ["'%s'" % payload() for row in xrange(BATCH_SIZE)]
        subqry = SQL_UNNEST_SUB % ','.join(p)
        rq["stmt"] = "%s (%s)" % (SQL_UNNEST, subqry)
    else:
        rq = {
            "stmt": SQL,
            "bulk_args": [[payload(), ] for row in xrange(BATCH_SIZE)]
        }

    print(json.dumps(rq))
