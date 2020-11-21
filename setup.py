from setuptools import find_packages, setup


setup(
    name="serverless-aws-bastion",
    version="0.0.1",
    description="Create a serverless bastion in AWS to access your private database instances",
    author="Nick Plutt",
    author_email="nplutt@gmail.com",
    license="MIT",
    url="https://github.com/nplutt/serverless-aws-bastion",
    project_urls={"Source Code": "https://github.com/nplutt/serverless-aws-bastion/"},
    keywords="serverless aws bastion python secure ssh",
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
    install_requires=["boto3", "click"],
    extras_require={
        "test": ["pytest", "pytest-cov"],
        "dev": ["mypy", "black", "isort", "boto3-stubs"],
    },
)
