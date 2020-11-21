FROM amazonlinux:2

MAINTAINER Nick Plutt <nplutt@gmail.com>

RUN yum update -y
RUN yum install -y https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm
RUN yum install -y python shadow-utils
RUN yum clean all

RUN rm -rf /var/cache/yum
RUN mv /etc/amazon/ssm/seelog.xml.template /etc/amazon/ssm/seelog.xml

COPY files/systemctl.py /usr/bin/systemctl
COPY files/entrypoint.sh /usr/local/bin/

RUN adduser ssm-user
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT [ "entrypoint.sh" ]
CMD [ "systemctl", "start", "amazon-ssm-agent" ]