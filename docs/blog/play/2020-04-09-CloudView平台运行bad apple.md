---
title: CloudView 平台运行 bad apple
date: 2020-04-09 12:00:00
tags:
  - cloudview
  - bad-apple
categories:
  - 折腾记录
---

重写了 bad-apple 的代码，利用了多进程的方式进行视频转换。

以下是各个配置转换 bad apple.mp4 的时间

|          | 线性执行 | 4 线程 | 1 进程 | 2 进程 | 4 进程 | 8 进程 | 16 进程 |
| -------- | -------- | ----- | ----- | ----- | ----- | ----- | ------ |
| 时间 (秒) | 34.97    | 34.70 | 35.05 | 24.15 | 18.11 | 18.09 | 18     |

其中线程为采用 threading 库，进程则采用 multiprocessing 库

我的电脑配置为：

| CPU     | intel(R) Core(TM) i5-7200U CPU @ 2.50GHz 2.70GHz |
| ------- | ------------------------------------------------ |
| RAM     | 8.00 GB                                          |
| Windows | Windows10 家庭版 1909 18363.720                  |

官方文档说明了 threading 库底层实现时仍只有一个线程，因而只适用于大量 I/O 并发的情况。而我们的图片转换成字符画的过程主要是计算密集型，因此基本没有改善性能。

而采用多进程时，刚好对应我电脑的 4 线程（2 核，采用超线程技术可以有 4 个线程，其实这里进程线程有点晕）时提升最大。

于是便想知道 32 个核时，能提升多少，便想在服务器上跑跑看。以下是配置运行过程。

出人意料的结果：

|          | 1 进程 | 4 线程 | 8 进程 | 16 进程 | 32 进程 |
| -------- | ----- | ----- | ----- | ------ | ------ |
| 时间 (秒) | 51    | 24    | 23.22 | 21.57  | 21.14  |

可能进程多了后，写文件的速度反而成了瓶颈，查看 top 发现各个核的 cpu 利用率都只有 10% 左右，在代码中输出 cvt_frame.qsize() 也发现几乎都是满的。（在自己电脑上大多数都是 0，表明 cvt_frame 供不应求）

<!-- more -->

## 安装 python3

首先发现没有 python3，于是想办法去安装 python3。

### 方法 1：编译安装

ipython 官网下载 python3 源码，这里下载了 python3.6.10

然后解压到/usr/local/src

```bash
sudo tar zxf Python-3.6.10.tgz -C /usr/local/src/
```

cd 到解压目录，编译安装

```
./configure
sudo make
sudo make install
```

到这里可能会报许多错误，这是缺少一些库导致的。

试错后知道需要 zlib, openssl 库（去官网下载源码，编译安装）

事实上搜索 centos 编译安装 python3 会告诉你需要以下这么多库，由于这里是内网环境，因此只能一个一个去下载编译。（但事实上可以使用方法 2 中的方法，搭好 yum 的本地源，从而可以使用 yum，虽然这样的话可以直接用 yum 安装 python，但是本地源中的 python 为固定版本，而编译安装可以从官网上下载不同的版本。并且推广来说，对于一些必须编译安装的软件，通过 yum 安装必要的库，然后编译安装是一种比较好的方式）

```
yum install zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel libffi-devel gcc make
```

上面的默认安装路径为/usr/loacl/bin，库文件则安装到/usr/local/lib。（也有可能/usr/local/lib64）

如果自定义安装路径如，./configure --prefix=/usr/local/python3

需要添加动态连接库路径。即在/etc/ld.so.conf 里添加/usr/local/python3/lib

还是默认路径比较好，不过自定义安装路径可以不需要 root 权限。（只要把程序安装到非 root 用户可以读写的目录下就可，上面的示例其实也需要 root 权限，但用户的 home 路径下应该可以随便装。还有非 root 安装时，最后需要里添加环境变量 LD_LIBTARY_PATH，而不是修改 ld.so.conf(需要 root 权限)）

### 方法 2

配置本地 yum 源

1. 上传 CentOS 系统 iso 文件，大概 11G

2. 挂载镜像文件

   ```bash
   mount CentOS-7-x86_64-Everything-1908.iso /media/cdrom
   ```

3. 配置地 yum 源，修改/etc/yum.repo.d/CentOS-Media.repo，把 enabled 置 1，因为 baseurl 中已经有了/media/cdrom 故不用改，如果上一步挂载路径为其它，则添加到其中。

   ```
   [root@centos1 temp]# cat /etc/yum.repos.d/CentOS-Media.repo
   # CentOS-Media.repo
   #
   #  This repo can be used with mounted DVD media, verify the mount point for
   #  CentOS-7.  You can use this repo and yum to install items directly off the
   #  DVD ISO that we release.
   #
   # To use this repo, put in your DVD and use it with the other repos too:
   #  yum --enablerepo=c7-media [command]
   #
   # or for ONLY the media repo, do this:
   #
   #  yum --disablerepo=\* --enablerepo=c7-media [command]
   
   [c7-media]
   name=CentOS-$releasever - Media
   baseurl=file:///media/CentOS/
           file:///media/cdrom/
           file:///media/cdrecorder/
   gpgcheck=1
   enabled=1
   gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7
   ```

