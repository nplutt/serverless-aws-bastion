from typing import Dict, List, Optional

import attr
from mypy_boto3_ecs.type_defs import TaskTypeDef

from serverless_aws_bastion.utils.aws_utils import get_tag_value


@attr.s(auto_attribs=True)
class InstanceInfo:
    bastion_id: str
    created_at: str
    public_ip: str
    ssm_instance_id: Optional[str]
    instance_name: str
    task_arn: str

    @property
    def as_dict(self) -> dict:
        return attr.asdict(self)


def build_instance_info(
    task_data: List[TaskTypeDef],
    task_ips: Dict[str, str],
    ssm_instance_data: Dict[str, str],
) -> List[InstanceInfo]:
    instance_info = []
    for data in task_data:
        bastion_id = get_tag_value("ecs", data["tags"], "BastionId")
        created_at = get_tag_value("ecs", data["tags"], "CreatedOn")
        activation_id = get_tag_value("ecs", data["tags"], "ActivationId")

        name_tag = get_tag_value("ecs", data["tags"], "Name")
        instance_name = name_tag[name_tag.find("/") + 1 :]

        instance_info.append(
            InstanceInfo(
                task_arn=data["taskArn"],
                bastion_id=bastion_id,
                created_at=created_at,
                instance_name=instance_name,
                public_ip=task_ips[bastion_id],
                ssm_instance_id=ssm_instance_data.get(activation_id, ''),
            ),
        )

    return instance_info
