FROM docker.dm-ai.cn/public/ubuntu:16.04-python37-node14

## base environment
#FROM ubuntu:16.04
#RUN apt update
#RUN apt install -y --no-install-recommends software-properties-common
## install Python3
#RUN add-apt-repository -y ppa:deadsnakes/ppa
#RUN apt-get update
#RUN apt install -y --no-install-recommends python3.7 python3-pip
#RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 1
#RUN pip3 install setuptools wheel
## install nodejs and NPM
#ADD ./node_setup_14.x.sh /setup_14.sh
#RUN chmod +x /setup_14.sh
#RUN ./setup_14.sh
#RUN apt install -y --no-install-recommends nodejs

## setup code environment
ADD . /code
WORKDIR /code/demo
RUN npm config set registry https://npm.dm-ai.cn/repository/npm/
RUN npm install
RUN pip3 install rich lark-parser numpy
RUN npm install -g xml-formatter ait-math-pg-tester
RUN cd deps/math-board-tester && npm install
RUN cp deps/ait-math-* deps/math-board-tester/node_modules/ait-math/src
RUN cd deps/math-board-tester/node_modules/ait-math/src && mv ait-math-json2mathml.js json2mathml.js && ./ait-math-fix-runtime.sh
