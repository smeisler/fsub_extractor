# Steps of preparing the Docker images:

# +++++++++++++++++++++++++++++++++++++++
tag_version="0.0.0.9000"
# +++++++++++++++++++++++++++++++++++++++

## build the dockerfile for miniconda
cmd="docker build -t chenyingzhao/fsub_extractor_miniconda:22.4.1 -f Dockerfile_Miniconda ."
echo $cmd
#$cmd

cmd="docker push chenyingzhao/fsub_extractor_miniconda:22.4.1"
echo $cmd
#$cmd

## build the dockerfile for fsub_extractor:
cmd="docker build -t chenyingzhao/fsub_extractor_deps:${tag_version} ."
echo $cmd
$cmd

cmd="docker push chenyingzhao/fsub_extractor_deps:${tag_version}"
echo $cmd
