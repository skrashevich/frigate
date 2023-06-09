# syntax = docker/dockerfile-upstream:master-labs

# https://askubuntu.com/questions/972516/debian-frontend-environment-variable
ARG DEBIAN_FRONTEND=noninteractive

FROM python:3.11-bullseye AS base
ARG DEBIAN_FRONTEND
RUN <<EOT
    apt update --allow-insecure-repositories
    apt install -y --no-install-recommends ca-certificates
    update-ca-certificates
EOT

FROM --platform=linux/amd64 python:3.11-bullseye AS base_amd64
ARG DEBIAN_FRONTEND
RUN <<EOT
    apt update --allow-insecure-repositories
    apt install -y --no-install-recommends ca-certificates
    update-ca-certificates
EOT

FROM python:3.11-slim-bullseye AS slim-base
ARG DEBIAN_FRONTEND
RUN <<EOT
    apt update --allow-insecure-repositories
    apt install -y --no-install-recommends ca-certificates
    update-ca-certificates
EOT

FROM slim-base AS wget
ARG DEBIAN_FRONTEND

RUN <<EOT
    apt update --allow-insecure-repositories
    apt install -y --no-install-recommends ca-certificates xz-utils wget
    update-ca-certificates
EOT

WORKDIR /rootfs

FROM --platform=$BUILDPLATFORM debian:11 AS nginx
ARG DEBIAN_FRONTEND
ARG TARGETARCH

# bind /var/cache/apt to tmpfs to speed up nginx build
RUN --mount=type=tmpfs,target=/tmp  \
    --mount=type=bind,source=docker/build_nginx.sh,target=/deps/build_nginx.sh \
    /deps/build_nginx.sh

FROM --platform=$BUILDPLATFORM wget AS go2rtc
ARG TARGETARCH
WORKDIR /rootfs/usr/local/go2rtc/bin
RUN wget -qO go2rtc "https://github.com/AlexxIT/go2rtc/releases/download/v1.5.0/go2rtc_linux_${TARGETARCH}" \
    && chmod +x go2rtc

FROM --platform=$BUILDPLATFORM node:16 AS docs-build
ADD --link ./docs /docs
ADD --link labelmap.txt /
WORKDIR /docs
RUN sed -i'' "s/baseUrl: '\/',/baseUrl: '\/docs\/',/" ./docusaurus.config.js
RUN npm install
RUN npm run build

####
#
# OpenVino Support
#
# 1. Download and convert a model from Intel's Public Open Model Zoo
# 2. Build libUSB without udev to handle NCS2 enumeration
#
####
# Download and Convert OpenVino model
FROM --platform=$BUILDPLATFORM base_amd64 AS ov-converter
ARG DEBIAN_FRONTEND

# Install OpenVino Runtime and Dev library
ADD requirements-ov.txt /requirements-ov.txt
RUN     apt-get -qq update \
    && apt-get -qq install -y wget python3-distutils \
    && wget -q https://bootstrap.pypa.io/get-pip.py -O get-pip.py \
    && python3 get-pip.py "pip" \
    && pip install -r /requirements-ov.txt

# Get OpenVino Model
RUN   mkdir /models \
    && cd /models && omz_downloader --name ssdlite_mobilenet_v2 \
    && cd /models && omz_converter --name ssdlite_mobilenet_v2 --precision FP16


# libUSB - No Udev
FROM wget as libusb-build
ARG TARGETARCH
ARG DEBIAN_FRONTEND

# Build libUSB without udev.  Needed for Openvino NCS2 support
WORKDIR /opt
RUN apt-get update && apt-get install -y --no-install-recommends unzip build-essential automake libtool
RUN wget -q https://github.com/libusb/libusb/archive/v1.0.25.zip -O v1.0.25.zip && \
    unzip v1.0.25.zip && cd libusb-1.0.25 && \
    ./bootstrap.sh && \
    ./configure --disable-udev --enable-shared && \
    make -j $(nproc --all)
RUN  apt-get update && \
    apt-get install -y --no-install-recommends libusb-1.0-0-dev && \
    apt-get clean
WORKDIR /opt/libusb-1.0.25/libusb
RUN /bin/mkdir -p '/usr/local/lib' && \
    /bin/bash ../libtool  --mode=install /usr/bin/install -c libusb-1.0.la '/usr/local/lib' && \
    /bin/mkdir -p '/usr/local/include/libusb-1.0' && \
    /usr/bin/install -c -m 644 libusb.h '/usr/local/include/libusb-1.0' && \
    /bin/mkdir -p '/usr/local/lib/pkgconfig' && \
    cd  /opt/libusb-1.0.25/ && \
    /usr/bin/install -c -m 644 libusb-1.0.pc '/usr/local/lib/pkgconfig' && \
    ldconfig



