from time import sleep
from typing import List

import click
from mypy_boto3_ecs.client import ECSClient
from mypy_boto3_ecs.type_defs import (
    CreateClusterResponseTypeDef,
    DescribeClustersResponseTypeDef,
    DescribeTasksResponseTypeDef,
    RunTaskResponseTypeDef,
    TaskTypeDef,
)

from serverless_aws_bastion.aws.ssm import create_activation
from serverless_aws_bastion.aws.utils import (
    fetch_boto3_client,
    get_default_tags,
    load_aws_region_name,
)
from serverless_aws_bastion.config import (
    CLUSTER_PROVISION_TIMEOUT,
    DEFAULT_NAME,
    TASK_BOOT_TIMEOUT,
    TASK_CPU,
    TASK_DEFINITION,
    TASK_MEMORY,
    TASK_ROLE_NAME,
)
from serverless_aws_bastion.enums.cluster_status import ClusterStatus


def create_fargate_cluster(cluster_name: str) -> CreateClusterResponseTypeDef:
    """
    Creates a Fargate cluster to launch the bastion task into
    """
    client: ECSClient = fetch_boto3_client("ecs")

    click.secho("Creating Fargate cluster", fg="green")
    response = client.create_cluster(
        clusterName=cluster_name,
        capacityProviders=["FARGATE"],
        tags=get_default_tags("ecs"),
    )
    wait_for_fargate_cluster_status(cluster_name, ClusterStatus.ACTIVE)
    return response


def delete_fargate_cluster(cluster_name: str) -> None:
    """
    Deletes a given Fargate cluster
    """
    client: ECSClient = fetch_boto3_client("ecs")

    click.secho("Deleting Fargate cluster", fg="green")
    client.delete_cluster(cluster=cluster_name)
    wait_for_fargate_cluster_status(cluster_name, ClusterStatus.INACTIVE)


def describe_fargate_cluster(cluster_name: str) -> DescribeClustersResponseTypeDef:
    """
    Fetches the status for a given cluster
    """
    client: ECSClient = fetch_boto3_client("ecs")
    return client.describe_clusters(clusters=[cluster_name])


def wait_for_fargate_cluster_status(
    cluster_name: str,
    cluster_stats: ClusterStatus,
    timeout_seconds: int = CLUSTER_PROVISION_TIMEOUT,
) -> None:
    """
    Waits for a cluster to to reach a desired status by polling the current
    state of the cluster
    """
    cluster_provisioned = False
    wait_time = 0

    click.secho(
        f"Waiting for cluster to reach {cluster_stats.value} state...", fg="green"
    )
    while not cluster_provisioned and wait_time < timeout_seconds:
        cluster_info = describe_fargate_cluster(cluster_name)

        if len(cluster_info["failures"]) > 0:
            break

        cluster_provisioned = all(
            [c["status"] == cluster_stats.value for c in cluster_info["clusters"]]
        )

        sleep(2)
        wait_time += 2

    if not cluster_provisioned:
        click.secho("Cluster failed to provision", err=True)


def create_task_definition(task_role_arn: str, execution_role_arn: str):
    """
    Creates the task definition that will be used to launch the
    serverless bastion container
    """
    client: ECSClient = fetch_boto3_client("ecs")

    click.secho("Creating bastion ECS task", fg="green")
    client.register_task_definition(
        family=DEFAULT_NAME,
        networkMode="awsvpc",
        cpu=TASK_CPU,
        memory=TASK_MEMORY,
        taskRoleArn=task_role_arn,
        executionRoleArn=execution_role_arn,
        containerDefinitions=[
            {
                "image": f"nplutt/{DEFAULT_NAME}",
                "name": DEFAULT_NAME,
                "essential": True,
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": "/ecs/ssh-bastion",
                        "awslogs-region": "us-west-2",
                        "awslogs-stream-prefix": "ecs",
                    },
                },
            },
        ],
        tags=get_default_tags("ecs"),
    )


def launch_fargate_task(
    cluster_name: str,
    subnet_ids: str,
    security_group_ids: str,
    authorized_keys: str,
) -> RunTaskResponseTypeDef:
    """
    Launches the ssh bastion Fargate task into the proper subnets & security groups,
    also sends in the authorized keys.
    """
    client: ECSClient = fetch_boto3_client("ecs")

    activation = create_activation(TASK_ROLE_NAME)

    click.secho("Starting bastion task", fg="green")
    response = client.run_task(
        cluster=cluster_name,
        taskDefinition=DEFAULT_NAME,
        overrides={
            "containerOverrides": [
                {
                    "name": DEFAULT_NAME,
                    "environment": [
                        {"name": "AUTHORIZED_SSH_KEYS", "value": authorized_keys},
                        {"name": "ACTIVATION_ID",
                            "value": activation["ActivationId"]},
                        {
                            "name": "ACTIVATION_CODE",
                            "value": activation["ActivationCode"],
                        },
                        {"name": "AWS_REGION", "value": load_aws_region_name()},
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
        tags=get_default_tags("ecs"),
    )

    wait_for_tasks_to_start(cluster_name, response["tasks"])
    return response


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
