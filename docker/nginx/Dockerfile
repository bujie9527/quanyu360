FROM nginx:1.27-alpine

RUN addgroup -S nginxapp && adduser -S -G nginxapp nginxapp

COPY docker/nginx/nginx.conf /etc/nginx/nginx.conf

EXPOSE 8080

USER nginxapp
