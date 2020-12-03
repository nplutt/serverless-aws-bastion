FROM golang:1.12-alpine as builder
ARG VERSION=2.3.930.0

RUN set -ex && apk add --no-cache make git gcc libc-dev curl bash && \
    curl -sLO https://github.com/aws/amazon-ssm-agent/archive/${VERSION}.tar.gz && \
    mkdir -p /go/src/github.com && \
    tar xzf ${VERSION}.tar.gz && \
    mv amazon-ssm-agent-${VERSION} /go/src/github.com/amazon-ssm-agent && \
    cd /go/src/github.com/amazon-ssm-agent && \
    echo ${VERSION} > VERSION && \
    gofmt -w agent && make checkstyle || ./Tools/bin/goimports -w agent && \
    make build-linux

FROM alpine
RUN set -ex && apk add --no-cache sudo ca-certificates && \
    adduser -D ssm-user && echo "ssm-user ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/ssm-agent-users && \
    mkdir -p /etc/amazon/ssm


COPY --from=builder /go/src/github.com/amazon-ssm-agent/bin/linux_amd64/ /usr/bin
COPY --from=builder /go/src/github.com/amazon-ssm-agent/bin/amazon-ssm-agent.json.template /etc/amazon/ssm/amazon-ssm-agent.json
COPY --from=builder /go/src/github.com/amazon-ssm-agent/bin/seelog_unix.xml /etc/amazon/ssm/seelog.xml

RUN apk add --no-cache openssh autossh
RUN ssh-keygen -t rsa -b 1024 -N "" -f /etc/ssh/ssh_host_rsa_key
RUN ssh-keygen -t dsa -b 1024 -N "" -f /etc/ssh/ssh_host_dsa_key
RUN ssh-keygen -t ecdsa -b 521 -N "" -f /etc/ssh/ssh_host_ecdsa_key
RUN ssh-keygen -t ed25519 -b 512 -N "" -f /etc/ssh/ssh_host_ed25519_key
RUN mkdir -p /home/ssm-user/.ssh
ADD docker_files/sshd_config /etc/ssh/

RUN apk add --no-cache python3 py3-pip bash dumb-init
RUN pip3 install --upgrade pip
RUN pip3 install awscli
RUN aws --version

RUN rm -rf /tmp/* /var/cache/apk/*

ADD docker_files/boot.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/boot.sh

EXPOSE 22

CMD ["dumb-init", "/bin/bash", "/usr/local/bin/boot.sh"]