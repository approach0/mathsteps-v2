IMAGE_NAME="mathsteps-v2"

docker rm $(docker ps --all -q --filter ancestor="${IMAGE_NAME}")
docker ps --all

docker image rm ${IMAGE_NAME}
docker images

docker build --network host --tag ${IMAGE_NAME} .

echo "==== Use commands below to run or modify ===="
echo docker run --network host -it ${IMAGE_NAME} /usr/bin/node daemon.js
echo docker run --network host -it ${IMAGE_NAME} /bin/bash
echo docker commit d46b7a389162 ${IMAGE_NAME}
