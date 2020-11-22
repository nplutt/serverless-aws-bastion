from time import sleep
from typing import List

import click
from mypy_boto3_ecs.client import ECSClient
from mypy_boto3_ecs.type_defs import DescribeTasksResponseTypeDef, TaskTypeDef

from serverless_aws_bastion.aws.clients import fetch_boto3_client
from serverless_aws_bastion.config import TASK_BOOT_TIMEOUT


def launch_fargate_task(
    cluster_name: str,
    subnet_ids: str,
    security_group_ids: str,
    authorized_keys: str,
) -> None:
    """
    Launches the ssh bastion Fargate task into the proper subnets & security groups,
    also sends in the authorized keys.
    """
    client: ECSClient = fetch_boto3_client("ecs")

    click.secho("Starting bastion task", fg="green")
    response = client.run_task(
        cluster=cluster_name,
        taskDefinition=f"ssh-task",
        overrides={
            "containerOverrides": [
                {
                    "name": "ssm-bastion",
                    "environment": [
                        {"name": "AUTHORIZED_KEYS", "value": authorized_keys},
                    ],
                }
            ]
        },
        count=1,
        launchType="FARGATE",
        networkConfiguration={
            "awsvpcConfiguration": {
                "subnets": subnet_ids.split(","),
                "securityGroups": security_group_ids.split(","),
                "assignPublicIp": "ENABLED",
            }
        },
    )

    wait_for_tasks_to_start(cluster_name, response["tasks"])


def describe_task(
    cluster_name: str,
    task_arns: List[str],
) -> DescribeTasksResponseTypeDef:
    """
    Fetches the statuses for a group of tasks
    """
    client: ECSClient = fetch_boto3_client("ecs")

    return client.describe_tasks(
        cluster=cluster_name,
        tasks=task_arns,
    )


def wait_for_tasks_to_start(
    cluster_name: str,
    tasks: List[TaskTypeDef],
    timeout_seconds: int = TASK_BOOT_TIMEOUT,
) -> None:
    """
    Waits for all of the tasks to reach their desired state by polling
    the current state of the tasks
    """
    task_arns = [t["taskArn"] for t in tasks]

    tasks_started = False
    wait_time = 0

    click.secho("Waiting for bastion task to start...", fg="green")
    while not tasks_started and wait_time < timeout_seconds:
        task_info = describe_task(cluster_name, task_arns)

        if len(task_info["failures"]) > 0:
            break

        tasks_started = all(
            [t["lastStatus"] == t["desiredStatus"] for t in task_info["tasks"]]
        )

        sleep(2)
        wait_time += 2

    if not tasks_started:
        click.secho("Bastion task failed to start", err=True)