FROM --platform=$BUILDPLATFORM wget AS models

# Get model and labels
ADD --link https://github.com/google-coral/test_data/raw/release-frogfish/ssdlite_mobiledet_coco_qat_postprocess_edgetpu.tflite edgetpu_model.tflite
ADD --link https://github.com/google-coral/test_data/raw/release-frogfish/ssdlite_mobiledet_coco_qat_postprocess.tflite cpu_model.tflite 
ADD --link https://raw.githubusercontent.com/google-coral/test_data/master/efficientdet_lite3_512_ptq_edgetpu.tflite /efficientdet_lite3_512_ptq_edgetpu.tflite
ADD --link https://storage.googleapis.com/mediapipe-tasks/object_detector/efficientdet_lite2_fp32.tflite /efficientdet_lite2_fp32.tflite
ADD --link https://raw.githubusercontent.com/google-coral/test_data/master/coco_labels.txt /coco_labels.txt 

ADD labelmap.txt .
# Copy OpenVino model
COPY --link --from=ov-converter /models/public/ssdlite_mobilenet_v2/FP16 openvino-model
ADD https://github.com/openvinotoolkit/open_model_zoo/raw/master/data/dataset_classes/coco_91cl_bkgr.txt openvino-model/coco_91cl_bkgr.txt
RUN sed -i 's/truck/car/g' openvino-model/coco_91cl_bkgr.txt



FROM --platform=$BUILDPLATFORM wget AS s6-overlay
ARG TARGETARCH
RUN --mount=type=bind,source=docker/install_s6_overlay.sh,target=/deps/install_s6_overlay.sh \
    /deps/install_s6_overlay.sh


FROM base AS wheels
ARG DEBIAN_FRONTEND
ARG TARGETARCH

# Use a separate container to build wheels to prevent build dependencies in final image
RUN apt-get -qq update \
    && apt-get -qq install -y --no-install-recommends \
    apt-transport-https \
    gnupg \
    wget \
    && apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 9165938D90FDDD2E \
    && echo "deb http://raspbian.raspberrypi.org/raspbian/ bullseye main contrib non-free rpi" | tee /etc/apt/sources.list.d/raspi.list \
    && apt-get -qq update \
    && apt-get -qq install -y --no-install-recommends \
    python3-dev \
    wget \
    # opencv dependencies
    build-essential cmake git pkg-config libgtk-3-dev \
    libavcodec-dev libavformat-dev libswscale-dev libv4l-dev \
    libxvidcore-dev libx264-dev libjpeg-dev libpng-dev libtiff-dev \
    gfortran openexr libatlas-base-dev libssl-dev\
    libtbb2 libtbb-dev libdc1394-22-dev libopenexr-dev \
    libgstreamer-plugins-base1.0-dev libgstreamer1.0-dev \
    libgl1 \
    # scipy dependencies
    gcc gfortran libopenblas-dev liblapack-dev \
    # mediapipe dependencies
    protobuf-compiler && \
    apt-get clean

RUN wget -q https://bootstrap.pypa.io/get-pip.py -O get-pip.py \
    && python3 get-pip.py "pip"

COPY requirements.txt /requirements.txt
RUN pip3 install -r requirements.txt

ADD requirements-wheels.txt /requirements-wheels.txt
RUN pip3 wheel --wheel-dir=/wheels -r requirements-wheels.txt

# Make this a separate target so it can be built/cached optionally
FROM wheels as trt-wheels
ARG DEBIAN_FRONTEND
ARG TARGETARCH

# Add TensorRT wheels to another folder
ADD requirements-tensorrt.txt /requirements-tensorrt.txt
RUN mkdir -p /trt-wheels && pip3 wheel --wheel-dir=/trt-wheels -r requirements-tensorrt.txt


# Collect deps in a single layer
FROM --platform=$BUILDPLATFORM scratch AS deps-rootfs
COPY --link --from=nginx /usr/local/nginx/ /usr/local/nginx/
COPY --link --from=skrashevich/go2rtc:master /usr/local/bin/go2rtc /usr/local/go2rtc/bin/go2rtc
COPY --link --from=s6-overlay /rootfs/ /
COPY --link --from=models /rootfs/ /
ADD docker/rootfs/ /


