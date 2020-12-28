from enum import Enum


class ClusterStatus(Enum):
    ACTIVE = "ACTIVE"
    PROVISIONING = "PROVISIONING"
    DEPROVISIONING = "DEPROVISIONING"
    FAILED = "FAILED"
    INACTIVE = "INACTIVE"