4. 可以使用 yum 安装一些常见的软件了。

我先采用了方式 1，虽然可以运行 python 了，但编译时的各种缺库的报错总让我觉得它有一些问题。后面又采用了方式 2 来安装 python

## 离线安装 opencv

bad apple 代码需要 import cv2，cv2 模块是 opencv-python 里的，需要安装 opencv-python 包。由于是内网，因此只能采用离线安装的方式。

离线安装 python 包

1. 去镜像网站寻找到需要的.whl 文件。如清华的镜像源目录结构为/pypi/web/simple 下。但这种方式寻找起来它麻烦了。而且 python 的包也是有依赖的，因此我们也不知道 opencv-python 需要哪些包。这里比较简单的方式是在自己的电脑上用 pip install opencv-python，输出信息中不仅包含需要哪些其它包，而且还包含它的下载路径，直接复制路径到浏览器打开即可下载。

   这里发现 opencv-python 只需要 numpy 和自己便可。

2. pip install 对应的 whl 文件即可。

这里由于自己电脑上的 python 为 3.7.3 的版本，因此找到的包为

```
numpy-1.18.2-cp37-cp37m-manylinux1_x86_64.wh
opencv_python-4.2.0.34-cp37-cp37m-manylinux1_x86_64.whl
```

但云主机上的 python 为 3.6.1 的版本，因此 pipinstall 的时候报了如下错误：

```bash
[root@centos1 mpiuser]# pip3 install numpy-1.18.2-cp37-cp37m-manylinux1_x86_64.whl
pip is configured with locations that require TLS/SSL, however the ssl module in Python is not available.
numpy-1.18.2-cp37-cp37m-manylinux1_x86_64.whl is not a supported wheel on this platform.
pip is configured with locations that require TLS/SSL, however the ssl module in Python is not available.
Could not fetch URL https://pypi.org/simple/pip/: There was a problem confirming the ssl certificate: HTTPSConnectionPool(host='pypi.org', port=443): Max retries exceeded with url: /simple/pip/ (Caused by SSLError("Can't connect to HTTPS URL because the SSL module is not available.",)) - skipping
```

上面的 require TLS/SSL可能就是因为我没有正确编译openssl导致的（但事实上openssl version 是可以输出的，且采用方式 2 后 yum install python3 应该不会有问题才对）这里先不管它。

主要是中间的`is not a supported wheel on this platform.`

在自己电脑上用 conda 安装其它 python 版本（安装其它 python 版本，在 window 上可以直接下载对应版本安装即可，但在 linux 上要么是添加其它源，要么就只有源码编译安装了，这里使用 conda 是取巧的方式，类似于添加其它源）

```bash
conda env list #查看conda创建的环境
conda create -e py36
conda activate py36
conda search python #可以看到许多python版本
conda install python=3.6.1 #指定版本

conda install pip #默认没有安装pip
pip install opencv-python #采用pip，因为我们就是想知道opencv-python的pip包需要哪些依赖。正常使用最好使用conda代替pip
```

最后下载的便是以下的包了，可以发现 cp37 变成了 cp36

```
opencv_python-4.2.0.34-cp36-cp36m-manylinux1_x86_64.wh
numpy-1.18.2-cp36-cp36m-manylinux1_x86_64.whl
```

下面是 numpy 安装的输出，可以看到还是有一点问题 (Caused by SSLError("Can't connect to HTTPS URL because the SSL module is not available.",)) - skipping。但还是安装成功了。

```
[root@centos1 mpiuser]# pip3 install numpy-1.18.2-cp36-cp36m-manylinux1_x86_64.whl
pip is configured with locations that require TLS/SSL, however the ssl module in Python is not available.
Processing ./numpy-1.18.2-cp36-cp36m-manylinux1_x86_64.whl
Installing collected packages: numpy
Successfully installed numpy-1.18.2
pip is configured with locations that require TLS/SSL, however the ssl module in Python is not available.
Could not fetch URL https://pypi.org/simple/pip/: There was a problem confirming the ssl certificate: HTTPSConnectionPool(host='pypi.org', port=443): Max retries exceeded with url: /simple/pip/ (Caused by SSLError("Can't connect to HTTPS URL because the SSL module is not available.",)) - skipping
```

python 运行时又报出一些动态链接库找不到（因该还是编译 python 时，没安装全那些库导致的），解决后便可以运行 bad apple 了。

```
[root@centos1 temp]# python3 convert_video_multiprocess.py
Traceback (most recent call last):
  File "convert_video_multiprocess.py", line 1, in <module>
    import cv2
  File "/usr/local/lib/python3.6/site-packages/cv2/__init__.py", line 5, in <module>
    from .cv2 import *
ImportError: libSM.so.6: cannot open shared object file: No such file or directory
还有libXrender等
```
