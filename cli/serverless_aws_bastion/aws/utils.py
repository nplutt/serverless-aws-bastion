from datetime import datetime
from typing import Any, Dict, List

import boto3
import click
from botocore.config import Config


CLIENT_CACHE: Dict[str, Any] = {}


def fetch_boto3_client(service_name: str):
    """
    Takes a service name & region and returns a boto3 client for
    the given service.
    """
    region_name = load_aws_region_name()
    cache_key = f"{region_name}-{service_name}"

    if CLIENT_CACHE.get(cache_key):
        return CLIENT_CACHE[cache_key]

    config = Config(
        region_name=region_name,
        signature_version="v4",
        retries={"max_attempts": 10, "mode": "standard"},
    )
    client = boto3.client(service_name, config=config)  # type: ignore

    CLIENT_CACHE[cache_key] = client

    return client


def load_aws_region_name() -> str:
    """
    Uses boto3 to load the current region set in the aws cli config
    """
    session = boto3.session.Session()
    region_name = (
        click.get_current_context().params.get("region") or session.region_name
    )
    return region_name


def get_default_tags() -> List[Dict[str, str]]:
    tags = {
        "CreatedBy": "serverless-aws-bastion:cli",
        "CreatedOn": str(datetime.utcnow()),
    }
    return [
        {
            "key": key,
            "value": value,
        }
        for key, value in tags.items()
    ]