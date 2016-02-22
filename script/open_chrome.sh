#!/usr/bin/env bash
# This script launches insecure chrome to test Google Cloud Endpoint
# explorer server

PORT_NUM=8080
LAUNCH_CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"${LAUNCH_CHROME}" --user-data-dir=dev_chrome --unsafely-treat-insecure-origin-as-secure=http://localhost:$PORT_NUM
