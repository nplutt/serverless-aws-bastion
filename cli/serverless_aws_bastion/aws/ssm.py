from datetime import datetime, timedelta

from mypy_boto3_ssm.client import SSMClient
from mypy_boto3_ssm.type_defs import CreateActivationResultTypeDef

from serverless_aws_bastion.aws.utils import fetch_boto3_client
from serverless_aws_bastion.config import DEFAULT_INSTANCE_NAME


def create_activation(iam_role_name: str) -> CreateActivationResultTypeDef:
    """
    Creates an SSM activation code that is used to connect the agent
    back to SSM
    """
    client: SSMClient = fetch_boto3_client("ssm")
    response = client.create_activation(
        Description=f"Used to activate ssm agent in {DEFAULT_INSTANCE_NAME}",
        DefaultInstanceName=DEFAULT_INSTANCE_NAME,
        IamRole=iam_role_name,
        RegistrationLimit=1,
        ExpirationDate=datetime.utcnow() + timedelta(minutes=5),
    )
    return response
