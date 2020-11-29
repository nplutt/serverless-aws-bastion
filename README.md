# serverless-aws-bastion

## Development
Installing CLI locally
```bash
python setup.py develop
```

## Feature To Do
- [x] CLI to manage booting up Fargate task
- [x] CLI for creating bastion stack (cluster, task, iam)
- [] CLI to destroy bastion stack (cluster, task, iam)
- [] SSH functionality via SSM
- [] Task timeout functionality
- [] CLI for machine cleanup on SSM side
- [] CLI to create security group to launch task into
- [] Scripts to allow SSM SSH into Fargate task
- [] Personal vs group bastion functionality

## Notes
Hourly pricing:
* Fargate: 0.25 * 0.04048 + 0.5 * 0.004445 = 0.0123/hr
* SSM: 0.00695/hr
* Total: 0.0192925/hr

For reference a t3.nano is 1/4 the price. 