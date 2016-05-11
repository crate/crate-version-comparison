# crate-version-comparison
Tests the INSERT performance for an existing Crate version.

# HOWTO

Generate payload (adjust variables in the python file to fine-tune stuff):

```
python2 data-gen.py > ../data/payload.1k.json
```

Run benchmark:
```
python2 bench.py ../data/payload.json 2 localhost:4200 --create ../data/bench.t1.create.ddl --drop ../data/bench.t1.drop.ddl --runs 10 --result-crate localhost:4200
``
