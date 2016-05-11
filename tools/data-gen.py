import json
import random
import string

BATCH_SIZE = 1000   # rows
PAYLOAD_SIZE = 512  # bytes
COLUMN_NAME = 't'
TABLE_NAME = 'bench.t1'
SQL = 'insert into %s (%s) values (?)' % (TABLE_NAME, COLUMN_NAME)


def payload():
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(PAYLOAD_SIZE))


if __name__ == '__main__':
    print(json.dumps({
        "stmt": SQL,
        "bulk_args": [[payload(), ] for row in xrange(BATCH_SIZE)]
    }))
