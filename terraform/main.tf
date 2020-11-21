data "aws_caller_identity" "current" {}

resource "aws_ecs_cluster" "ssh_cluster" {
  name = "ssh-cluster"
}

resource "aws_ecs_task_definition" "ssh_task" {
  family = "ssh-task"

  network_mode = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu = 256
  memory = 512

  task_role_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/ecsTaskExecutionRole"
  execution_role_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/ecsTaskExecutionRole"
  container_definitions =  file("task.json")
}