from setuptools import find_packages, setup


setup(
    name="serverless-aws-bastion",
    version="0.1.0",
    description="Create and manage your serverless bastion",
    author="Nick Plutt",
    author_email="nplutt@gmail.com",
    license="MIT",
    url="https://github.com/nplutt/serverless-aws-bastion",
    project_urls={"Source Code": "https://github.com/nplutt/serverless-aws-bastion/"},
    keywords="serverless aws bastion jump server python ssh",
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.6",
    packages=find_packages(exclude=("tests",)),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "sab = serverless_aws_bastion.cli:main",
            "serverless-aws-bastion =  serverless_aws_bastion.cli:main",
        ],
    },
    install_requires=[
        "attrs==20.3.0",
        "boto3==1.16.28",
        "boto3-stubs[ec2,ecs,iam,ssm,sts]==1.16.28.0",
        "click==8.0.0a1",
        "colorama==0.4.4",
    ],
    extras_require={
        "test": [
            "pytest==6.1.2",
            "pytest-cov==2.10.1",
        ],
        "dev": [
            "add-trailing-comma==2.0.1",
            "mypy==0.790",
            "black==20.8b1",
            "isort==5.6.4",
        ],
    },
)