# Frigate deps (ffmpeg, python, nginx, go2rtc, s6-overlay, etc)
FROM slim-base AS deps
ARG TARGETARCH

ARG DEBIAN_FRONTEND
# http://stackoverflow.com/questions/48162574/ddg#49462622
ARG APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=DontWarn

# https://github.com/NVIDIA/nvidia-docker/wiki/Installation-(Native-GPU-Support)
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES="compute,video,utility"

ENV PATH="/usr/lib/btbn-ffmpeg/bin:/usr/local/go2rtc/bin:/usr/local/nginx/sbin:${PATH}"

# Install dependencies

RUN  --mount=type=bind,source=docker/install_deps.sh,target=/deps/install_deps.sh \
    /deps/install_deps.sh

RUN  --mount=type=bind,from=wheels,source=/wheels,target=/deps/wheels \
    pip3 install -U /deps/wheels/*.whl

COPY --link --from=deps-rootfs / /
#ADD --link docker/ffmpeg /usr/lib/btbn-ffmpeg/bin/ffmpeg
#ADD --link docker/ffprobe /usr/lib/btbn-ffmpeg/bin/ffprobe
#COPY --from=skrashevich/ffmpeg:linux64-nonfree-shared-5.1 /app /usr/lib/btbn-ffmpeg

RUN ldconfig; true

EXPOSE 5000
EXPOSE 1935
EXPOSE 8554
EXPOSE 8555/tcp 8555/udp

# Configure logging to prepend timestamps, log to stdout, keep 0 archives and rotate on 10MB
ENV S6_LOGGING_SCRIPT="T 1 n0 s10000000 T"

ENTRYPOINT ["/init"]
CMD []

# Frigate deps with Node.js and NPM for devcontainer
FROM deps AS devcontainer

# Do not start the actual Frigate service on devcontainer as it will be started by VSCode
# But start a fake service for simulating the logs
ADD docker/fake_frigate_run /etc/s6-overlay/s6-rc.d/frigate/run

# Create symbolic link to the frigate source code, as go2rtc's create_config.sh uses it
RUN mkdir -p /opt/frigate \
    && ln -svf /workspace/frigate/frigate /opt/frigate/frigate

# Install Node 16
RUN  apt-get update \
    && apt-get install --no-install-recommends wget -y \
    && wget -qO- https://deb.nodesource.com/setup_16.x | bash - \
    && apt-get install -y --no-install-recommends nodejs  \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g npm@9

WORKDIR /workspace/frigate

RUN  apt-get update \
    && apt-get install --no-install-recommends make -y \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=bind,source=./requirements-dev.txt,target=/workspace/frigate/requirements-dev.txt \
    pip3 install -r requirements-dev.txt

CMD ["sleep", "infinity"]


# Frigate web build
# This should be architecture agnostic, so speed up the build on multiarch by not using QEMU.
FROM --platform=$BUILDPLATFORM node:16 AS web-build

WORKDIR /work
ADD web/package.json web/package-lock.json ./
RUN npm install

ADD web/ ./
RUN npm run build \
    && mv dist/BASE_PATH/monacoeditorwork/* dist/assets/ \
    && rm -rf dist/BASE_PATH
RUN wget https://gobinaries.com/tj/node-prune --output-document - | /bin/sh && node-prune

# Collect final files in a single layer
FROM --platform=$BUILDPLATFORM scratch AS rootfs

WORKDIR /opt/frigate/
ADD frigate frigate/
ADD migrations migrations/
COPY --link --from=web-build /work/dist/ web/
COPY --link --from=docs-build /docs/build/ web/docs/

# Frigate final container
FROM deps AS frigate

WORKDIR /opt/frigate/
COPY --link --from=rootfs / /

# Frigate w/ TensorRT Support as separate image
FROM frigate AS frigate-tensorrt
COPY --link --from=libusb-build /usr/local/lib /usr/local/lib
RUN --mount=type=bind,from=trt-wheels,source=/trt-wheels,target=/deps/trt-wheels \
    pip3 install -U /deps/trt-wheels/*.whl && \
    ln -s libnvrtc.so.11.7 /usr/local/lib/python3.11/dist-packages/nvidia/cuda_nvrtc/lib/libnvrtc.so && \
    ldconfig

# Dev Container w/ TRT
FROM devcontainer AS devcontainer-trt

RUN --mount=type=bind,from=trt-wheels,source=/trt-wheels,target=/deps/trt-wheels \
    pip3 install -U /deps/trt-wheels/*.whl
