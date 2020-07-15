FROM ubuntu:16.04
RUN apt update
RUN apt install -y --no-install-recommends curl sudo python3
RUN curl -sL https://deb.nodesource.com/setup_14.x | sudo -E bash -
RUN apt install -y --no-install-recommends nodejs npm

ADD . ./code
WORKDIR ./code/demo
RUN npm config set registry https://npm.dm-ai.cn/repository/npm/
RUN npm install
