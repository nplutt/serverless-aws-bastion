#!/usr/bin/env bash

set -e

cd "$(dirname "$0")/../cli"

black .
isort .
add-trailing-comma $(find . -type f -name '*.py') --exit-zero-even-if-changed