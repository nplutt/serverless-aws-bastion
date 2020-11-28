#!/usr/bin/env bash

set -e

/usr/bin/amazon-ssm-agent -register -code ${ACTIVATION_CODE} -id ${ACTIVATION_ID} -region ${AWS_REGION} -clear -y
/usr/bin/amazon-ssm-agent