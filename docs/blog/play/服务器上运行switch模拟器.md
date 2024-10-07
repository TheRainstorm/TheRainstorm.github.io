---
title: 服务器上运行switch模拟器（linux 云游戏）
date: 2023-07-24 15:49:07
tags:
  - wolf
  - gow
  - linux
  - gaming
  - docker
  - 虚拟游戏房
categories:
  - 折腾记录
---
# 介绍


服务器有一些老计算卡如 P40，TitanV 都是有图形能力的，并且貌似性能还不错（比如 TitanV 有 3070 的性能）。还有一些老卡如 1080Ti 很少有人用，闲置太浪费了。

因此本着科学求实的精神，想探究下实验室这些卡的性能水平，为之后科研做铺垫。。。好吧，我编不下去了，就是想白嫖实验室显卡玩游戏。加上最近塞尔达王国之泪出了，之前捡垃圾时，见过用 P106 这种 100 块的 “1060” linux 下玩 switch 模拟器效果不错。而自己的显卡 rx550 根本带不动，流下了没钱买卡的泪水。

声明

- 所有配置都是在 docker 等隔离的虚拟化环境中，不会对系统环境造成污染，影响其它人使用
- 只在使用人数不多的机器上实验，不会在 A100 等主力机器上实验
- 只在没人用时实验

效果

- docker gow

![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/Snipaste_2023-05-14_17-19-00.jpg)
![Snipaste_2023-05-16_15-08-25.jpg](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/Snipaste_2023-05-16_15-08-25.jpg)

![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/snode2-steam-system-info.jpg)

![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/Snipaste_2023-05-16_14-51-03.jpg)

wolf 即插即用效果

![image.png](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20241003112530.png)

![image.png](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20241003112556.png)

<!-- more -->

# “计算卡”性能对比

