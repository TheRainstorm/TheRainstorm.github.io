---
title: 使用 docker 配置 hexo 博客环境
date: 2022-05-24 22:19:21
tags:
- docker
- hexo
categories:
- 折腾记录
---

由于 nodejs 版本较多，直接在宿主机上安装 nodejs 环境不容易管理。因此可以使用 docker 维护一个专门用于 hexo 的环境。

<!-- more -->

## hexo 直接安装

教程：<https://hexo.io/zh-cn/docs/index.html>

首先需要安装 node.js 和 git，然后安装 hexo

```
npm install -g hexo-cli
```

常用 hexo 命令

```
#建站
hexo init
npm install     #init后需要使用npm安装hexo所需依赖

hexo new [layout] <title>

hexo clean      #删除public目录(生成的html)
hexo s -p PORT #运行server，对markdown的修改会实时反应
hexo g      #生成html
hexo d      #部署，或hexo d -g
```

## docker 安装

主要过程：

1. 使用 Dockerfile，基于 node 基镜像，创建含 hexo 的镜像
2. 运行该镜像，将 blog 目录映射到 docker 容器中，然后进行 hexo 操作
3. [可选]为了避免部署时输入 github 密码，可以将.ssh 目录映射到容器中

### dockerfile

说明

- 参考的 dockerfile：[使用 docker 搭建 Hexo - wanf3ng's blog](https://wanf3ng.github.io/2021/01/29/使用docker搭建Hexo/)

- 设置用户问题：[在 docker 中執行 hexo | Plusku@blog](https://blog.plusku.net/2020/08/08/docker-hexo/)
  - 默认了用户 uid=1000。因此可以直接指定 User node 来避免容器内生成的文件为 root 所有问题。

- 添加了 git 设置

- 使用 node12.0，否则 hexo 运行会报错

```
FROM node:12.6.0-alpine

# 切换中科大源
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories
# 安装bash git openssh
RUN apk add bash git openssh

# 设置容器时区为上海
RUN apk add tzdata && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
&& echo "Asia/Shanghai" > /etc/timezone \
&& apk del tzdata

# 安装hexo
RUN \ 
npm config set registry https://registry.npm.taobao.org \
&&npm install \
&&npm install hexo-cli -g \
&& npm install hexo-server --save \
&& npm install hexo-asset-image --save \
&& npm install hexo-wordcount --save \
&& npm install hexo-generator-sitemap --save \
&& npm install hexo-generator-baidu-sitemap --save \
&& npm install hexo-deployer-git --save

ARG GIT_NAME
ARG GIT_EMAIL

User node

# 设置git push时的用户名和邮箱
RUN \
 git config --global user.email "$GIT_EMAIL" \
 && git config --global user.name "$GIT_NAME"

WORKDIR /home/node/blog

EXPOSE 4000

ENTRYPOINT ["/bin/bash"]
```

##### build 镜像

```
docker build -t yfy/hexo-blog\
 --build-arg GIT_NAME="Fuyan Yuan"\
 --build-arg GIT_EMAIL="33221728+TheRainstorm@users.noreply.github.com"\
 .
```

##### 运行

```
docker run -it --name hexo-blog\
 -p 4000:4000 \
 -v /home/yfy/Documents/hexo-blog:/home/node/blog/ \
 -v /home/yfy/.ssh:/home/node/.ssh\
 yfy/hexo-blog
```

如果 blog 下没有 node_modules，则需要

```
npm install
```

之后正常使用 hexo 即可

> docker 技巧：连接到已有容器。
>
> ```
> docker attach CONTAINER
> docker exec -it CONTAINER CMD
> ```
>
> `attach`命令将终端的标准输入，标准输出，标准错误连接到正在运行的容器。如果容器正在运行的命令是 bash，则 exit 后，容器退出
>
> `exec`命令在容器内启动新的进程。常见如 bash
