from typing import Any, List, Optional

import attr
from mypy_boto3_ecs.type_defs import TaskTypeDef

from serverless_aws_bastion.aws.ec2 import load_public_ips_from_task_data
from serverless_aws_bastion.utils.aws_utils import get_tag_values


@attr.s
class InstanceInfo:
    task_arn: str
    bastion_id: str
    public_ip: str
    instance_name: str
    ssm_instance_id: Optional[str]

    @classmethod
    def from_stuff(
        cls,
        task_data: List[TaskTypeDef],
        ssm_data: List[Any],
    ) -> List["InstanceInfo"]:
        return [
            cls(
                task_arn=data["taskArn"],
                bastion_id=get_tag_values(data["tags"], "BastionId")[0],
                instance_name=get_tag_values(data["tags"], "Name")[0],
                public_ip=load_public_ips_from_task_data([data])[0],
                ssm_instance_id="",
            )
            for data in task_data
        ]
