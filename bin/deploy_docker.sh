#!/usr/bin/env bash

set -e

cd "$(dirname "$0")/.."
docker build -t nplutt/serverless-ssm-bastion .
docker push nplutt/serverless-ssm-bastion:latest