FROM ubuntu:16.04
RUN apt update
RUN apt install -y --no-install-recommends curl sudo iproute2
RUN curl -sL https://deb.nodesource.com/setup_14.x | sudo -E bash -
RUN apt install -y --no-install-recommends python3 nodejs npm

ADD . ./code
WORKDIR ./code/demo
RUN npm config set registry https://npm.dm-ai.cn/repository/npm/
#RUN npm install
