FROM ubuntu:16.04
RUN apt update
RUN apt install -y --no-install-recommends curl sudo python3
RUN curl -sL https://deb.nodesource.com/setup_14.x | sudo -E bash -
RUN apt install -y --no-install-recommends nodejs npm

RUN useradd -ms /bin/bash dm
USER dm

ADD --chown=dm:dm . /home/dm/code
WORKDIR /home/dm

WORKDIR /home/dm/code/demo
RUN npm config set registry https://npm.dm-ai.cn/repository/npm/
RUN npm install
RUN echo hello
