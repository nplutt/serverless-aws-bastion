#!/usr/bin/env bash

set -e

cd "$(dirname "$0")/../cli"

echo "Running black..."
black . --check

echo "Running add trailing commas..."
add-trailing-comma $(find . -type f -name '*.py')

echo "Running isort..."
isort . -c

echo "Running mypy..."
mypy -p serverless_aws_bastion
