#!/usr/bin/env bash

set -e

cleanup() {
    INSTANCE_ID_LOG='Successfully registered the instance with AWS SSM using Managed instance-id:'
    INSTANCE_ID=$(sudo grep ${INSTANCE_ID_LOG} /var/log/amazon/ssm/amazon-ssm-agent.log | cut -d ' ' -f14-)
    aws ssm deregister-managed-instance --instance-id ${INSTANCE_ID} --region ${AWS_REGION}
}
trap cleanup EXIT
trap cleanup SIGTERM

/usr/bin/amazon-ssm-agent -register -code ${ACTIVATION_CODE} -id ${ACTIVATION_ID} -region ${AWS_REGION} -clear -y
/usr/bin/amazon-ssm-agent