---
title: docker
date: 2024-01-08 16:16:56
tags:
  - docker
categories:
  - 软件工具
---

记录 docker 的使用，包含 docker 常用命令和 Dockerfile 的编写。目前已经成功使用 dockerfile 发布了第一个应用[`rzero/pal`](https://hub.docker.com/repository/docker/rzero/pal/general)

<!-- more -->
## 安装

ubuntu: [Install Docker Engine on Ubuntu | Docker Docs](https://docs.docker.com/engine/install/ubuntu/#prerequisites)

debian: [Debian | Docker Docs](https://docs.docker.com/engine/install/debian/)

| 特性       | ~/.docker/config.json          | ~/.config/docker/daemon.json           |
| :------- | :----------------------------- | :------------------------------------- |
| **核心组件** | **Client** (命令行工具)             | **Daemon** (后台引擎)                      |
| **主要功能** | 告诉 Docker **你是谁** (Login Auth) | 告诉 Docker **怎么运行** (Storage, Net, Log) |
| **修改生效** | 立即生效 (下次敲命令时)                  | **通常需重启 Docker 服务**                    |
| **典型场景** | `docker login` 自动生成；配置 CLI 快捷键 | 配置国内镜像源；修改容器日志大小限制                     |
| **代理设置** | 影响 `docker build` 时的网络环境（部分）   | 影响 `docker pull` 拉取镜像时的网络环境            |

## docker 命令行

### container 相关

docker run

- `-it`：交互式
- `-d`：启动后进入后台
- `--rm`：运行后删除
- `--name`
- `-p`：映射端口，多个端口重复多次-p
- `-v src:dst`：bind mount

删除容器，`-f`用于删除正在运行的容器

```bash
docker rm container
```

查看容器输出，`-f`跟踪输出

```
docker logs container -f
```

容器运行后，貌似不能修改映射端口和路径。可以通过 update 修改 cpu，内存等限制。
更新容器 restart policy

```bash
docker update --restart unless-stopped redis
```

其它
指定用户运行

```bash
docker run --user <username_or_UID> <image_name>
```

#### restart

- no
  - Don't automatically restart the container. (Default)
- `on-failure[:max-retries]`
  - Restart the container if it exits due to an error, which manifests as a non-zero exit code. Optionally, limit the number of times the Docker daemon attempts to restart the container using the :max-retries option. The on-failure policy only prompts a restart if the container exits with a failure. It doesn't restart the container if the daemon restarts.
- always
  - Always restart the container if it stops. If it's manually stopped, it's restarted only when Docker daemon restarts or the container itself is manually restarted.
- unless-stopped
  - Similar to always, except that when the container is stopped (manually or otherwise), it isn't restarted even after Docker daemon restarts.

```
docker run -d --restart unless-stopped redis

docker update --restart unless-stopped redis
```

#### 覆盖 Entrypoint

对于那些指定了 entrypoint 为特定程序，如 python 的容易非常有用，可以用于上去维修。

```bash
docker run -it --rm --name test --entrypoint bash image
```

应用场景：如果容器在反复重启，导致无法 exec 上去。此时就需要使用镜像重新 docker run，然后修改 entrypoint 避免再次失败重启。

#### workdir

```
docker run -it --rm -v $(pwd):/workspace --name test --entrypoint /bin/sh --workdir /workspace node:18-alpine

npm install
```

### images 相关

```bash
docker images   # 查看images
docker rmi      # 删除
docker history <image>  # 查看镜像历史记录（不同layer）
```

重命名 image

```bash
docker tag old_image_name:old_tag new_image_name:new_tag
docker rmi old_image_name:old_tag
```

#### save/load vs export/import vs commit

总结

- `docker save/load`：适用于备份和迁移一个或多个镜像，在不同的 Docker 主机之间传输。
- `docker export/import`：适用于备份容器的文件系统，不包括完整的镜像元数据和历史记录。
- `docker commit`：适用于创建基于容器当前状态的新镜像，包含新的一层 layer

**save/load**

将一个或多个镜像打包成 tar 归档文件，用于备份和传输镜像。
输出

```bash
docker save --output busybox.tar busybox  # 输出到tar文件
docker save -o ubuntu.tar ubuntu:lucid ubuntu:saucy  # 选择多个tag

docker save myimage:latest | gzip > myimage_latest.tar.gz # 输出到标准输出并使用gzip压缩
docker save myimage:latest | pv | zstd > myimage_latest.zstd
```

导入

```bash
docker load --input=file.tar

zstd -d -c myimage_latest.tar.zst | docker load  # -c 输出到标准输出
gzip -d -c myimage_latest.tar.zst | docker load  # -c 输出到标准输出
```

**export/import**

将容器的文件系统导出为 tar 文件，但不包含镜像的元数据和历史记录。

```
docker export -o container_filesystem.tar container_id

docker import container_filesystem.tar new_image_name:new_tag
```

**commit**

将容器目前的更改保存为新的一个 layer，从而基于该新镜像创建其它容器

```bash
docker commit nginx_base hello_world_nginx   # 保存为hello_world_nginx镜像

docker commit --author amit.sharma@sentinelone.com --message 'this is a basic nginx image' nginx_base authored # 添加author, message信息
```

可以通过`--change`修改原本容器的一些配置

- CMD
- ENTRYPOINT
- ENV
- EXPOSE
- USER
- VOLUME
- WORKDIR

```
docker commit --change='CMD ["nginx", "-T"]' nginx_base conf_dump
```

example

```
docker run --entrypoint bash --name test --gpus '"device=0"' -u 0:0 -it ghcr.io/k4yt3x/video2x:5.0.0-beta6

docker commit --author yuanfuya@qq.com --message 'fix interpolate parameter' --change='Entrypoint ["/usr/bin/python3.8", "-m", "video2x"]' test video2x:5.0.0-beta6.2
```

#### rename

```
docker tag old_image_name:old_tag new_image_name:new_tag

docker rmi old_image_name:old_tag
```

### 空间清理

docker system df  # 查看空间，包含每种资源可以删除的比例（reclaimable）

```
yfy@ares ➜  ~ docker system df
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          5         5         7.21GB    74.81MB (1%)
Containers      5         4         4.824GB   0B (0%)
Local Volumes   4         2         7.698GB   14.07kB (0%)
Build Cache     0         0         0B        0B
```

```
docker image prune # 删除悬挂镜像（docker build），不会删除没使用的
docker image prune -a  # 删除未使用的镜像
```

### 坑

#### --env-file 字符串不要加引号

若强行添加双引号（如 `MY_VAR="value"`），引号​**​会被视为值的一部分​**​，导致实际值为 `"value"`（包含引号），可能引发程序解析错误

**`docker run -e` 命令​**​：  
命令行中需用引号包裹含空格的字符串（如 `-e "MY_VAR=With space"`），但 `.env` 文件无需此操作

## docker 高级

### volume

#### 复制 volume trick

docker 不直接提供复制 volume 命令

```
docker volume create open-webui_open-webui

docker run --rm \
       -v open-webui:/from \
       -v open-webui_open-webui:/to \
       alpine sh -c "cd /from ; cp -av . /to"

```

## docker compose

### 升级镜像

```
docker compose pull && docker compose up -d
```

### 问题

#### 使用现有 volume

默认创建 `项目名_volume`

通过指定 `extrenal` 使用外部创建的 volume

```
volumes: # 将这里也修改为新卷名 
    open-webui_new:
    # 声明它是一个已经存在的、外部的卷
    external: true
```

也可以将现有卷复制一份到新的名字，docker compose 会自动使用。

## dockerfile

创建 Dockerfile，经常遇到因为某一步错误，导致反复 docker build。其实可以先创建一个基础环境，然后进入环境配置一遍，成功后再写 dockerfile。

先如下搭建一个基础环境

```Dockerfile
FROM ubuntu:22.04

RUN apt update\
  && apt install ...\

COPY . /app 
```

```
docker build -t app .  # .表示build时的上下文，如果Dockerfile放在项目根目录的话。COPY .便表示将整个项目复制到容器
```

然后进入项目，手动安装剩余依赖，直到测试能够运行

```bash
docker run -it --rm app bash
```

最后完善 Dockerfile

### COPY 与上下文

docker copy 只能复制上下文內的文件，可以在更顶级运行 docker build，通过 -f 指定 Dockerfile。

```
docker build -f docker/Dockerfile -t my-image .
```

### 使用 entrypoint.sh 脚本

使用 entrypoint 脚本可以实现根据用户运行容器时指定的环境变量，设置用户 uid,gid，从而保证容器和 host 文件权限正确。

```bash
ENTRYPOINT [ "/parse-and-link/docker/entrypoint.sh" ]
```

```bash
#!/bin/bash

PUID=${PUID:-1000}
PGID=${PGID:-1000}

if [ `id -u abc` -ne $PUID ]; then
    usermod -u $PUID myuser
fi
if [ `id -g abc` -ne $PGID ]; then
    groupmod -g $PGID abc
fi
chown -R abc:abc /parse-and-link

if [ -n "$JELLYFIN_URL" ] && [ -n "$JELLYFIN_API_KEY" ] ; then
    echo "Jellyfin URL is set to $JELLYFIN_URL"
    su abc -c "python3 run_config.py -c /config.json -m -j $JELLYFIN_URL -k $JELLYFIN_API_KEY"
else
    su abc -c "python3 run_config.py -c /config.json -m"
fi
```

### 其它小 tips

测试版命令

```bash
docker run -it --rm --name test --entrypoint bash rzero/pal:v1.0
```

发布版命令

```bash
docker run -d --name pal --restart unless-stopped \
  -e JELLYFIN_URL="xxxxx" \
  -e JELLYFIN_API_KEY="xxxxx" \
  -v ./config/example.docker.json:/config.json \
  rzero/pal:v1.0
```

- 使用`.dockerignore`文件，否则每次修改 Dockerfile，COPY 之后的步骤就都不能复用了

#### ADD

可以解压压缩包

```
WORKDIR /app
ADD nickdir.tar.gz .
```

### 发布到 dockerhub

```bash
docker login

docker tag local_image:tag username/repository:tag
docker push username/repository:tag
```

### 清理空间

```
docker system df -v  
```

```
docker system prune      # 删除停止的容器、未使用的镜像、网络、悬空镜像[1,3,6](@ref)
docker system prune -a   # 强制删除所有未使用的镜像（包括有标签但未引用的镜像）[1,3,6](@ref)
docker volume prune      # 删除未挂载的卷[3,11](@ref)
docker network prune     # 删除未使用的网络[3](@ref)
docker images prune
```

```
docker rmi $(docker images -q -f "dangling=true")  # 删除无标签的镜像[2,4](@ref)
```

### 坑

#### git safe 目录导致报错

```
git config --global safe.directory '*'
```

```
 > [13/17] ADD MLNX_OFED_LINUX-5.7-1.0.2.0-ubuntu22.04-x86_64.tgz /:
------
Dockerfile:105
--------------------
 103 |
 104 |     # 安装 MLNX OFED 用户态库
 105 | >>> ADD MLNX_OFED_LINUX-5.7-1.0.2.0-ubuntu22.04-x86_64.tgz /
 106 |     RUN cd /MLNX_OFED_LINUX-5.7-1.0.2.0-ubuntu22.04-x86_64 \
 107 |         && ./mlnxofedinstall --user-space-only --without-fw-update --force
--------------------
ERROR: failed to solve: Error processing tar file(exit status 1): failed to Lchown "/MLNX_OFED_LINUX-5.7-1.0.2.0-ubuntu22.04-x86_64/DEBS/neohost-sdk_1.5.0-102_amd64.deb" for UID 71873, GID 0 (try increasing the number of subordinate IDs in /etc/subuid and /etc/subgid): lchown /MLNX_OFED_LINUX-5.7-1.0.2.0-ubuntu22.04-x86_64/DEBS/neohost-sdk_1.5.0-102_amd64.deb: invalid argument
```

### 进阶：多阶段构建

多阶段构建是为了分离构建环境和运行时环境，减小最终镜像体积。

构建阶段可使用较大的开发环境（如完整版 `python:3.11`），而最终阶段改用精简镜像（如 `python:3.11-slim`），仅复制必要的运行文件（如编译后的代码、依赖包），避免携带构建工具和中间文件

- `builder` 阶段安装依赖
  - `pip install --user` 将包安装到​**​用户级目录​**​ `/root/.local/`
    - 二进制文件：`/root/.local/bin/`
    - 库文件：`/root/.local/lib/python3.11/site-packages/`
- `final` 阶段复制并使用依赖
  - 从 `builder` 阶段复制 `/root/.local` 目录到当前阶段的相同路径，完整保留依赖文件结构
  - Python 运行时默认会搜索 `sys.path` 中的路径（包括用户级目录 `/root/.local/lib/python3.11/site-packages/`），因此无需额外配置即可导入已安装的包

## docker 实验

### 软硬链接

总结

- 软链接需要使用相对路径，并且 src 和 dst（链接）最长相同路径的目录，必须同时存在于 docker 和 host
- 硬链接没有任何要求，打上链接的一刻，任何地方均能访问到该文件

实验：
host:

```sh
➜  pwd
/home/yfy/scripts/test/mnt
➜  tree -L 4
.
├── Disk1
│   ├── links
│   │   └── Movie
│   │       ├── aa.mp4 -> ../../Movie/a.mp4
│   │       ├── a.mp4 -> /home/yfy/scripts/test/mnt/Disk1/Movie/a.mp4
│   │       └── b.mp4   # 硬链接
│   └── Movie
│       └── a.mp4  # 原始文件
├── Disk2
├── outfile -> ../../outfile  # 软链接到docker中看不到的目录文件
└── outfile-hl   # 硬链接

5 directories, 7 files

```

docker:

```sh
ubuntu@dfc03804864c ➜  pwd
/workspace/mnt
ubuntu@dfc03804864c ➜  tree -L 4
.
|-- Disk1
|   |-- Movie
|   |   `-- a.mp4
|   `-- links
|       `-- Movie
|           |-- a.mp4 -> /home/yfy/scripts/test/mnt/Disk1/Movie/a.mp4  (无法访问)
|           |-- aa.mp4 -> ../Movie/a.mp4  (无法访问)
|           |-- aaa.mp4 -> ../../Movie/a.mp4  
|           `-- b.mp4
|-- Disk2
|-- outfile -> ../../outfile   (无法访问)
`-- outfile-hl  (无法访问)

5 directories, 7 files
```

在 docker 和 host 中查看 outfile-hl 的 inode 可以看到和源文件 outfile 是相同的

```
➜  ls -i ../../outfile
1091603 -rw-rw-r-- 2 yfy yfy 0 12月  9 16:57 ../../outfile

➜  ls -i outfile-hl
1091603 -rw-rw-r-- 2 yfy yfy 0 12月  9 16:57 outfile-hl
```

### gpu

```
Error response from daemon: failed to create task for container: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: error during container init: error running hook #0: error running hook: exit status 1, stdout: , stderr: Auto-detected mode as 'legacy'
nvidia-container-cli: initialization error: nvml error: driver/library version mismatch: unknown
Error: failed to start containers: jellyfin
```

```
[Sat Apr 13 23:38:47 2024] NVRM: API mismatch: the client has the version 535.171.04, but
                           NVRM: this kernel module has the version 535.161.07.  Please
                           NVRM: make sure that this kernel module and all NVIDIA driver
                           NVRM: components have the same version.
```

## nvidia-container-toolkit  

nvidia runtime

nvidia-container-runtime 已经被 nvidia-container-toolkit  替代了： [NVIDIA/nvidia-container-runtime: NVIDIA container runtime (github.com)](https://github.com/NVIDIA/nvidia-container-runtime)

安装教程

[Installing the NVIDIA Container Toolkit — NVIDIA Container Toolkit 1.16.0 documentation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

Configure the container runtime by using the `nvidia-ctk` command:

```
sudo nvidia-ctk runtime configure --runtime=docker

sudo systemctl restart docker
```

### nvidia cuda 镜像
