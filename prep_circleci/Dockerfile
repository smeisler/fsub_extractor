# This Dockerfile is for CircleCI tests of this python package. Below we install necessary dependent packages.
# This Dockerfile is NOT for building the docker image of this python package.

# ref: https://github.com/PennLINC/qsiprep_build/blob/main/setup_build.sh
# ref: https://github.com/PennLINC/qsiprep_build/blob/main/Dockerfile

FROM pennbbl/qsiprep-mrtrix3:22.1.0 as build_mrtrix3
FROM chenyingzhao/fsub_extractor_miniconda:22.4.1 as build_miniconda

## MRtrix3
COPY --from=build_mrtrix3 /opt/mrtrix3-latest /opt/mrtrix3-latest
ENV PATH="$PATH:/opt/mrtrix3-latest/bin" \
    MRTRIX3_DEPS="bzip2 ca-certificates curl libpng16-16 libblas3 liblapack3"

## Python, compiled dependencies
COPY --from=build_miniconda /usr/local/miniconda /usr/local/miniconda
COPY --from=build_miniconda /home/qsiprep/.dipy /home/qsiprep/.dipy
ENV PATH="/usr/local/miniconda/bin:$PATH"


## Install deps:
RUN apt-get update \
    && apt install -y --no-install-recommends \
    ${MRTRIX3_DEPS}

## Install fury:
RUN conda install -c conda-forge fury

## Install antspy:
# RUN pip install antspyx   # is this correct ????????????