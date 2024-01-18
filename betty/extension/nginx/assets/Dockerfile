FROM openresty/openresty:alpine

RUN mkdir /betty-lua
COPY content_negotiation.lua /betty-lua/content_negotiation.lua
RUN echo "lua_package_path '/betty-lua/?.lua;;';" > /etc/nginx/conf.d/default.conf
