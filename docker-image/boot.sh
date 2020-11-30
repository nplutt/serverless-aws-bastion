#!/usr/bin/env bash

set -e

cleanup() {
    INSTANCE_ID=$(
        sudo grep 'Successfully registered the instance with AWS SSM using Managed instance-id:' /var/log/amazon/ssm/amazon-ssm-agent.log \
        | awk '{print $NF}'
    )
    aws ssm deregister-managed-instance --instance-id ${INSTANCE_ID} --region ${AWS_REGION}
}
trap cleanup EXIT SIGTERM SIGKILL

/usr/bin/amazon-ssm-agent -register -code ${ACTIVATION_CODE} -id ${ACTIVATION_ID} -region ${AWS_REGION} -clear -y
/usr/bin/amazon-ssm-agent