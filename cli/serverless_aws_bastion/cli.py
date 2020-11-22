import click

from serverless_aws_bastion.aws.ecs import launch_fargate_task


@click.group()
def cli():
    pass


@cli.command(
    "start-bastion", help="Starts up a serverless bastion in your Fargate cluster"
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
def launch_bastion(
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
