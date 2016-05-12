#!/bin/sh -e

# Configurable parameters

## Source packages
CDN=https://cdn.crate.io/downloads/releases

## Cache for the runtime environment
BASEDIR=${WORKSPACE:-$HOME}/cache

## Number of nodes in cluster
N=2

## ???
RUNS=100

## ???
REQUESTS=100

## IP of cluster nodes
IP=127.0.0.2

## Starting port of cluster nodes http and transport, get incremented for each node
HTTPPORT=4251
TRANPORT=4351

## Memory for Java heap
CRATE_HEAP_SIZE=1g

## Tools directory from package crate-version-comparison
TOOLSDIR=${WORKSPACE:-$(pwd)}/tools

## Python interpreter
PYTHON=python2.7


# Command line parsing
if [ "$1" = "" ]; then
    echo "No args found. Trying environment CRATE_VERSION:"
    ver=$CRATE_VERSION
else
    echo "Using command line argument for version:"
    ver=$1
fi

if [ "$ver" = "" ]; then
    echo "No version provided. Exiting."
    echo "Usage: $0 version"
    exit 1
else
    echo "Scaffolding Crate version $ver."
fi

echo "Java environment:"
if java -version; then
    echo "Java ok."
else
    echo "missing. Exiting."
    exit 2
fi


echo "Python environment:"
if $PYTHON --version; then
    echo "Python ok."
else
    echo "missing. Exiting."
    exit 3
fi


# Project environment cache, each version gets own directory
[ -d $BASEDIR ] || mkdir -p $BASEDIR
cd $BASEDIR


# Install Crate 
if [ -d crate-$ver ]; then
    echo "crate-$ver is already downloaded:"
    ls -ld crate-$ver
else
    echo "Downloading crate-$ver ..."
    curl -Ssl $CDN/crate-$ver.tar.gz | tar xfz -
    echo "Installed."
fi
cd crate-$ver
[ -d logs ] || mkdir logs

# Start Crate cluster with N nodes
export CRATE_HEAP_SIZE=8g
http=$HTTPPORT
tran=$TRANPORT
for i in $(seq 1 $N); do
    echo "Launching bench-node-$i ..." 
    ./bin/crate \
          -Des.cluster.name=bench-insert-cluster \
	  -Des.network.bind_host=$IP \
          -Des.network.publish_host=$IP \
	  -Des.http.port=$http \
          -Des.transport.tcp.port=$tran \
          -Des.transport.publish_port=$tran \
          -Des.node.name=bench-node-$i \
          -Des.multicast.enabled=true \
          > logs/bench-node-$i-$(date +%Y-%m-%d-%H:%M).log &
    http=$(($http + 1))
    tran=$(($tran + 1))
done
echo "All nodes launched. See logs in $BASEDIR/crate-$ver/logs:"
ls -l logs


# Prearrange benchmark data if not existing
if [ -f $BASEDIR/bench-data.json ]; then
    echo "Benchmark data available: $(ls $BASEDIR/bench-data.json)."
else
    echo "Generating benchmark data."
    $PYTHON $TOOLSDIR/data-gen.py > $BASEDIR/bench-data.json
fi


# Spinlock to make sure the cluster has started by now

echo -n "Waiting for cluster to become ready: "
until curl -Ssl 127.0.0.2:4251 2>/dev/null | grep -q ok; do
    echo -n "."
    sleep 1
done
echo " Ready."


# Feed benchmark data into cluster
echo "Starting benchmark ..."
echo $PYTHON $TOOLSDIR/bench.py --runs $RUNS \
                 $BASEDIR/bench-data.json \
                 $REQUESTS \
		 $IP:$HTTPPORT
$PYTHON $TOOLSDIR/bench.py --runs $RUNS \
                 $BASEDIR/bench-data.json \
                 $REQUESTS \
		 $IP:$HTTPPORT
echo "Finished."
