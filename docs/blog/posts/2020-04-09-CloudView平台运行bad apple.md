---
title: CloudView平台运行bad apple
date: 2020-04-09 12:00:00
tags:
  - cloudview
  - bad-apple
categories:
  - 折腾
---

重写了bad-apple的代码，利用了多进程的方式进行视频转换。

以下是各个配置转换bad apple.mp4的时间

|          | 线性执行 | 4线程 | 1进程 | 2进程 | 4进程 | 8进程 | 16进程 |
| -------- | -------- | ----- | ----- | ----- | ----- | ----- | ------ |
| 时间(秒) | 34.97    | 34.70 | 35.05 | 24.15 | 18.11 | 18.09 | 18     |

其中线程为采用threading库，进程则采用multiprocessing库

我的电脑配置为：

| CPU     | intel(R) Core(TM) i5-7200U CPU @ 2.50GHz 2.70GHz |
| ------- | ------------------------------------------------ |
| RAM     | 8.00 GB                                          |
| Windows | Windows10 家庭版 1909 18363.720                  |

官方文档说明了threading库底层实现时仍只有一个线程，因而只适用于大量I/O并发的情况。而我们的图片转换成字符画的过程主要是计算密集型，因此基本没有改善性能。

而采用多进程时，刚好对应我电脑的4线程（2核，采用超线程技术可以有4个线程，其实这里进程线程有点晕）时提升最大。

于是便想知道32个核时，能提升多少，便想在服务器上跑跑看。以下是配置运行过程。



出人意料的结果：

|          | 1进程 | 4线程 | 8进程 | 16进程 | 32进程 |
| -------- | ----- | ----- | ----- | ------ | ------ |
| 时间(秒) | 51    | 24    | 23.22 | 21.57  | 21.14  |

可能进程多了后，写文件的速度反而成了瓶颈，查看top发现各个核的cpu利用率都只有10%左右，在代码中输出cvt_frame.qsize()也发现几乎都是满的。（在自己电脑上大多数都是0，表明cvt_frame供不应求）

<!-- more -->

## 安装python3


首先发现没有python3，于是想办法去安装python3。

### 方法1：编译安装

ipython官网下载python3源码，这里下载了python3.6.10

然后解压到/usr/local/src

```bash
sudo tar zxf Python-3.6.10.tgz -C /usr/local/src/
```

cd到解压目录，编译安装

```
./configure
sudo make
sudo make install
```

到这里可能会报许多错误，这是缺少一些库导致的。

试错后知道需要zlib, openssl库（去官网下载源码，编译安装）



事实上搜索centos 编译安装python3会告诉你需要以下这么多库，由于这里是内网环境，因此只能一个一个去下载编译。（但事实上可以使用方法2中的方法，搭好yum的本地源，从而可以使用yum，虽然这样的话可以直接用yum安装python，但是本地源中的python为固定版本，而编译安装可以从官网上下载不同的版本。并且推广来说，对于一些必须编译安装的软件，通过yum安装必要的库，然后编译安装是一种比较好的方式）

```
yum install zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel libffi-devel gcc make
```



上面的默认安装路径为/usr/loacl/bin，库文件则安装到/usr/local/lib。（也有可能/usr/local/lib64）

如果自定义安装路径如，./configure --prefix=/usr/local/python3

需要添加动态连接库路径。即在/etc/ld.so.conf里添加/usr/local/python3/lib

还是默认路径比较好，不过自定义安装路径可以不需要root权限。（只要把程序安装到非root用户可以读写的目录下就可，上面的示例其实也需要root权限，但用户的home路径下应该可以随便装。还有非root安装时，最后需要里添加环境变量LD_LIBTARY_PATH，而不是修改ld.so.conf(需要root权限)）



### 方法2：

配置本地yum源

1. 上传CentOS系统iso文件，大概11G

2. 挂载镜像文件

   ```bash
   mount CentOS-7-x86_64-Everything-1908.iso /media/cdrom
   ```

3. 配置地yum源，修改/etc/yum.repo.d/CentOS-Media.repo，把enabled置1，因为baseurl中已经有了/media/cdrom故不用改，如果上一步挂载路径为其它，则添加到其中。

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

