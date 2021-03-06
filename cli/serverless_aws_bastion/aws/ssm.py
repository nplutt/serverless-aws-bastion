from datetime import datetime, timedelta
from typing import Dict, List

from mypy_boto3_ssm.client import SSMClient
from mypy_boto3_ssm.type_defs import (
    CreateActivationResultTypeDef,
    InstanceInformationStringFilterTypeDef,
)

from serverless_aws_bastion.config import DEFAULT_NAME
from serverless_aws_bastion.utils.aws_utils import (
    build_tags,
    fetch_boto3_client,
)


def create_activation(
    iam_role_name: str,
    instance_name: str,
    bastion_id: str,
) -> CreateActivationResultTypeDef:
    """
    Creates an SSM activation code that is used to connect the agent
    back to SSM
    """
    instance_name = f"{DEFAULT_NAME}/{instance_name}"

    client: SSMClient = fetch_boto3_client("ssm")
    response = client.create_activation(
        Description=f"Used to activate ssm agent in {DEFAULT_NAME}",
        DefaultInstanceName=instance_name,
        IamRole=iam_role_name,
        RegistrationLimit=1,
        ExpirationDate=datetime.utcnow() + timedelta(minutes=5),
        Tags=build_tags("ssm", {"Name": instance_name, "BastionId": bastion_id}),
    )
    return response


def load_instance_ids(
    instance_name: str = None,
    bastion_ids: List[str] = None,
) -> Dict[str, str]:
    """
    Loads all of the ssm instance ids for instances that were
    created by this cli. If the instance name is passed in, then
    instances are also filtered by name.
    """
    client: SSMClient = fetch_boto3_client("ssm")
    filters: List[InstanceInformationStringFilterTypeDef] = [
        {
            "Key": "tag:CreatedBy",
            "Values": ["serverless-aws-bastion:cli"],
        },
    ]

    if instance_name:
        filters.append(
            {
                "Key": "tag:Name",
                "Values": [f"{DEFAULT_NAME}/{instance_name}"],
            },
        )

    if bastion_ids:
        filters.append(
            {
                "Key": "tag:BastionId",
                "Values": bastion_ids,
            },
        )

    response = client.describe_instance_information(Filters=filters)
    return {
        i["ActivationId"]: i["InstanceId"] for i in response["InstanceInformationList"]
    }
