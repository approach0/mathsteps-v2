# base
FROM ubuntu:16.04
RUN apt update
# install Python3
RUN apt install -y --no-install-recommends python3
# install nodejs and NPM
ADD ./node_setup_14.x.sh /setup_14.sh
RUN chmod +x /setup_14.sh
RUN ./setup_14.sh
RUN apt install -y --no-install-recommends nodejs
# setup code environment
ADD . /code
WORKDIR /code/demo
RUN npm config set registry https://npm.dm-ai.cn/repository/npm/
#RUN npm install
