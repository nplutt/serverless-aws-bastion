from typing import List

from mypy_boto3_ec2.client import EC2Client
from mypy_boto3_ecs.type_defs import TaskTypeDef

from serverless_aws_bastion.utils.aws_utils import fetch_boto3_client


def load_public_ips_from_task_data(task_data: List[TaskTypeDef]) -> List[str]:
    attachments = [
        a
        for t in task_data
        for a in t["attachments"]
    ]
    network_interface_ids = [
        detail["value"]
        for a in attachments
        for detail in a["details"]
        if detail["name"] == "networkInterfaceId"
    ]
    return load_public_ips_for_network_interfaces(network_interface_ids)


def load_public_ips_for_network_interfaces(
    interface_ids: List[str],
) -> List[str]:
    """
    Loads the public ip addresses for a list of network
    interface ids
    """
    client: EC2Client = fetch_boto3_client("ec2")
    interfaces = client.describe_network_interfaces(
        NetworkInterfaceIds=interface_ids,
    )

    public_ips = []
    for interface in interfaces["NetworkInterfaces"]:
        try:
            public_ips.append(interface["Association"]["PublicIp"])
        except KeyError:
            pass

    return public_ips
