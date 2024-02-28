---
title: 安装 centos 虚拟机以及配置 gameboy.live 记录
date: 2020-02-02 19:08:52
tags:
- centos
- gameboy
categories:
- 折腾
---

安装 centos 虚拟机以及配置 gameboy.live 记录
<!-- more -->

## 1. 下载镜像

在清华源等镜像源都可以，我下载的是 everything 版本（有 10G 左右）

## 2. VirtualBox 安装 CentOS

需要选择安装那些软件（默认是 minimalist)，我选择了手动，然后选择了网络相关的（默认有 sshd)。然后设置 root 密码，新建初始账户。

## 3. 配置（换源）

1. 发现刚安装的 centos 没办法使用 yum（repository 没有配置好）。找到如何换源的方法，主要分为本地源（iso 镜像里有一个 Packages，包含官方的所有软件 (rpm 包)，10000 个左右）和网络源。

2. 先安装下 VBox 扩展，

   ```bash
   mkdir /mnt/cdrom
   mount /dev/cdrom /mnt/cdrom
   cd /mnt/cdrom
   ./VBoxLinuxAdditions.run (中途会编译)
   ```

   之后可以设置共享文件夹，剪切板等。

3. 安装本地源：

   1. 挂载 centos 系统镜像（everything 那个）:

      先在虚拟机设置里存储，IDE 控制器那分配光驱，把 iso 添加进去。

      ```
      mkdir /media/cdrom
      mount /dev/cdrom /media/cdrom
      ```

   2. 修改源配置文件

      - /etc/yum.config包含main配置，在/etc/yum.repos.d/下为各种源（本地源CentOS-Media.repo，网络源CentOS-Base.repo）

      - 由于/media/cdrom 已经在 baseurl 里有了，故只需将 enabled 设为 1 即可

      - 将 CenOS-Base.repo 重命名为其它

   3. 使之生效

      ```
      yum clean all
      yum makecache
      ```

      愉快地安装 vim, git, python 吧。

      不知道如何安装 netstat，ifconfig？直接 yum search xxx 会告诉你答案。
   
4. 设置镜像源

   阿里云镜像比较齐全，且有帮助文档。https://developer.aliyun.com/mirror/ 

## 4 配置 gameboy.live

### 1. 安装 golang

yum install 会显示没有 golang，或者版本不够新

在官网上有已经编译好的 golang，直接下载解压就可以使用。

```bash
wget https://dl.google.com/go/go1.13.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.13.linux-amd64.tar.gz
添加PATH变量

go version #查看版本
```

   tips: 关于 linux 安装路径：

- /usr 目录下为系统软件目录，有/usr/bin, /usr/lib等文件夹。相当于windows的C://windows/
- /usr/local为用户软件目录，也有/usr/local/bin, /usr/local/lib等。用户安装的软件默认会安装在这里。相当于C://Program Files/
- /opt，代表可选软件，如 firefox 等独立的大型软件可以安装在这里。相当于 D://

### 2. 配置 golang 代理

直接 go get 很容易超时。

```bash
go env -w GO111MODULE=on
go env -w GOPROXY=https://goproxy.cn,direct
```

   可以查看 https://goproxy.cn 官网介绍

   

### 3. 安装 x11

直接 go 编译 gameboy.live 会报各种.h 文件找不到。以下

```bash

# https://github.com/go-gl/glfw
...

yum install libX11-devel libXcursor-devel libXrandr-devel libXinerama-devel mesa-libGL-devel libXi-devel


# github.com/hajimehoshi/oto
../../go/pkg/mod/github.com/hajimehoshi/oto@v0.3.1/driver_linux.go:23:28: fatal error: alsa/asoundlib.h: No such file or directory

yum install alsa-lib-devel (ubuntu下的安装libasound2就好了，yum下好不容易才找到可以安装这个代替libasound2。)
```



#### 4. 运行

- 发现由于 mobaxterm 自带 x11server，因此在阿里云上运行，便会自动打开图形窗口。

- 发现在 putty 上可以正确显示，但按键只有 Enter 起作用，ctrl+z 等可以产生 Right 的效果。
- 在 VB 虚拟机（无图形界面）上无法正确显示画面。WSL 上也不行。
- 在 ubuntu 桌面版的终端可以完美运行。

#### 5. 结束 ssh 后不停止运行

 https://blog.csdn.net/v1v1wang/article/details/6855552 

