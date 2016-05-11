# crate-version-comparison

Tests the INSERT performance for an existing Crate version/nigthly build.


# Run the Benchmark

Essentially, there are two scripts (located in tools): `bench.py` and `data-gen.py`
that do the heavy lifting. `data-gen.py` generates a payload JSON file, which
is sent to a server via the `bench.py` script.

## data-gen.py

Run the script to create a JSON payload. To adjust the output, variables
in the beginning of the file can be used.

```
$ python2 data-gen.py > ../data/payload.1k.json
```

## bench.py

This script will execute the benchmark by sending the payload via HTTP
requests to Crate *sequentially*. Additionally further options let you
specify how to create/drop the benchmark table and if the whole run should
be repeated.

Example run:

```
$ python2 bench.py ../data/payload.1k.json 2 localhost:4200 --create ../data/bench.t1.create.ddl --drop ../data/bench.t1.drop.ddl --runs 10 --result-crate localhost:4200
```

## runme.sh

This script ties everything together: It downloads and runs the specified
Crate version, makes sure they form a cluster and then starts the benchmark.
To pass in a crate version either set the environment variable or use the
first argument. More fine tuning can be done within the script.

Example run:

```
$ ./runme.sh 0.54.9
```

# Getting help

This project is not extensively documented and was intentionally kept really
simple.

```
$ python2 bench.py --help
usage: bench.py [-h] [--runs RUNS] [--create CREATE] [--drop DROP]
                [--result-crate RESULT_CRATE]
                payload number_of_requests url

Push-based insert benchmarking.

positional arguments:
  payload               the payload file
  number_of_requests    how many requests to make (number_of_requests *
                        bulksize = nr of rows inserted)
  url                   server address, use url:port

optional arguments:
  -h, --help            show this help message and exit
  --runs RUNS           number of times to repeat the inserts
  --create CREATE       path to create table script
  --drop DROP           path to drop table script
  --result-crate RESULT_CRATE
                        url:port to Crate for saving results instead of STDOUT
```
