import click

from serverless_aws_bastion.aws.ecs import (
    create_fargate_cluster,
    create_task_definition,
    delete_fargate_cluster,
    delete_task_definition,
    launch_fargate_task,
    load_task_public_ips,
)
from serverless_aws_bastion.aws.iam import (
    create_bastion_task_execution_role,
    create_bastion_task_role,
    delete_bastion_task_execution_role,
    delete_bastion_task_role,
)
from serverless_aws_bastion.aws.ssm import load_instance_ids
from serverless_aws_bastion.config import TASK_TIMEOUT
from serverless_aws_bastion.enums.bastion_type import BastionType
from serverless_aws_bastion.utils.click_utils import log_info


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
@click.option(
    "--region",
    help="The aws region where the Fargate cluster should be created",
    type=click.STRING,
    default=None,
)
def handle_create_fargate_cluster(cluster_name: str, region: str):
    create_fargate_cluster(cluster_name)
    log_info("Fargate cluster running")


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
@click.option(
    "--region",
    help="The aws region where the Fargate cluster should be deleted",
    type=click.STRING,
    default=None,
)
def handle_delete_fargate_cluster(cluster_name: str, region: str):
    delete_fargate_cluster(cluster_name)
    log_info("Fargate cluster deleted")


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
@click.option(
    "--region",
    help="The aws region where the Fargate task should be created",
    type=click.STRING,
    default=None,
)
def handle_create_bastion_task(
    task_role_arn: str = None,
    execution_role_arn: str = None,
    region: str = None,
):
    if not task_role_arn:
        task_role_arn = create_bastion_task_role()

    if not execution_role_arn:
        execution_role_arn = create_bastion_task_execution_role()

    create_task_definition(task_role_arn, execution_role_arn)
    log_info("Bastion ECS task created")


@cli.command(
    "delete-bastion-task",
    help="Creates the ECS task used to launch the bastion",
)
@click.option(
    "--region",
    help="The aws region where the Fargate task should be created",
    type=click.STRING,
    default=None,
)
def handle_delete_bastion_task(region: str = None):
    delete_task_definition()

    log_info("Deleting bastion task iam roles")
    delete_bastion_task_role()
    delete_bastion_task_execution_role()

    log_info("Bastion task deleted.")


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
@click.option(
    "--region",
    help="The aws region where the Fargate task should be started",
    type=click.STRING,
    default=None,
)
def handle_launch_bastion(
    cluster_name: str,
    subnet_ids: str,
    security_group_ids: str,
    authorized_keys: str,
    bastion_name: str,
    bastion_timeout: int,
    bastion_type: str,
    region: str,
) -> None:
    try:
        bastion_type = BastionType[bastion_type]
    except KeyError:
        raise click.ClickException("bastion-type must be one of `original` or `ssm`")

    launch_fargate_task(
        cluster_name=cluster_name,
        subnet_ids=subnet_ids,
        security_group_ids=security_group_ids,
        authorized_keys=authorized_keys,
        instance_name=bastion_name,
        timeout_minutes=bastion_timeout,
        bastion_type=bastion_type,
    )
    log_info("Bastion task is running")

    public_ips = load_task_public_ips(cluster_name, bastion_name)
    log_info(f"Instance public ip(s): {', '.join(public_ips)}")

    if bastion_type == BastionType.ssm:
        instances = load_instance_ids(bastion_name)
        log_info(f"Instance ssm id(s): {', '.join(instances)}")


@cli.command(
    "list-bastion-instances",
    help="Starts up a serverless bastion in your Fargate cluster",
)
@click.option(
    "--name",
    help="The name bastion instance to filter by",
    type=click.STRING,
)
@click.option(
    "--region",
    help="The aws region where the bastion instance can be found",
    type=click.STRING,
    default=None,
)
def handle_list_bastion_instances(name: str, region: str) -> None:
    instances = load_instance_ids(name)
    log_info(f"Instance ids: {', '.join(instances)}")


def main() -> None:
    cli()
