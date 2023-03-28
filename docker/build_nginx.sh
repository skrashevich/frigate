#!/bin/bash

set -euxo pipefail

NGINX_VERSION="1.23.3"
VOD_MODULE_VERSION="1.31"
SECURE_TOKEN_MODULE_VERSION="openssl3-hmac-deprecation.zip" #1.5
RTMP_MODULE_VERSION="master" #1.2.2-r1

cp /etc/apt/sources.list /etc/apt/sources.list.d/sources-src.list
sed -i 's|deb http|deb-src http|g' /etc/apt/sources.list.d/sources-src.list
apt-get update

apt-get -yqq build-dep nginx

apt-get -yqq install --no-install-recommends ca-certificates wget
update-ca-certificates -f
mkdir /tmp/nginx
cd /tmp
wget -nv https://nginx.org/download/nginx-${NGINX_VERSION}.tar.gz
tar -zxf nginx-${NGINX_VERSION}.tar.gz -C /tmp/nginx --strip-components=1
rm nginx-${NGINX_VERSION}.tar.gz
mkdir /tmp/nginx-vod-module
wget -nv https://github.com/comrat/nginx-vod-module/archive/refs/tags/${VOD_MODULE_VERSION}.tar.gz
tar -zxf ${VOD_MODULE_VERSION}.tar.gz -C /tmp/nginx-vod-module --strip-components=1
rm ${VOD_MODULE_VERSION}.tar.gz
    # Patch MAX_CLIPS to allow more clips to be added than the default 128
sed -i 's/MAX_CLIPS (128)/MAX_CLIPS (1080)/g' /tmp/nginx-vod-module/vod/media_set.h
patch -d /tmp/nginx-vod-module/ -p1 << 'EOF'
--- a/vod/avc_hevc_parser.c       2022-06-27 11:38:10.000000000 +0000
+++ b/vod/avc_hevc_parser.c       2023-01-16 11:25:10.900521298 +0000
@@ -3,6 +3,9 @@
 bool_t
 avc_hevc_parser_rbsp_trailing_bits(bit_reader_state_t* reader)
 {
+	// https://github.com/blakeblackshear/frigate/issues/4572
+	return TRUE;
+
 	uint32_t one_bit;

 	if (reader->stream.eof_reached)
EOF


mkdir /tmp/nginx-secure-token-module
wget https://github.com/kaltura/nginx-secure-token-module/archive/refs/heads/${SECURE_TOKEN_MODULE_VERSION}.zip
tar -zxf ${SECURE_TOKEN_MODULE_VERSION}.zip -C /tmp/nginx-secure-token-module --strip-components=1
rm ${SECURE_TOKEN_MODULE_VERSION}.zip
mkdir /tmp/nginx-rtmp-module
wget -nv https://github.com/mannyamorim/nginx-rtmp-module/archive/refs/heads/${RTMP_MODULE_VERSION}.zip
tar -zxf ${RTMP_MODULE_VERSION}.zip -C /tmp/nginx-rtmp-module --strip-components=1
rm ${RTMP_MODULE_VERSION}.zip

cd /tmp/nginx

./configure --prefix=/usr/local/nginx \
    --with-file-aio \
    --with-http_sub_module \
    --with-http_ssl_module \
    --with-threads \
    --add-module=../nginx-vod-module \
    --add-module=../nginx-secure-token-module \
    --add-module=../nginx-rtmp-module \
    --with-cc-opt="-O3 -Wno-error=implicit-fallthrough"

make -j$(nproc) && make install
rm -rf /usr/local/nginx/html /usr/local/nginx/conf/*.default
