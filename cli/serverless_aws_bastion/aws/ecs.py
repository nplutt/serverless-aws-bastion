from time import sleep
from typing import Dict, List, Optional
from uuid import uuid4

from click import Abort
from mypy_boto3_ecs.client import ECSClient
from mypy_boto3_ecs.type_defs import (
    CreateClusterResponseTypeDef,
    DescribeClustersResponseTypeDef,
    DescribeTasksResponseTypeDef,
    RunTaskResponseTypeDef,
    TaskTypeDef,
)

from serverless_aws_bastion.aws.ec2 import (
    load_public_ips_for_network_interfaces,
)
from serverless_aws_bastion.aws.ssm import create_activation
from serverless_aws_bastion.config import (
    CLUSTER_PROVISION_TIMEOUT,
    DEFAULT_NAME,
    TASK_BOOT_TIMEOUT,
    TASK_CPU,
    TASK_MEMORY,
    TASK_ROLE_NAME,
)
from serverless_aws_bastion.enum.bastion_type import BastionType
from serverless_aws_bastion.enum.cluster_status import ClusterStatus
from serverless_aws_bastion.utils.aws_utils import (
    build_tags,
    fetch_boto3_client,
    get_tag_value,
    load_aws_region_name,
)
from serverless_aws_bastion.utils.click_utils import log_error, log_info


def create_fargate_cluster(cluster_name: str) -> CreateClusterResponseTypeDef:
    """
    Creates a Fargate cluster to launch the bastion task into
    """
    client: ECSClient = fetch_boto3_client("ecs")

    log_info("Creating Fargate cluster")
    response = client.create_cluster(
        clusterName=cluster_name,
        capacityProviders=["FARGATE"],
        tags=build_tags("ecs"),
    )
    wait_for_fargate_cluster_status(cluster_name, ClusterStatus.ACTIVE)
    return response


def delete_fargate_cluster(cluster_name: str) -> None:
    """
    Deletes a given Fargate cluster
    """
    client: ECSClient = fetch_boto3_client("ecs")

    log_info("Deleting Fargate cluster")

    try:
        client.delete_cluster(cluster=cluster_name)
    except client.exceptions.ClusterNotFoundException:
        log_error(f"Failed to find {cluster_name} Fargate cluster")
        raise Abort()

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

    log_info(f"Waiting for cluster to reach {cluster_stats.value} state...")
    while not cluster_provisioned and wait_time < timeout_seconds:
        cluster_info = describe_fargate_cluster(cluster_name)

        if len(cluster_info["failures"]) > 0:
            break

        cluster_provisioned = all(
            [c["status"] == cluster_stats.value for c in cluster_info["clusters"]],
        )

        sleep(2)
        wait_time += 2

    if not cluster_provisioned:
        log_error("Cluster failed to provision")
        raise Abort()


def create_task_definition(task_role_arn: str, execution_role_arn: str) -> None:
    """
    Creates the task definition that will be used to launch the
    serverless bastion container
    """
    client: ECSClient = fetch_boto3_client("ecs")

    log_info("Creating bastion ECS task")
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
                "portMappings": [
                    {
                        "hostPort": 22,
                        "protocol": "tcp",
                        "containerPort": 22,
                    },
                ],
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": "/ecs/ssh-bastion",
                        "awslogs-region": load_aws_region_name(),
                        "awslogs-stream-prefix": "ecs",
                    },
                },
            },
        ],
        tags=build_tags("ecs"),
    )


def delete_task_definition() -> None:
    """
    Inactivates all serverless-aws-bastion task definitions
    """
    client: ECSClient = fetch_boto3_client("ecs")
    task_definitions = client.list_task_definitions(familyPrefix=DEFAULT_NAME)

    log_info("Deregistering task definitions")
    for td in task_definitions["taskDefinitionArns"]:
        client.deregister_task_definition(taskDefinition=td)


