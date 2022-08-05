# Steps of preparing the Docker images:

# +++++++++++++++++++++++++++++++++++++++
tag_version="0.0.0.9000"
# +++++++++++++++++++++++++++++++++++++++


## build the dockerfile for fsub_extractor:
cmd="docker build -t chenyingzhao/fsub_extractor_deps:${tag_version} -f Dockerfile_4circleci ."
echo $cmd
#$cmd

cmd="docker push chenyingzhao/fsub_extractor_deps:${tag_version}"
echo $cmd
$cmd
