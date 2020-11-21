import boto3
from typing import Optional


client = boto3.client('ecs')


def create_cluster(
    name: Optional[str],
    tags: Optional[dict],
) -> None:
    """
    Creates Fargate cluster to launch bastion instances into
    """
    client.create_cluster()