def launch_fargate_task(
    cluster_name: str,
    subnet_ids: str,
    security_group_ids: str,
    authorized_keys: str,
    instance_name: str,
    timeout_minutes: int,
    bastion_type: BastionType,
) -> RunTaskResponseTypeDef:
    """
    Launches the ssh bastion Fargate task into the proper subnets & security groups,
    also sends in the authorized keys.
    """
    client: ECSClient = fetch_boto3_client("ecs")

    bastion_id = str(uuid4())

    activation: Dict[str, str] = {}
    if bastion_type == BastionType.ssm:
        activation = create_activation(TASK_ROLE_NAME, instance_name, bastion_id)  # type: ignore

    log_info("Starting bastion task")
    try:
        response = client.run_task(
            cluster=cluster_name,
            taskDefinition=DEFAULT_NAME,
            overrides={
                "containerOverrides": [
                    {
                        "name": DEFAULT_NAME,
                        "environment": [
                            {"name": "AUTHORIZED_SSH_KEYS", "value": authorized_keys},
                            {
                                "name": "ACTIVATION_ID",
                                "value": activation.get("ActivationId", ""),
                            },
                            {
                                "name": "ACTIVATION_CODE",
                                "value": activation.get("ActivationCode", ""),
                            },
                            {"name": "AWS_REGION", "value": load_aws_region_name()},
                            {"name": "TIMEOUT", "value": str(timeout_minutes * 60)},
                            {"name": "BASTION_TYPE", "value": bastion_type.value},
                        ],
                    },
                ],
            },
            count=1,
            launchType="FARGATE",
            networkConfiguration={
                "awsvpcConfiguration": {
                    "subnets": subnet_ids.split(","),
                    "securityGroups": security_group_ids.split(","),
                    "assignPublicIp": "ENABLED",
                },
            },
            tags=build_tags(
                "ecs",
                {
                    "Name": f"{DEFAULT_NAME}/{instance_name}",
                    "BastionId": bastion_id,
                    "ActivationId": activation.get("ActivationId", ""),
                },
            ),
        )

    except client.exceptions.ClusterNotFoundException:
        log_error("Specified cluster to launch bastion task into doesn't exist")
        raise Abort()

    except (
        client.exceptions.ClientException,
        client.exceptions.InvalidParameterException,
    ) as e:
        log_error(e.response["Error"]["Message"])
        raise Abort()

    wait_for_tasks_to_start(cluster_name, response["tasks"])
    return response


def stop_fargate_tasks(cluster: str, tasks: List[TaskTypeDef]) -> None:
    client: ECSClient = fetch_boto3_client("ecs")

    log_info(f"Stopping {len(tasks)} tasks...")
    for t in tasks:
        client.stop_task(cluster=cluster, task=t["taskArn"])


def describe_task(
    cluster_name: str,
    task_arns: List[str],
) -> Optional[DescribeTasksResponseTypeDef]:
    """
    Fetches the statuses for a group of tasks
    """
    client: ECSClient = fetch_boto3_client("ecs")

    if len(task_arns) == 0:
        return None

    return client.describe_tasks(
        cluster=cluster_name,
        tasks=task_arns,
        include=["TAGS"],
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

    log_info("Waiting for bastion task to start...")
    while not tasks_started and wait_time < timeout_seconds:
        task_info = describe_task(cluster_name, task_arns)

        if not task_info or len(task_info["failures"]) > 0:
            break

        tasks_started = all(
            [t["lastStatus"] == t["desiredStatus"] for t in task_info["tasks"]],
        )

        sleep(2)
        wait_time += 2

    if not tasks_started:
        log_error("Bastion task failed to start")
        raise Abort()


def load_running_task_info(
    cluster_name: str,
    instance_name: Optional[str] = None,
    bastion_id: Optional[str] = None,
) -> List[TaskTypeDef]:
    """
    Loads and returns all running bastion tasks in the given cluster with the
    selected instance name
    """
    client: ECSClient = fetch_boto3_client("ecs")

    task_list = client.list_tasks(cluster=cluster_name, family=DEFAULT_NAME)
    task_response = describe_task(cluster_name, task_list["taskArns"])

    if not task_response:
        return []

    response = task_response["tasks"]

    if instance_name:
        response = [
            t
            for t in response
            if f"{DEFAULT_NAME}/{instance_name}"
            == get_tag_value("ecs", t["tags"], "Name")
        ]

    if bastion_id:
        response = [
            t
            for t in response
            if bastion_id == get_tag_value("ecs", t["tags"], "BastionId")
        ]

    return response


def load_task_public_ips(cluster_name: str, instance_name: str) -> List[str]:
    """
    Loads all of the public ip addresses for tasks that were
    created by this cli. If the instance name is passed in, then
    instances are also filtered by name.
    """
    tasks = load_running_task_info(cluster_name, instance_name)

    attachments = [a for t in tasks for a in t["attachments"]]
    network_interface_ids = [
        detail["value"]
        for a in attachments
        for detail in a["details"]
        if detail["name"] == "networkInterfaceId"
    ]
    return list(load_public_ips_for_network_interfaces(network_interface_ids).values())
