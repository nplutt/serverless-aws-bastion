TASK_BOOT_TIMEOUT = 100
CLUSTER_PROVISION_TIMEOUT = 60

DEFAULT_NAME = "serverless-aws-bastion"
TASK_ROLE_NAME = f"{DEFAULT_NAME}-task-role"
TASK_EXECUTION_ROLE_NAME = f"{DEFAULT_NAME}-task-execution-role"

TASK_CPU = '256'
TASK_MEMORY = '512'
TASK_DEFINITION = [
    {
        "image": "nplutt/ssm-bastion",
        "name": DEFAULT_NAME,
        "essential": True,
    }
]
