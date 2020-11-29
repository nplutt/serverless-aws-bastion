import json
from typing import List, Optional

import click
from mypy_boto3_iam.client import IAMClient

from serverless_aws_bastion.aws.utils import (
    fetch_boto3_client,
    get_default_tags,
)
from serverless_aws_bastion.config import (
    TASK_EXECUTION_ROLE_NAME,
    TASK_ROLE_NAME,
)


# def create_deregister_ssm_policy() -> str:
#     client: IAMClient = fetch_boto3_client("iam")
#     client.create_policy()


def create_bastion_task_role() -> str:
    """
    Creates the role that will be used by the bastion ECS task.
    Skips creation if the role already exists.
    """
    client: IAMClient = fetch_boto3_client("iam")

    current_role_arn = fetch_role_arn(TASK_ROLE_NAME)
    if current_role_arn:
        return current_role_arn

    click.secho(f"Creating {TASK_ROLE_NAME} role", fg="green")
    response = client.create_role(
        RoleName=TASK_ROLE_NAME,
        Description="Used by serverless-aws-bastion ECS tasks",
        AssumeRolePolicyDocument=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "",
                        "Effect": "Allow",
                        "Principal": {
                            "Service": ["ecs-tasks.amazonaws.com", "ssm.amazonaws.com"]
                        },
                        "Action": "sts:AssumeRole",
                    }
                ],
            }
        ),
        Tags=get_default_tags("iam"),
    )
    attach_policies_to_role(
        TASK_ROLE_NAME,
        [
            "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
        ],
    )

    return response["Role"]["Arn"]


def create_bastion_task_execution_role() -> str:
    """
    Creates the role that will be used by ECS to launch the bastion ECS task.
    Skips creation if the role already exists.
    """
    client: IAMClient = fetch_boto3_client("iam")

    current_role_arn = fetch_role_arn(TASK_EXECUTION_ROLE_NAME)
    if current_role_arn:
        return current_role_arn

    click.secho(f"Creating {TASK_EXECUTION_ROLE_NAME} role", fg="green")
    response = client.create_role(
        RoleName=TASK_EXECUTION_ROLE_NAME,
        Description="Used by Fargate to launch serverless-aws-bastion ECS tasks",
        AssumeRolePolicyDocument=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "",
                        "Effect": "Allow",
                        "Principal": {"Service": ["ecs-tasks.amazonaws.com"]},
                        "Action": "sts:AssumeRole",
                    }
                ],
            }
        ),
        Tags=get_default_tags("iam"),
    )
    attach_policies_to_role(
        TASK_EXECUTION_ROLE_NAME,
        [
            "arn:aws:iam::aws:policy/AmazonECSTaskExecutionRolePolicy",
        ],
    )

    return response["Role"]["Arn"]


def attach_policies_to_role(role_name: str, policy_arns: List[str]) -> None:
    """
    Attaches a list of IAM policies to a given IAM role
    """
    client: IAMClient = fetch_boto3_client("iam")
    for policy_arn in policy_arns:
        client.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)


def fetch_role_arn(role_name: str) -> Optional[str]:
    """
    Checks if the given role name exists
    """
    client: IAMClient = fetch_boto3_client("iam")

    try:
        response = client.get_role(RoleName=role_name)
    except client.exceptions.NoSuchEntityException:
        return None

    return response["Role"]["Arn"]