[NVIDIA Tesla P40 Specs | TechPowerUp GPU Database](https://www.techpowerup.com/gpu-specs/tesla-p40.c2878)
[NVIDIA Tesla P100 PCIe 16 GB Specs | TechPowerUp GPU Database](https://www.techpowerup.com/gpu-specs/tesla-p100-pcie-16-gb.c2888)

![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20230615135150.png)
![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20230615134759.png)

P100(0.84)< 1080 Ti(1) < P40(1.04) < Titan V(1.32) < 3070Ti(1.46)


# LXD 虚拟机方案（不用了）

*p.s. lxd 必须使用本地用户，服务器现在已经没有本地 home 目录了，因此这个方案不再适用。*

```
Sorry, home directories outside of /home needs configuration.
See https://forum.snapcraft.io/t/11209 for details.
```
## steam 安装

[5 Simple Ways to Install Steam on Linux - wikiHow](https://www.wikihow.com/Install-Steam-on-Linux)
[Steam under Linux - Valve Developer Community (valvesoftware.com)](https://developer.valvesoftware.com/wiki/Steam_under_Linux)
dpkg i386

steam play(proton)
[Linux Gaming with Ubuntu Desktop Part 1: Steam & Proton | Ubuntu](https://ubuntu.com/blog/linux-gaming-with-ubuntu-desktop-steam-and-proton)

## steam link 使用

steam link流式传输错误 无法连接以中继
- 刚开始手机steam link无法连接。在lxd容器内开启wg全部流量走op2后可以。
- 但是笔记本steam link不行，甚至可以测得速率。
  - 笔记本也开启wg全部流量走op2。居然就可以连接了
  - 看到日志是@LAN两边的ipv6地址

steam link有声音，延迟红线是60。
可以玩星露谷，但是无法使用手柄操作。

![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/steam-link-connected-ip.jpg)

## sunshine 配置

parsec althernative
- moonlight + sunshine
[(6) Parsec alternative for Linux : linux_gaming (reddit.com)](https://www.reddit.com/r/linux_gaming/comments/tz36bs/parsec_alternative_for_linux/)

### setup

[Nvidia’s GameStream is dead. Sunshine and Moonlight are great replacements. | Ars Technica](https://arstechnica.com/gaming/2023/04/nvidias-gamestream-is-dead-sunshine-and-moonlight-are-better-replacements/)
[Usage - Sunshine documentation (lizardbyte.dev)](https://docs.lizardbyte.dev/projects/sunshine/en/latest/about/usage.html#setup)

### 遇到的问题

#### use nvidia runtime

```
Error: Failed to create session: Version mismatch between NvFBC and the X driver interface
[2023:05:15:02:38:46]: Error: Couldn't expose some/all drm planes for card: /dev/dri/card8

Error: Could not open codec [h264_nvenc]: Function not implemented
Error: Failed to create a CUDA device: Operation not supported
```

手动安装nvida driver会包含x driver，因此导致broken
> Did you build from source, and if so, does the build include CUDA support and how was CUDA installed in that case?
> I've seen the 'version mismatch between NvFBC and X driver' error when the NVidia driver installation is broken and multiple versions of driver & nvidia library versions exist on the system at build time. One source of this is manually installing CUDA by using the NVidia installer from their website instead of using only distro packages. The reason is that the CUDA installer from NVidia includes the full X driver as well so if you install the distro drivers then install the NVidia CUDA manually, your driver config will be broken and building with CUDA support enabled will get you this error.

卸载nvida驱动后，使用nvidia runtime
- [Error: Couldn't import RGB Image: 00003009 & Error: Unknown status & Error: Failed to create session: Version mismatch between NvFBC and the X driver interface · Issue #514 · LizardByte/Sunshine (github.com)](https://github.com/LizardByte/Sunshine/issues/514)
```
Error: Couldn't find any of the following libraries: [libnvidia-fbc.so.1, libnvidia-fbc.so]
[2023:05:15:14:01:19]: Error: Couldn't expose some/all drm planes for card: /dev/dri/card8
Error: Could not open codec [h264_nvenc]: Operation not permitted

Error: Failed to create a CUDA device: Operation not supported
```

```
apt install libnvidia-fbc1-530
```

## lxd 手柄

moonlight连接sunshine后，没有手柄。尝试在lxd中添加/dev/uinput，结果moonlight连接后连键鼠都无法操作了。

但是steam link是可以的，发现steam link连接后，/dev/input下会出现js0和对应evet。将这些都lxc add后（也就是说需要steam link连接后再手动添加），容器内确实可以手柄操作了。但是要想让yuzu检测到手柄，还需要通过steam启动yuzu才行。

后面发现可以直接直通/dev/input（当然为了避免权限问题，lxd可以以特权容器运行，这样就不需要经过uid和gid映射），然后moonlight连接后，键鼠没有出现问题。但是手柄还是不行，报错。感觉可以解决，但是发现帧数和docker方案差不多，因此就没去尝试解决了。
```
Error: Could not create Sunshine Gamepad: Permission denied
```



lxd直通手柄
[Joystick Passthrough - LXD - Linux Containers Forum](https://discuss.linuxcontainers.org/t/joystick-passthrough/14383/6)
[Unable to get input in container - LXD - Linux Containers Forum](https://discuss.linuxcontainers.org/t/unable-to-get-input-in-container/13609/4)
[7. uinput module — The Linux Kernel documentation](https://docs.kernel.org/input/uinput.html)

```
 lxc config device add ubuntu20 event unix-char path=/dev/input/event uid=1001 gid=1001 mode=0777
```

- 在host运行xorg，将unix socket暴露给容器。运行steam的方法[Unable to get input in container - LXD - Linux Containers Forum](https://discuss.linuxcontainers.org/t/unable-to-get-input-in-container/13609)
> I suspect it may have to do with Xorg trying to list things through udev and udev not having database entries for those devices.
> You could maybe cheat by copying the /run/udev data across to the container prior to starting Xorg, though I wonder if it wouldn’t be cleaner to run Xorg outside of the container, leaving all the input stuff handled there and then just expose the X11 socket to the container for it to run kodi against.
> That’d be closer to other setups described on this forum before for running things like steam inside of a container.


新发现：
- /run/udev无法直通到lxd容器内（tmpfs的原因？）
- 以普通用户启动tigervnc，启动sunshine，/dev/input目录下并没有出现键盘设备和js设备（docker方案出现了mouse0-2, js0-1）
- 以root用户启动tigervnc，普通用户启动sunshine，/dev/input出现了键鼠。但是无法操作键鼠了。

#### docker 对比

```

```

```
root@531dd4a4763b:~# cat .config/sunshine/sunshine.log
[2023:05:17:10:39:35]: Error: Failed to create session: This hardware does not support NvFBC
[2023:05:17:10:39:35]: Error: Couldn't expose some/all drm planes for card: /dev/dri/card2
[2023:05:17:10:39:35]: Info: Detecting connected monitors
[2023:05:17:10:39:35]: Info: // Testing for available encoders, this may generate errors. You can safely ignore those errors. //
[2023:05:17:10:39:35]: Info: Trying encoder [nvenc]
[2023:05:17:10:39:35]: Info: Screencasting with X11
[2023:05:17:10:39:35]: Info: SDR color coding [Rec. 601]
[2023:05:17:10:39:35]: Info: Color range: [JPEG]
[2023:05:17:10:39:36]: Error: Could not open codec [h264_nvenc]: Function not implemented
[2023:05:17:10:39:36]: Info: Screencasting with X11
[2023:05:17:10:39:36]: Info: SDR color coding [Rec. 601]
[2023:05:17:10:39:36]: Info: Color range: [JPEG]
[2023:05:17:10:39:36]: Error: Failed to create a CUDA device: Operation not supported
[2023:05:17:10:39:36]: Info: Screencasting with X11
[2023:05:17:10:39:36]: Info: SDR color coding [Rec. 601]
[2023:05:17:10:39:36]: Info: Color range: [JPEG]
[2023:05:17:10:39:36]: Error: Failed to create a CUDA device: Operation not supported
[2023:05:17:10:39:36]: Info: Screencasting with X11
[2023:05:17:10:39:36]: Info: SDR color coding [Rec. 601]
[2023:05:17:10:39:36]: Info: Color range: [JPEG]
[2023:05:17:10:39:36]: Error: Failed to create a CUDA device: Operation not supported
[2023:05:17:10:39:36]: Info: Encoder [nvenc] failed
[2023:05:17:10:39:36]: Info: Trying encoder [vaapi]
[2023:05:17:10:39:36]: Info: Screencasting with X11
[2023:05:17:10:39:36]: Info: SDR color coding [Rec. 601]
[2023:05:17:10:39:36]: Info: Color range: [JPEG]
[2023:05:17:10:39:36]: Info: vaGetDriverNameByIndex() failed with unknown libva error, driver_name = (null)
[2023:05:17:10:39:36]: Error: Couldn't initialize va display: unknown libva error
[2023:05:17:10:39:36]: Info: Screencasting with X11
[2023:05:17:10:39:36]: Info: SDR color coding [Rec. 601]
[2023:05:17:10:39:36]: Info: Color range: [JPEG]
[2023:05:17:10:39:36]: Info: vaGetDriverNameByIndex() failed with unknown libva error, driver_name = (null)
[2023:05:17:10:39:36]: Error: Couldn't initialize va display: unknown libva error
[2023:05:17:10:39:36]: Info: Screencasting with X11
[2023:05:17:10:39:36]: Info: SDR color coding [Rec. 601]
[2023:05:17:10:39:36]: Info: Color range: [JPEG]
[2023:05:17:10:39:36]: Info: vaGetDriverNameByIndex() failed with unknown libva error, driver_name = (null)
[2023:05:17:10:39:36]: Error: Couldn't initialize va display: unknown libva error
[2023:05:17:10:39:36]: Info: Screencasting with X11
[2023:05:17:10:39:36]: Info: SDR color coding [Rec. 601]
[2023:05:17:10:39:36]: Info: Color range: [JPEG]
[2023:05:17:10:39:36]: Info: vaGetDriverNameByIndex() failed with unknown libva error, driver_name = (null)
[2023:05:17:10:39:36]: Error: Couldn't initialize va display: unknown libva error
[2023:05:17:10:39:36]: Info: Encoder [vaapi] failed
[2023:05:17:10:39:36]: Info: Trying encoder [software]
[2023:05:17:10:39:36]: Info: Screencasting with X11
[2023:05:17:10:39:36]: Info: SDR color coding [Rec. 601]
[2023:05:17:10:39:36]: Info: Color range: [JPEG]
[2023:05:17:10:39:36]: Info: Screencasting with X11
[2023:05:17:10:39:36]: Info: SDR color coding [Rec. 601]
[2023:05:17:10:39:36]: Info: Color range: [JPEG]
[2023:05:17:10:39:36]: Info: Screencasting with X11
[2023:05:17:10:39:36]: Info: SDR color coding [Rec. 601]
[2023:05:17:10:39:36]: Info: Color range: [JPEG]
[2023:05:17:10:39:36]: Info: Screencasting with X11
[2023:05:17:10:39:36]: Info: SDR color coding [Rec. 709]
[2023:05:17:10:39:36]: Info: Color range: [JPEG]
[2023:05:17:10:39:36]: Error: Could not open codec [libx264]: Invalid argument
[2023:05:17:10:39:36]: Info: Screencasting with X11
[2023:05:17:10:39:36]: Info: SDR color coding [Rec. 601]
[2023:05:17:10:39:36]: Info: Color range: [JPEG]
[2023:05:17:10:39:36]: Warning: software: h264: replacing nalu prefix data
[2023:05:17:10:39:36]: Info:
[2023:05:17:10:39:36]: Info: // Ignore any errors mentioned above, they are not relevant. //
[2023:05:17:10:39:36]: Info:
[2023:05:17:10:39:36]: Info: Found encoder software: [libx264]
[2023:05:17:10:39:36]: Info: Adding avahi service Sunshine
[2023:05:17:10:39:36]: Info: Configuration UI available at [https://localhost:47990]
[2023:05:17:10:39:37]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:39:37]: Info: Avahi service Sunshine successfully established.
[2023:05:17:10:39:40]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:39:43]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:39:47]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:39:47]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:39:50]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:39:51]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:39:51]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:39:53]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:39:54]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:39:57]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:39:57]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:39:58]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:39:58]: Info: Executing [Desktop]
[2023:05:17:10:39:58]: Info: CLIENT CONNECTED
[2023:05:17:10:39:58]: Info: Detecting connected monitors
[2023:05:17:10:39:58]: Info: Screencasting with X11
[2023:05:17:10:39:58]: Info: Configuring selected monitor (0) to stream
[2023:05:17:10:39:58]: Info: Streaming display: DP-0 with res 1920x1080 offset by 0x0
[2023:05:17:10:39:58]: Info: SDR color coding [Rec. 601]
[2023:05:17:10:39:58]: Info: Color range: [MPEG]
[2023:05:17:10:39:58]: Info: Setting default sink to: [sink-sunshine-stereo]
[2023:05:17:10:39:58]: Info: Found default monitor by name: sink-sunshine-stereo.monitor
[2023:05:17:10:40:00]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:40:03]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:40:07]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:40:10]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:40:13]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:40:17]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:40:20]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:40:20]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:40:23]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:40:27]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:40:30]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:40:33]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:40:37]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:40:40]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:40:43]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:40:47]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:17:10:40:50]: Info: /CN=NVIDIA GameStream Client -- verified
```

# Docker方案

## Game on Whale (被 wolf 升级替代)

在docker容器里跑x11应用。可以直接在host上显示，也可以运行在headless服务器上，通过sunshine串流到本地。

- 支持声音
- 支持手柄
- 串流支持硬件加速（nvec, vaapi, libx264）

- 组件介绍：[Components Overview :: Games On Whales (games-on-whales.github.io)](https://games-on-whales.github.io/gow/components-overview.html)
- 效果展示：[Ramblings from Jessie: Docker Containers on the Desktop (jessfraz.com)](https://blog.jessfraz.com/post/docker-containers-on-the-desktop/#guis)

### 组件分析

![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20230516171521.png)

#### xorg

```
# host desktop模式下，容器使用host的xorg socket
XORG_SOCKET=/tmp/.X11-unix/X0
XORG_DISPLAY=:0

# headless模式
XORG_SOCKET=xorg
XORG_DISPLAY=:99

# headless模式下，启用xorg容器。该容器使用xorg volume，用于和其它容器共享。
- ${XORG_SOCKET}:/tmp/.X11-unix

XORG_IPC=shareable
ipc: ${XORG_IPC}  # xorg容器设置ipc为可共享

SHARED_IPC=service:xorg
ipc: ${SHARED_IPC} # 其它容器设置ipc为xorg容器
```

#### pulse

```
PULSE_SOCKET_HOST=pulse
PULSE_SOCKET_GUEST=/tmp/pulse/

# headless模式下，启用pulse容器。该容器使用pulse volume，用于和其它容器共享。
# 所有容器将volume pulse映射到该路径下
- ${PULSE_SOCKET_HOST}:${PULSE_SOCKET_GUEST}
```

#### udev

```
UDEVD_NETWORK=service:udevd
```

### 额外设置

#### headless display
[Monitor requirements :: Games On Whales (games-on-whales.github.io)](https://games-on-whales.github.io/gow/monitor.html)
- Edid.txt
- xorg-screen.conf

#### 使用闭源gpu驱动
[NVIDIA GPUs :: Games On Whales (games-on-whales.github.io)](https://games-on-whales.github.io/gow/nvidia.html)

- 设置nvidia container toolkit：`sudo nvidia-ctk runtime configure`
- env/nvidia.env：GUID选择显卡：`sudo nvidia-container-cli --load-kmods info`
- 运行时添加--gpu nvidia选项

#### multi gpu

xorg-primary

### 添加自定义app

需要基于base_app_image
```
docker build -t yfy/gow-yuzu \
  --build-arg BASE_APP_IMAGE=gameonwhales/base-app:sha-b51c691 \
  .
```
  
### 遇到的问题

#### dbus not found

sunshine中需要使用dbus
```
Failed to connect to system bus: Failed to connect to socket /run/dbus/system_bus_socket
```

host安装
```
apt install avahi-daemon
```

#### docker-compse需要更新到2.x

```
fyyuan@snode6 ➜  gow git:(master) ✗ ./run-gow --platform headless --app firefox pull
Your docker-compose is too old; please install v2.6.0 or later.
```

新的版本换了命令
> Note that Compose standalone uses the `-compose` syntax instead of the current standard syntax `compose`.  
For example type `docker-compose up` when using Compose standalone, instead of `docker compose up`.

需要卸载老版本，然后安装docker-compose-pulgin（需要apt添加了docker给仓库）
```
apt purge docker-compose
apt install docker-compose-pulgin
```

但是直接运行docker-compose会找不到命令
apt-file search docker-compose可以发现docker-compose-pulgin提供了该程序，使用软连接即可
```
 sudo ln -s /usr/libexec/docker/cli-plugins/docker-compose /bin/docker-compose
```

#### sunshine非局域网无法连接

打开网页显示403

sunshine log
```
[2023:05:15:14:16:33]: Error: Failed to create session: This hardware does not support NvFBC
[2023:05:15:14:16:33]: Error: Couldn't expose some/all drm planes for card: /dev/dri/card1

[2023:05:15:14:16:33]: Info: Trying encoder [nvenc]
[2023:05:15:14:16:33]: Info: Screencasting with X11

[2023:05:15:14:16:34]: Error: Could not open codec [libx264]: Invalid argument
```

发现log和在自己台式机上差不多，最后都是libx264无效参数。但是台式机是可以打开网页的，因此觉得是不是其它问题。尝试在台式机上设置配置文件为只能pc访问，发现网页一样报403错误。

因为sunshine默认的设置是只允许lan内访问。而我的情况是服务器有公网ip，虽然docker监听的是0.0.0.0的地址。但是容器内发现src地址不是lan就丢弃了。

尝试编辑配置文件，位于`$local_state/sunshine/sunshine.conf`（`local_state`定义于`user.env`），可以访问web了。但是moonlight无法连接。让检查udp 47999端口。查看sunshine日志发现，它直接尝试访问我这边NAT后的公网地址。

因此这样解决很麻烦。此时wireguard又排上用场了。可以使用wireguard让服务器和我这边直接位于一个LAN内！

解决后成功使用moonlight连接。由于app是firefox，因此可以打开网页，播放音乐有声音！
- 但是仍然无法播放b站视频。现象为一直加载视频
- 浏览器中文字体缺失。

![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20230515233000.png)

#### sunshine无法挂载路径闪退

尝试在A100 80g机器上跑。

莫名奇妙退出了
```
gow-sunshine-1  | chown: changing ownership of '/home/retro': Operation not permitted
gow-steam-1     | chown: changing ownership of '/home/retro': Operation not permitted
gow-steam-1 exited with code 1
gow-sunshine-1 exited with code 1

gow-xorg-1      | Setting DP-0 output to: 1920x1080@60
gow-xorg-1      | warning: output DP-0 not found; ignoring
```

发现是home目录权限导致的。（nfs挂载导致root无法写nfs下目录）

取消local_state挂载后，firefox可以跑。（但是感觉是CPU渲染？鼠标很卡。而且不知道什么原因，移动几下鼠标后就画面就卡住了。播放b站视频也会卡住）

多搞几下，最后直接闪退了
```
[2023:05:16:03:58:59]: Info: CLIENT CONNECTED
[2023:05:16:03:58:59]: Info: Detecting connected monitors
[2023:05:16:03:58:59]: Info: Screencasting with X11
[2023:05:16:03:58:59]: Info: Configuring selected monitor (0) to stream
[2023:05:16:03:58:59]: Info: Streaming display: DVI-D-0 with res 2560x1600 offset by 0x0
[2023:05:16:03:58:59]: Info: SDR color coding [Rec. 601]
[2023:05:16:03:58:59]: Info: Color range: [MPEG]
[2023:05:16:03:59:00]: Info: Setting default sink to: [sink-sunshine-stereo]
[2023:05:16:03:59:00]: Info: Found default monitor by name: sink-sunshine-stereo.monitor
[2023:05:16:03:59:52]: Info: CLIENT DISCONNECTED
[2023:05:16:03:59:52]: Info: Setting default sink to: [null]
[2023:05:16:03:59:52]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:16:03:59:52]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:16:03:59:55]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:16:03:59:55]: Info: /CN=NVIDIA GameStream Client -- verified
[2023:05:16:04:00:17]: Fatal: Hang detected! Session failed to terminate in 10 seconds.


gow-firefox-1   | [Child 359, MediaDecoderStateMachine #1] WARNING: Decoder=7ff8e3e17d00 Decode error: NS_ERROR_DOM_MEDIA_FATAL_ERR (0x806e0005) - Error no decoder found for video/avc: file /build/firefox-HNs9Ru/firefox-113.0.1+build1/dom/media/MediaDecoderStateMachineBase.cpp:164
```

#### docker-compose改为相对路径后sunshine exit2

将gow复制到root目录，然后修改docker-compose中关于edid等文件为相对路径。结果一运行，sunshine就exit 2。貌似是没有显示器？
```
gow-sunshine-1  | [2023:05:16:03:40:37]: Error: Missing extension: [EGL_EXT_image_dma_buf_import]
gow-sunshine-1  | [2023:05:16:03:40:37]: Info: Encoder [software] failed
gow-sunshine-1  | [2023:05:16:03:40:37]: Fatal: Couldn't find any working encoder
gow-sunshine-1 exited with code 2


[2023:05:16:03:43:41]: Info: Screencasting with KMS
[2023:05:16:03:43:41]: Error: Couldn't get primary file descriptor for Framebuffer [39]: Function not implemented
[2023:05:16:03:43:41]: Info: Found monitor for DRM screencasting
[2023:05:16:03:43:41]: Error: Failed to determine panel orientation, defaulting to landscape.
[2023:05:16:03:43:41]: Error: Missing extension: [EGL_EXT_image_dma_buf_import]
```

重新改为绝对路径后正常。screencasting确实不一样。KMS->X11

```
[2023:05:16:03:51:33]: Error: Environment variable WAYLAND_DISPLAY has not been defined
[2023:05:16:03:51:33]: Info: Detecting connected monitors
[2023:05:16:03:51:33]: Info: // Testing for available encoders, this may generate errors. You can safely ignore those errors. //
[2023:05:16:03:51:33]: Info: Trying encoder [nvenc]
[2023:05:16:03:51:33]: Info: Screencasting with NvFBC
[2023:05:16:03:51:35]: Error: Failed to create session:
[2023:05:16:03:51:48]: Info: Encoder [nvenc] failed
[2023:05:16:03:51:48]: Info: Trying encoder [vaapi]
[2023:05:16:03:51:48]: Info: Screencasting with X11
```

#### moonlight连接后直接退出

发现TITAN V也有显示输出，并且性能和RTX 3070差不多（3070 104%, 3070Ti 110%），遂尝试。

对比了log，**xorg连接DP-0是没问题的。sunshine中也没有明显不同的log**。

最后发现是系统内核版本为4.15，照理来说ubuntu20.04默认是5.4。更新重启后成功。

进入后发现vulkan画面渲染有问题（黑屏），opengl没问题。更新到nvidia-drive-530后解决。

## Wolf

GoW 的替代升级版本，仅使用单个镜像包含 moonlight server、PulseAudio、wayland、uinput等多个组件。一条命令 docker 命令就可以把服务起起来。

总结

- 优点
  - 配置简单，单条命令
- 缺点
  - 4K 串流会将 5800x 单个线程跑满，导致非常 laggy（确实是使用 NVENC 编码 h265），使用 1080p 就正常了。

### 设置

前提

- nvidia-container-toolkit
- `sudo cat /sys/module/nvidia_drm/parameters/modeset` 需要为 Y
  - nvidia-drm 和 DRM 有关，wolf 基于 wayland 需要使用 DRM
  - 没有开启的话需要更改模块参数，重新加载。由于 nvidia 模块通常被占用，因此一般无法直接重新加载 模块，需要修改参数，然后重启。
  ```
  sudo vim /etc/modprobe.d/nvidia-drm.conf
  options nvidia-drm modeset=1
  sudo update-initramfs -u
  ```

[games-on-whales/wolf: Stream virtual desktops and games running in Docker (github.com)](https://github.com/games-on-whales/wolf)

```
docker run \
    --name wolf \
    --network=host \
    -e XDG_RUNTIME_DIR=/tmp/sockets \
    -v /tmp/sockets:/tmp/sockets:rw \
    -e HOST_APPS_STATE_FOLDER=/mnt/Disk1/wolf \
    -v /mnt/Disk1/wolf:/etc/wolf:rw \
    -v /var/run/docker.sock:/var/run/docker.sock:rw \
    -e NVIDIA_DRIVER_CAPABILITIES=all \
    -e NVIDIA_VISIBLE_DEVICES=all \
    --gpus=all \
    --device /dev/dri/ \
    --device /dev/uinput \
    --device /dev/uhid \
    -v /dev/:/dev/:rw \
    -v /run/udev:/run/udev:rw \
    --device-cgroup-rule "c 13:* rmw" \
    ghcr.io/games-on-whales/wolf:stable
```

|                        |                     |                                                                                                                                                                     |
| ---------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| HOST_APPS_STATE_FOLDER | /etc/wolf           | The base folder in the host where the running apps will store permanent state                                                                                       |
| WOLF_RENDER_NODE       | /dev/dri/renderD128 | The default render node used for virtual desktops; see: [Multiple GPUs](https://games-on-whales.github.io/wolf/stable/user/configuration.html#_multiple_gpu)        |
| WOLF_ENCODER_NODE      | $WOLF_RENDER_NODE   | The default render node used for the Gstreamer pipelines; see: [Multiple GPUs](https://games-on-whales.github.io/wolf/stable/user/configuration.html#_multiple_gpu) |
#### 修改 app 存储数据的目录

> Since Wolf supports multiple streaming sessions at the same time and each session can run a different app, we need to make sure that each app has its own folder where it can store permanent data.  
> To achieve this, for each running app, Wolf will create a folder structure like this and then mount that as the home (`/home/retro`) for the docker container that will run the selected app.
```
${HOST_APPS_STATE_FOLDER}/${app_state_folder}/${app_title}
```

主要和一下三个变量有关

- `HOST_APPS_STATE_FOLDER`: defaults to `/etc/wolf`, can be changed via ENV
- `app_state_folder`: defaults to a unique identifier for each client so that every Moonlight session will have its own folder. Can be changed in the `config.toml` file
- `app_title`: the title of the app as defined in the `config.toml` file

### 遇到的问题

#### 黑屏

官方文档说刚开时黑屏是因为在下载镜像和 update。我在实验室服务器上始终是黑屏，ryzen 上测试，第一次黑屏，关闭应用，然后连接就正常了。

另一台服务器上却能够正常运行

发现问题在于 nvidia-drm 没有启用，启用后就好了
```
sudo vim /etc/modprobe.d/nvidia-drm.conf
options nvidia-drm modeset=1
sudo update-initramfs -u
```
#### steam 大屏幕启动卡在网络设置

提示 电量低，无法进行下一步操作

[无法启动 Steam - 网络问题 ·问题 #120 ·鲸鱼/狼的游戏 --- Unable to start Steam - network issues · Issue #120 · games-on-whales/wolf (github.com)](https://github.com/games-on-whales/wolf/issues/120)

解决办法

- 关闭大屏幕模式，在 config 中添加额外的环境变量 `STEAM_STARTUP_FLAGS=-steamos3`
- 我自己发现连点两下有线连接，就能跳过这里的设置，直接进入 steam 了
### windows compositor

成功串流 firefox 后，注意到除了浏览器，就只能看到顶上系统的任务条。有按钮可以打开终端，终端以分屏形式展示。但是窗口都没有关闭按钮。感觉可能是类似 iw3 那种窗口管理器？

Wolf support both [Sway](https://swaywm.org/) and [Gamescope](https://github.com/ValveSoftware/gamescope) compositor.
Sway is used by default, but some game may work better with one or the other.
Usage is controlled by environment variables on `[apps.runner]` configs:

- `RUN_SWAY=1` - enable Sway (Default for newer Wolf installation)
- `RUN_GAMESCOPE=1` - enable Gamescope

#### 实现细节（非常好的科普）

[Headless Wayland :: Games On Whales (games-on-whales.github.io)](https://games-on-whales.github.io/wolf/stable/dev/wayland.html)

已经知道了使用 Gstreamer 将图像串流到 Moonlight，问题是如**何从 upstream 获得图像**。

使用 X11 可以容易做到，但是有很多缺点

- - Xorg has to be up and running; we can run it via Docker in GOW but that’s not without its challenges.
- You need a physical monitor or a dummy plugged into your GPU (or some esoteric [EDID trick](https://games-on-whales.github.io/gow/monitor.html#_force_xorg_to_use_a_custom_edid) which works only when also performing a human sacrifice).
- It doesn’t scale well with multiple remote clients when sharing a single host

有没有一个办法可以直接从应用读取图像？
![](https://kroki.io/plantuml/svg/eNpljTEOwjAMRfecwgpzr4DEAhNTB4aqQxqcEuHEUepKIMTdaVNUQGxffu9_D1cfk8kmgOWQOGKUWu6EkNGKiT2hUm7CCHqXEnlrxHMcNDwUQFMLmtDOae8zOr616rn6JyanYUO-v0hHIy6VwyB5KmEuqiUezzNojsyxqOX-Xoaq2v5U1j__5JMX9jX4AkhsTU8=)

总结

通过自定义个一个 Wayland Compositor 实现了该功能。得益于 linux DRM，compositor 和 app 间可以通过 EGL 共享 GPU memory，避免需要在 CPU 和 GPU 间复制 2 次。目前存在的问题是从 compositor 到 Gstreamer 需要一次复制，使用 DMA buffer 也许可以解决该问题，但是目前存在一些问题，和 modifier 有关。
> What are modifiers? Modifiers add additional vendor specific properties to the internal pixel layout of a buffer. These modifiers are usually internally used by the GPU to speed up certain operations depending on characteristics of the hardware.

![](https://kroki.io/plantuml/svg/eNplUEtPwzAMvudXWOWcf4CQEI8eoAIxIQ7TDqF1R0QaR07GQ4j_TuNlWyputr-H7S--Wx8Mmwl6mgJ59GmVvh0CY5-M3zpUapxhhOYyBGd7kyz52MCPAlivEpppk6tbyzjS10b9Hvkv5MYGzpzdvqVXt8O9pI2JZxGyyK7y0mgTsSh7R7sh89YdkRdl7dhhNGXzTXsvBg8BfSnbx2cY2H4gx1p0h-zRFdn1UydYuRy01hfF7PjCYlh45zKqrz3R_2Oq7gq-t6vnmvN_GasyqeqKUKWhxAm0w1GgQwCH4oQs8lh080kDffpMkkD-ACxkpww=)

## nvidia runtime

docker --gpu all，可以直接运行nvidia-smi（需要设置docker daemon中使用nvidia runtime）

lxc添加gpu device后，set nvidia.runtime true后可以直接运行nvidia-smi
- 添加gpu后，/dev/可以看到许多nvidia设备

docker 特权容器 /dev下有host所有设备。而lxc特权容器，/dev下仍然只有少数设备。
### nvidia-container-tookit

现在已经更名

安装方式见：[Installing the NVIDIA Container Toolkit — NVIDIA Container Toolkit 1.16.2 documentation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
## 其它链接

docker steam：[mikenye/docker-steam: Valve's Steam, on Linux, in Docker. Perfect for gaming via Remote Play. (github.com)](https://github.com/mikenye/docker-steam)


# 使用多GPU提升性能？

### SLI

[Best Games With SLI Support 2023 [Complete List] - GPU Mag](https://www.gpumag.com/best-games-that-support-sli/)
[SLI_Best_Practices_2011_Feb.pdf (nvidia.com)](https://developer.download.nvidia.com/whitepapers/2011/SLI_Best_Practices_2011_Feb.pdf)

老
[Chapter 28. Configuring SLI and Multi-GPU FrameRendering (nvidia.com)](https://download.nvidia.com/XFree86/Linux-x86_64/396.51/README/sli.html)
新
[Chapter 31. Configuring SLI and Multi-GPU Mosaic (nvidia.com)](https://download.nvidia.com/XFree86/Linux-x86_64/530.30.02/README/sli.html)
[Chapter 6. Configuring X for the NVIDIA Driver](https://download.nvidia.com/XFree86/Linux-x86_64/530.30.02/README/editxconfig.html)

科普
[【官方双语】多显卡的历史 #电子速谈_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1sA411E7a2/?spm_id_from=333.788.recommend_more_video.5&vd_source=b01257db06b1514b2fb50663dd339833)
[【官方双语】跑得比SLI还快？NVLink#linus谈科技_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1dW411z7Zu/?vd_source=b01257db06b1514b2fb50663dd339833)
[【官方双语】SLI真的已死#linus谈科技_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1Zz4y1d7Mr/?spm_id_from=333.337.search-card.all.click&vd_source=b01257db06b1514b2fb50663dd339833)

## X11

[Windowing system - Wikipedia](https://en.wikipedia.org/wiki/Windowing_system#Display_server)
[Direct Rendering Manager - Wikipedia](https://en.wikipedia.org/wiki/Direct_Rendering_Manager#Kernel_mode_setting)

display server
- 任何需要显示GUI的应用都是client
- server和client间通过协议通信。
- 从内核获得input（键盘、鼠标、触控板），并将其发送给不同的client
- 声音通常不负责

X11
- 需要第二个程序(composting window manager)，负责窗口的组合(composting)。
- 常见实现：x.org, xfree86
![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20230516221140.png)


wayland不同
- 包含了compositing
- client可以直接访问framebuffer。Wayland compositors communicate with Wayland clients over the [Wayland display server protocol](https://en.wikipedia.org/wiki/Wayland_(display_server_protocol) "Wayland (display server protocol)"). This protocol defines that clients can directly write data into the framebuffer using the [EGL](https://en.wikipedia.org/wiki/EGL_(OpenGL) "EGL (OpenGL)") [rendering API](https://en.wikipedia.org/wiki/Rendering_API "Rendering API").
![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20230516221917.png)


## DRM

linux内核模块

The [Linux kernel](https://en.wikipedia.org/wiki/Linux_kernel "Linux kernel") already had an [API](https://en.wikipedia.org/wiki/Application_programming_interface "Application programming interface") called [fbdev](https://en.wikipedia.org/wiki/Linux_framebuffer "Linux framebuffer"), used to manage the [framebuffer](https://en.wikipedia.org/wiki/Framebuffer "Framebuffer") of a [graphics adapter](https://en.wikipedia.org/wiki/Graphics_adapter "Graphics adapter"),but it couldn't be used to handle the needs of modern 3D-accelerated [GPU](https://en.wikipedia.org/wiki/GPU "GPU")-based video hardware.
- 需要队列
These devices usually require setting and managing a command queue in [their own memory](https://en.wikipedia.org/wiki/Video_RAM "Video RAM") to dispatch commands to the GPU and also require management of buffers and free space within that memory
- 避免了不同设备同时设置gpu导致冲突。

### 架构/API

用户需要使用的话，需要通过系统调用。但是DRM没有定义新的系统调用，而是遵从了unix万物即文件的想法，通过文件命令空间将GPU暴露出来。位于/dev/层次下的device文件（在/dev/dri/cardX）。用户进程打开dev文件，并通过ioctl调用DRM。

用户空间库libdrm将DRM ioctl API包装为C函数。

DRM包含通用的DRM core和硬件专用的DRM driver两部分。DRM core provides the basic framework where different DRM drivers can register and also provides to user space a minimal set of ioctls with common, hardware-independent functionality。当DRM driver提供了增强的API时，用户空间的libdrm也需要额外的libdrm-*driver*进行扩展。

![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20230516215751.png)


### 两大部分

- GEM（Graphics Execution Manager）：
  - 管理显卡memory。Due to the increasing size of [video memory](https://en.wikipedia.org/wiki/Video_memory "Video memory") and the growing complexity of graphics APIs such as [OpenGL](https://en.wikipedia.org/wiki/OpenGL "OpenGL"), the strategy of reinitializing the graphics card state at each [context switch](https://en.wikipedia.org/wiki/Context_switch "Context switch") was too expensive, performance-wise. Also, modern [Linux desktops](https://en.wikipedia.org/wiki/Linux_desktop "Linux desktop") needed an optimal way to share off-screen buffers with the [compositing manager](https://en.wikipedia.org/wiki/Compositing_manager "Compositing manager"). These requirements led to the development of new methods to manage graphics [buffers](https://en.wikipedia.org/wiki/Data_buffer "Data buffer") inside the kernel. T
- KMS（Kernel Mode Setting）
  - 用于设置显卡输出分辨率，In order to work properly, a video card or graphics adapter must set a _[mode](https://en.wikipedia.org/wiki/Framebuffer#Display_modes "Framebuffer")_—a combination of [screen resolution](https://en.wikipedia.org/wiki/Screen_resolution "Screen resolution"), [color depth](https://en.wikipedia.org/wiki/Color_depth "Color depth") and [refresh rate](https://en.wikipedia.org/wiki/Refresh_rate "Refresh rate")—that is within the range of values supported by itself and the attached [display screen](https://en.wikipedia.org/wiki/Computer_monitor "Computer monitor").
  - KMS has been adopted to such an extent that certain drivers which lack 3D acceleration (or for which the hardware vendor doesn't want to expose or implement it) nevertheless implement the KMS API without the rest of the DRM API, allowing display servers (like [Wayland](https://en.wikipedia.org/wiki/Wayland_(protocol) "Wayland (protocol)")) to run with ease.[[47]](https://en.wikipedia.org/wiki/Direct_Rendering_Manager#cite_note-47)

render node：将计算和渲染的部分剥离开来，避免只有特权用户才能访问gpu。
The "render nodes" concept tries to solve these scenarios by splitting the DRM user space API into two interfaces – one privileged and one non-privileged – and using separate device files (or "nodes") for each one. For every GPU found, its corresponding DRM driver—if it supports the render nodes feature—creates a device file `/dev/dri/renderD_X_`, called the _render node_, in addition to the primary node `/dev/dri/card_X_`

### 硬件支持

展示了AMD的两套驱动：Mesa和AMD自身的
![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20230516214345.png)


## headless串流

就是需要一个display adapter，无论是虚拟的还是物理的都可以

[(7) Moonlight Streaming without Monitor (no dummy plug needed) : MoonlightStreaming (reddit.com)](https://www.reddit.com/r/MoonlightStreaming/comments/rzpcpc/moonlight_streaming_without_monitor_no_dummy_plug/)

[如何在没有显示器的情况下运行 Parsec？这是适合您的虚拟监视器解决方案（间接显示） |由 Arche Basic |中等 --- How to run Parsec without monitor? Here’s a virtual monitor solution for you (Indirect Display) | by Arche Basic | Medium](https://archeb.medium.com/how-to-run-parsec-without-monitor-heres-a-virtual-monitor-solution-for-you-indirect-display-ecba5173b86a)

# 