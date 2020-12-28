from datetime import datetime
from typing import Any, Dict, List, Optional

import boto3
import click
from botocore.config import Config
from click.exceptions import Abort
from mypy_boto3_sts.client import STSClient

from serverless_aws_bastion.utils.click_utils import log_error


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


def load_aws_account_id() -> str:
    """
    Uses boto3 to load the current account id
    """
    client: STSClient = fetch_boto3_client("sts")
    return client.get_caller_identity()["Account"]


def capitalize_tag_kv(service: str) -> bool:
    """
    Returns true or false depending on if the boto3 service
    name needs the key & value values capitalized
    """
    return service in ("ec2", "iam", "ssm")


def build_tags(service: str, extra_tags: dict = None) -> List[Any]:
    tags = {
        "CreatedBy": "serverless-aws-bastion:cli",
        "CreatedOn": str(datetime.utcnow()),
    }
    if extra_tags:
        tags.update(extra_tags)

    capitalize = capitalize_tag_kv(service)
    return [
        {
            f"{'K' if capitalize else 'k'}ey": key,
            f"{'V' if capitalize else 'v'}alue": value,
        }
        for key, value in tags.items()
    ]


def get_tag_value(
    service: str,
    tags: List[Any],
    tag_key: str,
) -> str:
    """
    Given a list of tags in key value format, returns a matching
    tag value if one is found.
    """
    capitalize = capitalize_tag_kv(service)
    matches = [
        t[f"{'V' if capitalize else 'v'}alue"]
        for t in tags
        if t[f"{'K' if capitalize else 'k'}ey"] == tag_key
    ]
    if len(matches) != 1:
        log_error(
            f"Oops it looks like we're unable to find a match for tag {tag_key}."
            "Please open an issue to help us get this fixed!",
        )
        raise Abort()

    return matches[0]
