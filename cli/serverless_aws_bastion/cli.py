import click

from serverless_aws_bastion.aws.ecs import (
    create_fargate_cluster,
    delete_fargate_cluster,
    launch_fargate_task,
)


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
    type=click.STRING,
)
def handle_create_fargate_cluster(cluster_name: str):
    create_fargate_cluster(cluster_name)
    click.secho("Fargate cluster is running", fg="green")


@cli.command(
    "delete-fargate-cluster",
    help="Deletes a give Fargate cluster",
)
@click.option(
    "--cluster-name",
    help="The name of the Fargate cluster",
    type=click.STRING,
)
def handle_delete_fargate_cluster(cluster_name: str):
    delete_fargate_cluster(cluster_name)
    click.secho("Fargate cluster is deleted", fg="green")





@cli.command(
    "start-bastion",
    help="Starts up a serverless bastion in your Fargate cluster",
)
@click.option(
    "--cluster-name",
    help="The name of the Fargate cluster to start the serverless bastion in",
    type=click.STRING,
)
@click.option(
    "--subnet-ids",
    help="A comma separated list of VPC subnet ids to launch the bastion into",
    type=click.STRING,
)
@click.option(
    "--security-group-ids",
    help="A comma separated list of security group ids to launch the bastion into",
    type=click.STRING,
)
@click.option(
    "--authorized-keys",
    help="All of the public keys that the bastion should allow",
    type=click.STRING,
)
@click.option(
    "--region",
    help="The aws region where the Fargate task should be started in",
    type=click.STRING,
    default=None,
)
def handle_launch_bastion(
    cluster_name: str,
    subnet_ids: str,
    security_group_ids: str,
    authorized_keys: str,
    region: str = None,
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
