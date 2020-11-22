from typing import Any, Dict

import boto3
import click
from botocore.config import Config


CLIENT_CACHE: Dict[str, Any] = {}


def fetch_boto3_client(service_name: str):
    """
    Takes a service name & region and returns a boto3 client for
    the given service.
    """
    region_name = (
        click.get_current_context().params.get("region") or _load_current_region_name()
    )
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


def _load_current_region_name() -> str:
    """
    Uses boto3 to load the current region set in the aws cli config
    """
    session = boto3.session.Session()
    return session.region_name
