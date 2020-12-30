import json
from functools import wraps
from typing import Optional

import click

from serverless_aws_bastion.aws.ec2 import load_public_ips_from_task_data
from serverless_aws_bastion.aws.ecs import (
    create_fargate_cluster,
    create_task_definition,
    delete_fargate_cluster,
    delete_task_definition,
    launch_fargate_task,
    load_running_task_info,
    stop_fargate_tasks,
)
from serverless_aws_bastion.aws.iam import (
    create_bastion_task_execution_role,
    create_bastion_task_role,
    delete_bastion_task_execution_role,
    delete_bastion_task_role,
    delete_deregister_ssm_policy,
)
from serverless_aws_bastion.aws.ssm import load_instance_ids
from serverless_aws_bastion.config import TASK_TIMEOUT
from serverless_aws_bastion.dto.instance_info import build_instance_info
from serverless_aws_bastion.enum.bastion_type import BastionType
from serverless_aws_bastion.enum.log_level import LogLevel
from serverless_aws_bastion.utils.click_utils import log_output, log_info


def common_params(func):
    @click.option(
        "--region",
        help="The aws region to run this command in",
        type=click.STRING,
        default=None,
    )
    @click.option(
        "--log-level",
        help="Output log level, the options are `info` or `error`. Default is `info`.",
        type=click.STRING,
        default=LogLevel.info.name,
    )
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@click.group()
def cli():
    pass


@cli.command(
    "create-fargate-cluster",
    help="Creates a Fargate cluster to launch the bastion into",
)
@click.option(
    "--cluster-name",
    help="The name of the Fargate cluster",
    required=True,
    type=click.STRING,
)
@common_params
def handle_create_fargate_cluster(cluster_name: str, **kwargs):
    create_fargate_cluster(cluster_name)
    log_output("Fargate cluster running")


@cli.command(
    "delete-fargate-cluster",
    help="Deletes a give Fargate cluster",
)
@click.option(
    "--cluster-name",
    help="The name of the Fargate cluster",
    required=True,
    type=click.STRING,
)
@common_params
def handle_delete_fargate_cluster(cluster_name: str, **kwargs):
    delete_fargate_cluster(cluster_name)
    log_output("Fargate cluster deleted")


@cli.command(
    "create-bastion-task",
    help="Creates the ECS task used to launch the bastion",
)
@click.option(
    "--task-role-arn",
    help="The role used by the bastion task to communicate with ECS & SSM, "
    "if left blank the default role will be created and used.",
    type=click.STRING,
    default=None,
)
@click.option(
    "--execution-role-arn",
    help="The role used by ECS to launch and manage the task, if left blank "
    "the default role will be created and used.",
    type=click.STRING,
    default=None,
)
@common_params
def handle_create_bastion_task(
    task_role_arn: str = None, execution_role_arn: str = None, **kwargs
):
    if not task_role_arn:
        task_role_arn = create_bastion_task_role()

    if not execution_role_arn:
        execution_role_arn = create_bastion_task_execution_role()

    create_task_definition(task_role_arn, execution_role_arn)
    log_output("Bastion ECS task created")


@cli.command(
    "delete-bastion-task",
    help="Creates the ECS task used to launch the bastion",
)
@common_params
def handle_delete_bastion_task(**kwargs):
    delete_task_definition()

    delete_bastion_task_role()
    delete_bastion_task_execution_role()
    delete_deregister_ssm_policy()

    log_output("Bastion ECS task deleted")


@cli.command(
    "start-bastion",
    help="Starts up a serverless bastion in your Fargate cluster",
)
@click.option(
    "--cluster-name",
    help="The name of the Fargate cluster to start the serverless bastion in",
    required=True,
    type=click.STRING,
)
@click.option(
    "--subnet-ids",
    help="A comma separated list of VPC subnet ids to launch the bastion into",
    required=True,
    type=click.STRING,
)
@click.option(
    "--security-group-ids",
    help="A comma separated list of security group ids to launch the bastion into",
    required=True,
    type=click.STRING,
)
@click.option(
    "--authorized-keys",
    help="All of the public keys that the bastion should allow",
    required=True,
    type=click.STRING,
)
@click.option(
    "--bastion-name",
    help="A unique name for the bastion instance",
    required=True,
    type=click.STRING,
)
@click.option(
    "--bastion-timeout",
    help="How many minutes that the bastion should stay alive for, "
    "the default is 8 hours",
    type=click.INT,
    default=TASK_TIMEOUT,
)
@click.option(
    "--bastion-type",
    help="The type of bastion that this task should run, options are either"
    "`original` or `ssm`",
    type=click.STRING,
    default=BastionType.ssm.value,
)
@common_params
def handle_launch_bastion(
    cluster_name: str,
    subnet_ids: str,
    security_group_ids: str,
    authorized_keys: str,
    bastion_name: str,
    bastion_timeout: int,
    bastion_type: str,
    **kwargs,
) -> None:
    try:
        bastion_type_enum = BastionType[bastion_type]
    except KeyError:
        raise click.ClickException("bastion-type must be one of `original` or `ssm`")

    launched_task_info = launch_fargate_task(
        cluster_name=cluster_name,
        subnet_ids=subnet_ids,
        security_group_ids=security_group_ids,
        authorized_keys=authorized_keys,
        instance_name=bastion_name,
        timeout_minutes=bastion_timeout,
        bastion_type=bastion_type_enum,
    )

    task_instance_info = launched_task_info['tasks']
    task_instance_ips = load_public_ips_from_task_data(task_instance_info)
    ssm_instance_info = load_instance_ids(bastion_name)

    instance_info = build_instance_info(
        task_instance_info,
        task_instance_ips,
        ssm_instance_info,
    )
    log_output(json.dumps([i.as_dict for i in instance_info], indent=4))


@cli.command(
    "stop-bastion-instances",
    help="Stop bastion instances in a given cluster",
)
@click.option(
    "--cluster-name",
    help="The name of the Fargate cluster to stop bastion instances in",
    type=click.STRING,
    required=True,
)
@click.option(
    "--bastion-name",
    help="The name bastion instance to filter by",
    type=click.STRING,
    default=None,
)
@click.option(
    "--bastion-id",
    help="The id bastion instance to filter by",
    type=click.STRING,
    default=None,
)
@common_params
def handle_stop_bastion_instances(
    cluster_name: str,
    bastion_name: Optional[str],
    bastion_id: Optional[str],
    **kwargs,
) -> None:
    task_info = load_running_task_info(cluster_name, bastion_name, bastion_id)
    stop_fargate_tasks(cluster_name, task_info)
    log_output(f"Stopped {len(task_info)} tasks")


@cli.command(
    "list-bastion-instances",
    help="Lists all serverless bastion instances running in your Fargate cluster",
)
@click.option(
    "--cluster-name",
    help="The name of the Fargate cluster to check for bastion instances in",
    type=click.STRING,
    required=True,
)
@click.option(
    "--bastion-name",
    help="The name bastion instance to filter by",
    type=click.STRING,
    default=None,
)
@common_params
def handle_list_bastion_instances(
    cluster_name: str, bastion_name: Optional[str], **kwargs
) -> None:
    task_instance_info = load_running_task_info(cluster_name, bastion_name)
    task_instance_ips = load_public_ips_from_task_data(task_instance_info)
    ssm_instance_info = load_instance_ids(bastion_name)

    instance_info = build_instance_info(
        task_instance_info,
        task_instance_ips,
        ssm_instance_info,
    )
    log_output(json.dumps([i.as_dict for i in instance_info], indent=4))


def main() -> None:
    cli()
