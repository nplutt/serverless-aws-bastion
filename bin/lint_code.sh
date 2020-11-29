#!/usr/bin/env bash

set -e

cd "$(dirname "$0")/../cli"

echo "Running black..."
black . --check

echo "Running isort..."
isort . -c

echo "Running mypy..."
mypy -p serverless_aws_bastion
