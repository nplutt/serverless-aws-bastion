#!/usr/bin/env bash

set -e

cd "$(dirname "$0")/../docker-image"
docker build -t nplutt/ssm-bastion .
docker push nplutt/serverless-ssm-bastion:latest