FROM alpine:2.22.4
RUN mkdir -p /workspace
WORKDIR /workspace

COPY . /workspace
RUN sed -i 's#https\?://dl-cdn.alpinelinux.org/alpine#https://mirrors.tuna.tsinghua.edu.cn/alpine#g' /etc/apk/repositories && \
    apk update && \
    apk add python3 py3-paste py3-waitress py3-prettytable py3-requests py3-flask py3-ujson && \
    apk cache clean --purge && \
    mkdir -p /workspace/static

EXPOSE 30000
CMD ["/usr/bin/python3", "/workspace/main.py"]
