from serverless_aws_bastion.enums.bastion_type import BastionType


TASK_BOOT_TIMEOUT = 100
CLUSTER_PROVISION_TIMEOUT = 60
TASK_TIMEOUT = 60 * 8

DEFAULT_NAME = "serverless-aws-bastion"
TASK_ROLE_NAME = f"{DEFAULT_NAME}-task-role"
TASK_EXECUTION_ROLE_NAME = f"{DEFAULT_NAME}-task-execution-role"
SSM_DEREGISTER_POLICY_NAME = f"{DEFAULT_NAME}-deregister-ssm"

TASK_CPU = "256"
TASK_MEMORY = "512"
