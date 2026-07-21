#!/bin/sh
set -eu
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
python3 "$project_dir/scripts/verify_boundary.py" --root "$project_dir"
python3 -B -m unittest discover -s "$project_dir/tests" -v
printf '%s\n' 'Static upstream-reference verification passed; no JVM, sbt, Solr, server, login, release, or deployment process was started.'
