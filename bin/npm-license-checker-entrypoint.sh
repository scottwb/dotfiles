#!/usr/bin/env bash

# This script is meant to be run inside a Docker container
# via the npm-license-checker script. Note that it installs
# stuff, so if you run it outside of docker, this will
# affect your system.

npm install -g license-checker
license-checker --csv --out=third-party-license-info.csv
