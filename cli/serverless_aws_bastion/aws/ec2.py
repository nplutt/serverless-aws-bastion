from typing import List

from mypy_boto3_ec2.client import EC2Client

from serverless_aws_bastion.utils.aws_utils import fetch_boto3_client


def load_public_ips_for_network_interfaces(
    interface_ids: List[str],
) -> List[str]:
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