4. 可以使用yum安装一些常见的软件了。

我先采用了方式1，虽然可以运行python了，但编译时的各种缺库的报错总让我觉得它有一些问题。后面又采用了方式2来安装python



## 离线安装opencv

bad apple代码需要import cv2，cv2模块是opencv-python里的，需要安装opencv-python包。由于是内网，因此只能采用离线安装的方式。

离线安装python包

1. 去镜像网站寻找到需要的.whl文件。如清华的镜像源目录结构为/pypi/web/simple下。但这种方式寻找起来它麻烦了。而且python的包也是有依赖的，因此我们也不知道opencv-python需要哪些包。这里比较简单的方式是在自己的电脑上用pip install opencv-python，输出信息中不仅包含需要哪些其它包，而且还包含它的下载路径，直接复制路径到浏览器打开即可下载。

   这里发现opencv-python只需要numpy和自己便可。

2. pip install 对应的whl文件即可。

这里由于自己电脑上的python为3.7.3的版本，因此找到的包为

```
numpy-1.18.2-cp37-cp37m-manylinux1_x86_64.wh
opencv_python-4.2.0.34-cp37-cp37m-manylinux1_x86_64.whl
```

但云主机上的python为3.6.1的版本，因此pipinstall的时候报了如下错误：

```bash
[root@centos1 mpiuser]# pip3 install numpy-1.18.2-cp37-cp37m-manylinux1_x86_64.whl
pip is configured with locations that require TLS/SSL, however the ssl module in Python is not available.
numpy-1.18.2-cp37-cp37m-manylinux1_x86_64.whl is not a supported wheel on this platform.
pip is configured with locations that require TLS/SSL, however the ssl module in Python is not available.
Could not fetch URL https://pypi.org/simple/pip/: There was a problem confirming the ssl certificate: HTTPSConnectionPool(host='pypi.org', port=443): Max retries exceeded with url: /simple/pip/ (Caused by SSLError("Can't connect to HTTPS URL because the SSL module is not available.",)) - skipping
```

上面的require TLS/SSL可能就是因为我没有正确编译openssl导致的（但事实上openssl version是可以输出的，且采用方式2后yum install python3应该不会有问题才对）这里先不管它。

主要是中间的`is not a supported wheel on this platform.`

在自己电脑上用conda安装其它python版本（安装其它python版本，在window上可以直接下载对应版本安装即可，但在linux上要么是添加其它源，要么就只有源码编译安装了，这里使用conda是取巧的方式，类似于添加其它源）

```bash
conda env list #查看conda创建的环境
conda create -e py36
conda activate py36
conda search python #可以看到许多python版本
conda install python=3.6.1 #指定版本

conda install pip #默认没有安装pip
pip install opencv-python #采用pip，因为我们就是想知道opencv-python的pip包需要哪些依赖。正常使用最好使用conda代替pip
```



最后下载的便是以下的包了，可以发现cp37变成了cp36

```
opencv_python-4.2.0.34-cp36-cp36m-manylinux1_x86_64.wh
numpy-1.18.2-cp36-cp36m-manylinux1_x86_64.whl
```

下面是numpy安装的输出，可以看到还是有一点问题(Caused by SSLError("Can't connect to HTTPS URL because the SSL module is not available.",)) - skipping。但还是安装成功了。

```
[root@centos1 mpiuser]# pip3 install numpy-1.18.2-cp36-cp36m-manylinux1_x86_64.whl
pip is configured with locations that require TLS/SSL, however the ssl module in Python is not available.
Processing ./numpy-1.18.2-cp36-cp36m-manylinux1_x86_64.whl
Installing collected packages: numpy
Successfully installed numpy-1.18.2
pip is configured with locations that require TLS/SSL, however the ssl module in Python is not available.
Could not fetch URL https://pypi.org/simple/pip/: There was a problem confirming the ssl certificate: HTTPSConnectionPool(host='pypi.org', port=443): Max retries exceeded with url: /simple/pip/ (Caused by SSLError("Can't connect to HTTPS URL because the SSL module is not available.",)) - skipping
```



python运行时又报出一些动态链接库找不到（因该还是编译python时，没安装全那些库导致的），解决后便可以运行bad apple了。

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

