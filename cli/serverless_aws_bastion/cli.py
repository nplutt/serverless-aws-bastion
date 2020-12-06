import click
from serverless_aws_bastion.aws.ecs import create_fargate_cluster
from serverless_aws_bastion.aws.ecs import create_task_definition
from serverless_aws_bastion.aws.ecs import delete_fargate_cluster
from serverless_aws_bastion.aws.ecs import launch_fargate_task
from serverless_aws_bastion.aws.iam import create_bastion_task_execution_role
from serverless_aws_bastion.aws.iam import create_bastion_task_role


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
    click.secho("Fargate cluster running", fg="green")


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
    click.secho("Fargate cluster deleted", fg="green")


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
    click.secho("Bastion ECS task created", fg="green")


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
    help=
    "A comma separated list of security group ids to launch the bastion into",
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
        region: str,
) -> None:
    launch_fargate_task(
        cluster_name=cluster_name,
        subnet_ids=subnet_ids,
        security_group_ids=security_group_ids,
        authorized_keys=authorized_keys,
    )
    click.secho("Task is running", fg="green")


def main() -> None:
    cli()
