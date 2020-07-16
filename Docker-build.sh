IMAGE_NAME="mathsteps-v2"

docker rm $(docker ps -a -q)
docker ps --all

docker image rm ${IMAGE_NAME}
docker images

docker build --network host --tag ${IMAGE_NAME} .

echo "==== USE COMMANDS BELOW TO MODIFY ===="
echo docker run --network host -it ${IMAGE_NAME} /bin/bash
echo docker commit d46b7a389162 ${IMAGE_NAME}