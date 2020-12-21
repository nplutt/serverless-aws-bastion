import json
from typing import List, Optional

from mypy_boto3_iam.client import IAMClient

from serverless_aws_bastion.config import (
    SSM_DEREGISTER_POLICY_NAME,
    TASK_EXECUTION_ROLE_NAME,
    TASK_ROLE_NAME,
)
from serverless_aws_bastion.utils.aws_utils import (
    build_tags,
    fetch_boto3_client,
    load_aws_account_id,
)
from serverless_aws_bastion.utils.click_utils import log_info


def create_deregister_ssm_policy() -> str:
    """
    Creates an IAM policy that allows the bastion ECS task to
    deregister itself from SSM.

    Returns the policy arn
    """
    client: IAMClient = fetch_boto3_client("iam")
    try:
        log_info(f"Creating {SSM_DEREGISTER_POLICY_NAME} policy")
        response = client.create_policy(
            Description="Used by serverless-aws-bastion ECS task to "
            "deregister itself from SSM",
            PolicyName=SSM_DEREGISTER_POLICY_NAME,
            PolicyDocument=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": [
                                "ssm:DeregisterManagedInstance",
                                "ssm:DescribeInstanceInformation",
                            ],
                            "Effect": "Allow",
                            "Resource": "*",
                        }
                    ],
                }
            ),
        )
        return response["Policy"]["Arn"]
    except client.exceptions.EntityAlreadyExistsException:
        account_id = load_aws_account_id()
        return f"arn:aws:iam::{account_id}:policy/{SSM_DEREGISTER_POLICY_NAME}"


def delete_deregister_ssm_policy() -> None:
    """
    Deletes the IAM policy that allows the bastion ECS task to
    deregister itself from SSM.
    """
    client: IAMClient = fetch_boto3_client("iam")

    try:
        log_info(f"Deleting {SSM_DEREGISTER_POLICY_NAME} policy")
        account_id = load_aws_account_id()
        client.delete_policy(
            PolicyArn=f"arn:aws:iam::{account_id}:policy/{SSM_DEREGISTER_POLICY_NAME}",
        )
    except client.exceptions.NoSuchEntityException:
        return None


def create_bastion_task_role() -> str:
    """
    Creates the role that will be used by the bastion ECS task.
    Skips creation if the role already exists.

    Returns role arn
    """
    client: IAMClient = fetch_boto3_client("iam")

    current_role_arn = fetch_role_arn(TASK_ROLE_NAME)
    if current_role_arn:
        return current_role_arn

    log_info(f"Creating {TASK_ROLE_NAME} role")
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
        Tags=build_tags("iam"),
    )

    deregister_ssm_arn = create_deregister_ssm_policy()
    attach_policies_to_role(
        TASK_ROLE_NAME,
        [
            deregister_ssm_arn,
            "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
        ],
    )

    return response["Role"]["Arn"]


def delete_bastion_task_role() -> None:
    """
    Deletes the role that's used by the bastion ECS task.
    """
    delete_role(TASK_ROLE_NAME)


def create_bastion_task_execution_role() -> str:
    """
    Creates the role that will be used by ECS to launch the bastion ECS task.
    Skips creation if the role already exists.

    Returns role arn
    """
    client: IAMClient = fetch_boto3_client("iam")

    current_role_arn = fetch_role_arn(TASK_EXECUTION_ROLE_NAME)
    if current_role_arn:
        return current_role_arn

    log_info(f"Creating {TASK_EXECUTION_ROLE_NAME} role")
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
        Tags=build_tags("iam"),
    )
    attach_policies_to_role(
        TASK_EXECUTION_ROLE_NAME,
        [
            "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
        ],
    )

    return response["Role"]["Arn"]


def delete_bastion_task_execution_role() -> None:
    """
    Deletes role used by ECS to launch the bastion ECS task.
    """
    delete_role(TASK_EXECUTION_ROLE_NAME)


def delete_role(role_name: str) -> None:
    """
    Safely deletes a given role by first detaching any policies
    and then deleting the role and handling any exceptions
    """
    client: IAMClient = fetch_boto3_client("iam")

    try:
        log_info(f"Deleting {role_name} role")
        detach_policies_from_role(role_name)
        client.delete_role(RoleName=role_name)
    except client.exceptions.NoSuchEntityException:
        return None


def attach_policies_to_role(role_name: str, policy_arns: List[str]) -> None:
    """
    Attaches a list of IAM policies to a given IAM role
    """
    client: IAMClient = fetch_boto3_client("iam")
    for policy_arn in policy_arns:
        client.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)


def detach_policies_from_role(role_name: str) -> None:
    """
    Detaches all policies from a role
    """
    client: IAMClient = fetch_boto3_client("iam")

    try:
        policies = client.list_attached_role_policies(RoleName=role_name)
        policy_arns = [p["PolicyArn"] for p in policies["AttachedPolicies"]]
    except client.exceptions.NoSuchEntityException:
        return None

    for policy_arn in policy_arns:
        client.detach_role_policy(RoleName=role_name, PolicyArn=policy_arn)


def fetch_role_arn(role_name: str) -> Optional[str]:
    """
    Checks if the given role name exists

    Returns role arn if it exists
    """
    client: IAMClient = fetch_boto3_client("iam")

    try:
        response = client.get_role(RoleName=role_name)
    except client.exceptions.NoSuchEntityException:
        return None

    return response["Role"]["Arn"]
