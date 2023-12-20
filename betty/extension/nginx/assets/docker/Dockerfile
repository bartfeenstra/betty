FROM openresty/openresty:alpine

RUN mkdir /cone
RUN wget -O /cone/cone.lua https://raw.githubusercontent.com/bartfeenstra/cone/master/cone.lua
RUN echo "lua_package_path '/cone/?.lua;;';" > /etc/nginx/conf.d/default.conf
