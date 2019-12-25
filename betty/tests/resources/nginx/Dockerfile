FROM alpine:3
ARG NGINX_VERSION=1.17.6
ARG NGX_DEVEL_KIT_VERSION=0.3.1
ARG OPENRESTY_LUAJIT_VERSION=2.1-20190912
ARG LUA_NGINX_MODULE_VERSION=0.10.15
ARG LUA_RESTY_CORE_VERSION=0.1.17
RUN apk add --no-cache \
        build-base \
        ca-certificates \
        certbot \
        libressl \
        linux-headers \
        luajit \
        pcre \
        zlib && \
    apk add --no-cache --virtual .build-dependencies \
        gcc \
        libressl-dev \
        luajit-dev \
        pcre-dev \
        zlib-dev && \
    mkdir /betty
WORKDIR /betty
RUN wget -O ./nginx.tar.gz "http://nginx.org/download/nginx-$NGINX_VERSION.tar.gz" && \
    tar -xzvf ./nginx.tar.gz && \
    rm ./nginx.tar.gz && \
    wget -O ./ngx_devel_kit.tar.gz "https://github.com/simplresty/ngx_devel_kit/archive/v$NGX_DEVEL_KIT_VERSION.tar.gz"  && \
    tar -xzvf ./ngx_devel_kit.tar.gz  && \
    rm ./ngx_devel_kit.tar.gz  && \
    wget -O ./lua-nginx-module.tar.gz "https://github.com/openresty/lua-nginx-module/archive/v$LUA_NGINX_MODULE_VERSION.tar.gz" && \
    tar -xzvf ./lua-nginx-module.tar.gz && \
    rm ./lua-nginx-module.tar.gz

#RUN ls -la /usr/include
#RUN ls -la /usr/lib/lua

WORKDIR "/betty/nginx-$NGINX_VERSION"
ARG LUAJIT_LIB=/usr/lib
ARG LUAJIT_INC=/usr/include/luajit-2.1/
RUN ./configure \
    --prefix=/etc/nginx \
    --sbin-path=/usr/sbin/nginx \
    --conf-path=/etc/nginx/nginx.conf \
    --pid-path=/var/run/nginx.pid \
    --lock-path=/var/run/nginx.lock \
    --with-ld-opt="-Wl,-rpath,/usr/lib" \
    --add-module="/betty/ngx_devel_kit-$NGX_DEVEL_KIT_VERSION" \
    --add-module="/betty/lua-nginx-module-$LUA_NGINX_MODULE_VERSION" && \
#    --add-module="/betty/lua-resty-core-$LUA_RESTY_CORE_VERSION" && \
    make install && \
    rm -r "/betty/nginx-$NGINX_VERSION" && \
    apk del .build-dependencies
COPY ./nginx.conf /etc/nginx/nginx.conf
CMD ["nginx"]
