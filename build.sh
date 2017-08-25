#docker build -t google-assistant-build .
#docker run -v build:/tmp -t google-assistant-build


#IMAGE_ID=$(docker build -t "google-assistant-build". | awk '/Successfully built/{print $NF}')

#docker create --name "google-asssitant-build" $IMAGE_ID
#docker cp google-assistant-build:/opt/dist/ntc-google-assistant ./build/


#docker build -t "google-assistant-build" .
docker run -it "google-assistant-build"
ID=$(docker ps --latest --quiet)
docker cp $ID:/opt/dist/ntc-google-assistant ./build
echo $ID

#docker cp google-assistant-build:/opt/dist/ntc-google-assistant .
#docker exec -i  /bin/bash -c "ls /opt/"

#docker exec -i $IMAGE_ID /bin/bash -c "cat > /opt/dist/ntc-google-assistant" < .

#echo $IMAGE_ID
#docker cp $IMAGE_ID:/opt/dist/ntc-google-assistant ntc-google-assistant

#'cat > /opt/dist/ntc-google-assistant' < ntc-google-assistant
#docker run -it google-assistant-build
#docker run -i $IMAGE_ID
