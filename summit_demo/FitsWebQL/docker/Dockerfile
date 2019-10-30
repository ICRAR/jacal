# Start with Ubuntu 18.04 LTS

FROM ubuntu:18.04

RUN apt-get update && \
    apt-get install --yes apt-utils
RUN apt-get install --yes build-essential libglib2.0-dev libjpeg-dev libbsd-dev libx264-dev cmake yasm wget git \
    unzip libssl-dev zlib1g-dev clang libpng-dev

RUN mkdir -p /tmp/ispc
WORKDIR /tmp/ispc
RUN wget -nv https://sourceforge.net/projects/ispcmirror/files/v1.10.0/ispc-v1.10.0-linux.tar.gz

RUN tar -xvf ispc-v1.10.0-linux.tar.gz
RUN cp ispc-1.10.0-Linux/bin/ispc /usr/bin

WORKDIR /tmp
RUN wget -nv https://ftpmirror.gnu.org/libmicrohttpd/libmicrohttpd-latest.tar.gz
RUN tar -xvf libmicrohttpd-latest.tar.gz

WORKDIR /tmp/libmicrohttpd-0.9.62
RUN ./configure
RUN make
RUN make install

WORKDIR /tmp
RUN git clone --recursive https://github.com/uNetworking/uWebSockets.git

WORKDIR /tmp/uWebSockets
RUN make

WORKDIR /tmp
RUN wget -nv https://github.com/jemalloc/jemalloc/releases/download/5.1.0/jemalloc-5.1.0.tar.bz2
RUN tar -xvf jemalloc-5.1.0.tar.bz2

WORKDIR /tmp/jemalloc-5.1.0
RUN ./configure
RUN make
RUN make install

WORKDIR /tmp
RUN wget -nv https://bellard.org/bpg/libbpg-0.9.8.tar.gz
RUN tar -xvf libbpg-0.9.8.tar.gz

WORKDIR /tmp/libbpg-0.9.8
RUN sed -i '/^USE_BPGVIEW/s/^/#/' Makefile
RUN make
RUN make install

RUN apt-get install --yes libcurl4-openssl-dev libnuma-dev libsqlite3-dev
WORKDIR /tmp
RUN wget -nv http://jvo.nao.ac.jp/~chris/fitswebql-1.1.14.tar.gz
RUN tar -xvf fitswebql-1.1.14.tar.gz

WORKDIR FITSWebQL
RUN (export HOME=/tmp && make local)