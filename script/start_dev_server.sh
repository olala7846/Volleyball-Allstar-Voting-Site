#!/usr/bin/env bash
# This script launches local server and attach to local database
# execute this in the same folder as app.yaml
# the local database will be populated under DB_PATH

DB_PATH="./db/allstar_datastore"
dev_appserver.py --datastore_path=$DB_PATH .
