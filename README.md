# serverless-aws-bastion

## Development
Installing CLI locally
```bash
python setup.py develop
```

## Feature To Do
- [] Terraform module to create Fargate cluster and task
- [] CLI to manage booting up Fargate task
- [] Scripts to allow SSM SSH into Fargate task
- [] Task timeout functionality
- [] SSM machine cleanup
- [] Basic security group to launch the Task into
- [] Personal vs group bastion functionality

## Notes
Hourly pricing:
* Fargate: 0.25 * 0.04048 + 0.5 * 0.004445 = 0.0123/hr
* SSM: 0.00695/hr
* Total: 0.0192925/hr

For reference a t3.nano is 1/4 the price. 