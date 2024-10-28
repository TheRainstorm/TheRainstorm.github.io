---
title: linux 相关-linux 使用
date: 2022-11-06 18:14:50
tags:
  - tty
categories:
  - 学习笔记
---
记录从 OS 使用者的角度，记录 linux 的一些经验

<!-- more -->
## tty, pts

- tty 表示终端 (terminal or console) 的统称。tty(tele typerwriter) 电传打字机为早期电脑的输入输出设备，后面被显示器和键盘取代。
  - ctrl alt + F1-F6 对应 6 个终端
  - ctrl alt + F7 对应图形化界面
- pts(pseudo terminal slave) 表示伪终端。是一个程序（终端仿真器 teminal emulators）

```bash
who #查看当前所有登录用户及终端
➜  ~ who
yfy      :1           2022-10-24 14:26 (:1)
yfy      pts/1        2022-10-16 15:36 (tmux(1158265).%0)
yfy      pts/2        2022-10-24 14:43 (192.168.1.180)
yfy      pts/3        2022-10-23 18:57 (tmux(1158265).%5)
yfy      pts/4        2022-10-16 15:37 (tmux(1158265).%2)
yfy      pts/6        2022-10-16 15:38 (tmux(1158265).%3)
yfy      pts/7        2022-10-16 15:38 (tmux(1158265).%4)
yfy      pts/12       2022-10-24 00:36 (tmux(1158265).%0)
who -m # 查看当前用户

echo "hello" > /dev/pty/x   #直接给对应终端发送消息
```


## 生活相关

### 禁止休眠

[How to Disable Suspend and Hibernation Modes In Linux (tecmint.com)](https://www.tecmint.com/disable-suspend-and-hibernation-in-linux/)

```
sudo systemctl status sleep.target suspend.target hibernate.target hybrid-sleep.target
```

### 禁止关闭笔记本盖子休眠

```
vim /etc/systemd/logind.conf

HandleLidSwitch=lock   # 从suspend改为lock
```

man logind.conf
> Controls how logind shall handle the system power, reboot and sleep keys and the lid switch to trigger actions such as system power-off, reboot or suspend. Can be one of "ignore", "poweroff", "reboot", "halt", "kexec", "suspend", "hibernate", "hybrid-sleep", "suspend-then-hibernate", "lock", and "factory-reset".
>
> If "ignore", systemd-logind will never handle these keys. If "lock", all running sessions will be screen-locked; otherwise, the specified action will be taken in the respective event. Only input devices with the "power-switch" udev tag will be watched for key/lid switch events.
>
> HandlePowerKey= defaults to "poweroff", HandleRebootKey= defaults to "reboot", HandleSuspendKey= defaults to "suspend", HandleHibernateKey= defaults to "hibernate", HandlePowerKeyLongPress= defaults to "ignore", HandleRebootKeyLongPress= defaults to "poweroff", HandleSuspendKeyLongPress= defaults to "hibernate", HandleHibernateKeyLongPress= defaults to "ignore".  HandleLidSwitch= defaults to "suspend".  HandleLidSwitchExternalPower= is completely ignored by default (for backwards compatibility) — an explicit value must be set before it will be used to determine behaviour.  HandleLidSwitchDocked= defaults to "ignore". If the system is inserted in a docking station, or if more than one display is connected, the action specified by HandleLidSwitchDocked= occurs; if the system is on external power the action (if any) specified by HandleLidSwitchExternalPower= occurs; otherwise the HandleLidSwitch= action occurs.
>
### 连接 wifi

#### iw,iwconfig 等底层工具

- iw
- iwlist
- wpa_supplicant: 用于连接 WPA 加密的 wifi

不使用 networkmanger 等工具，需要

- iw 连接 wifi
  - ifup interface
- 开启 dhcpclient 获得 ip

[Network configuration/Wireless - ArchWiki (archlinux.org)](https://wiki.archlinux.org/title/Network_configuration/Wireless)

```
█▓▒░root@king3399█▓▒░ Mon Aug 07 03:07:46pm
~/ iw dev wlan0 station dump
Station 3c:cd:57:f5:da:85 (on wlan0)
        inactive time:  0 ms
        rx bytes:       26025
        rx packets:     153
        tx bytes:       22842
        tx packets:     121
        tx failed:      0
        signal:         -63 dBm
        tx bitrate:     234.0 MBit/s
        rx bitrate:     390.0 MBit/s
        authorized:     yes
        authenticated:  yes
        associated:     yes
        WMM/WME:        yes
        TDLS peer:      no
        DTIM period:    1
        beacon interval:100
        short slot time:yes
        connected time: 60 seconds
        current time:   1691392108815 ms
█▓▒░root@king3399█▓▒░ Mon Aug 07 03:08:28pm
~/ iw dev wlan0 link
Connected to 3c:cd:57:f5:da:85 (on wlan0)
        SSID: ACSA-706-5G
        freq: 5240
        RX: 29153 bytes (171 packets)
        TX: 24932 bytes (142 packets)
        signal: -60 dBm
        rx bitrate: 390.0 MBit/s
        tx bitrate: 234.0 MBit/s

        bss flags:      short-slot-time
        dtim period:    1
        beacon int:     100
```

扫描 wifi

```
iwlist wlan0 scan |grep ESSID    # 列出wifi
```

#### iwd

pve 设置 wifi 和普通 debian 差不多，但是应该避免使用 networkmanager 等高级的网络服务。因为这些是为桌面环境设计的，不适合 pve。[WLAN - Proxmox VE](https://pve.proxmox.com/wiki/WLAN)
> Setting up the Wi-Fi itself is not different in Proxmox VE than with a default Debian installation. But **avoid** installing advanced, network daemons like **NetworkManager** as those are normally suited for desktops only and may interfere with Proxmox VEs network requirements.

debian 使用 wifi 方法总结：[WiFi/HowToUse - Debian Wiki](https://wiki.debian.org/WiFi/HowToUse#Network_Configuration)

- iwd 作为 NetworkManager, and systemd-networkd 等的 backend
- 可以自己使用 iwd + systemd-resolved 打造一个最轻量的网络栈

[iwd - ArchWiki (archlinux.org)](https://wiki.archlinux.org/title/iwd)

如果想要单独使用 iwd，需要 `/etc/iwd/main.conf` 开启网络配置（否则不会 dhcp 获得 v4 地址）

```
[General]
EnableNetworkConfiguration=true
```

```
[IPv4]
Address=192.168.36.216
Netmask=255.255.255.0
Gateway=192.168.36.1
Broadcast=192.168.36.255
DNS=192.168.36.1
```

#### NetworkManger

GUI：基于 GTK 的**nm-connection-editor**
CLI：

- nmtui：使用起来很简单，可以编辑有线无线配置，激活连接等。
- nmcli：更加底层的命令行，功能还是很强大的

##### nmtui 

简单的话，直接使用 nmtui，选择 Wifi 输入密码即可。

![image.png](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20240918235326.png)


##### nmcli 基本使用

```
nmcli conn
nmcli conn edit xxx
```

##### WPA2 Enterprise 连接配置（eduroam）

WPA2 Enterprise 导致的 wifi 无法连接问题[(7) Cannot Connect to College WIFI using NetworkManager : archlinux (reddit.com)](https://www.reddit.com/r/archlinux/comments/pb3r0f/cannot_connect_to_college_wifi_using/)

```
Failed to determine AP security information
```

[12.10 - Connect to a WPA2-Enterprise Connection via CLI (no desktop) - Ask Ubuntu](https://askubuntu.com/questions/262491/connect-to-a-wpa2-enterprise-connection-via-cli-no-desktop)

```bash
nmcli con add type wifi ifname wlan0 con-name eduroam ssid eduroam 

You may edit the following settings: connection, 802-11-wireless (wifi), 802-11-wireless-security (wifi-sec), 802-1x, ethtool, match, ipv4, ipv6, hostname, tc, proxy
nmcli> set 802-1x.eap peap
nmcli> set 802-1x.phase2-auth mschapv2
nmcli> set 802-1x.identity xxxxx
nmcli> set 802-1x.password xxxxx
nmcli> set wifi-sec.key-mgmt wpa-eap
nmcli> save
Connection 'eduroam' (ae79dc6c-b660-469d-9ecb-3a29504de969) successfully updated.
nmcli> activate
```

#### netplan 连接 wifi 配置

[How to configure wifi in Ubuntu (linuxhint.com)](https://linuxhint.com/configure-wifi-ubuntu/)

```
# netplan yaml
network:
  version: 2
  renderer: networkd
  wifis:
      wlan0:
        optional: true
        dhcp4: true
        dhcp6: true
        access-points:
          "ustcnet": {}   # 没有密码
          "ssid2":
            password: "aaa"
```

通过 iwconfig 查看是否连接成功，出现 ESSID 则为成功

```
➜  ~ iwconfig wlan0
wlan0     IEEE 802.11  ESSID:"P2W_5G"
          Mode:Managed  Frequency:5.745 GHz  Access Point: 1C:40:E8:11:89:CF
          Bit Rate=234 Mb/s   Tx-Power=22 dBm
          Retry short limit:7   RTS thr:off   Fragment thr:off
          Power Management:on
          Link Quality=70/70  Signal level=-35 dBm
          Rx invalid nwid:0  Rx invalid crypt:0  Rx invalid frag:0
          Tx excessive retries:0  Invalid misc:7   Missed beacon:0
```

### 音乐

[USB Bluetooth passthrough KVM : VFIO (reddit.com)](https://www.reddit.com/r/VFIO/comments/q0oq9e/usb_bluetooth_passthrough_kvm/)
[The 5 Best Command Line Music Players for Linux (tecmint.com)](https://www.tecmint.com/command-line-music-players-for-linux/)

```
sudo apt install cmus
cmus

5 # 浏览当前文件夹
```

使用 vlc

```
cvlc file.mp3
```

### 蓝牙

[Bluetooth - ArchWiki (archlinux.org)](https://wiki.archlinux.org/title/bluetooth)

命令行工具`bluetoothctl`

1. (optional) Select a default controller with `select _MAC_address_`.
2. (optional) Enter `power on` to turn the power to the controller on if the device is set to off. It is on by default; see [#Default adapter power state](https://wiki.archlinux.org/title/bluetooth#Default_adapter_power_state).
3. Enter `devices` to get the MAC address of the device with which to pair.
4. Enter device discovery mode with `scan on` command if device is not yet on the list.
5. Turn the agent on with `agent on` or choose a specific agent: if you press tab twice after `agent` you should see a list of available agents. A bluetooth agent is what manages the Bluetooth 'pairing code'. It can either respond to a 'pairing code' coming in, or can send one out. The `default-agent` should be appropriate in most cases.[[1]](https://askubuntu.com/questions/763939/bluetoothctl-what-is-a-bluetooth-agent)
6. Enter `pair _MAC_address_` to do the pairing (tab completion works).
7. If using a device without a PIN, one may need to manually trust the device before it can reconnect successfully. Enter `trust _MAC_address_` to do so.
8. Enter `connect _MAC_address_` to establish a connection.


## 桌面环境

### 基本概念

什么是 Desktop Environment？
> A desktop environment bundles together a variety of components to provide common graphical user interface elements such as icons, toolbars, wallpapers, and desktop widgets.

- 通常也自带了 window manager 和 Display manager

[window manager](https://wiki.archlinux.org/title/Window_manager "Window manager") 
- DE 通常自带一个 window manager，但是也可以替换成兼容的其它 window manager
- Window managers are X clients that control the appearance and behaviour of the frames ("windows") where the various graphical applications are drawn.
- Window manager 时 Xorg 的概念，Wayland 下对应的组件是 Compositor。**Window managers are unique to Xorg**. The equivalent of window managers on Wayland are called [compositors](https://wiki.archlinux.org/title/Wayland#Compositors "Wayland") because they also act as [compositing window managers](https://en.wikipedia.org/wiki/Compositing_window_manager "wikipedia:Compositing window manager").
- 类型
  - stacking
  - tiling
    - i3

[Display manager - ArchWiki (archlinux.org)](https://wiki.archlinux.org/title/Display_manager)
- A [display manager](https://en.wikipedia.org/wiki/X_display_manager_(program_type) "wikipedia:X display manager (program type)"), or **login manager**, is typically a graphical user interface that is displayed at the end of the boot process in place of the default shell.
- **[GDM](https://wiki.archlinux.org/title/GDM "GDM")** — [GNOME](https://wiki.archlinux.org/title/GNOME "GNOME") display manager.
- **[LightDM](https://wiki.archlinux.org/title/LightDM "LightDM")** — Cross-desktop display manager, can use various front-ends written in any toolkit.

gnome-shell：shell 就是我们可以看到的图形界面

### display manager

#### lightdm

效果还是不错的，并且启动 xfce4 和 gnome 都没有遇到问题。
![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20240912193508.png)

安装时会提示和 gdm 冲突
```
apt install lightdm
```

![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20240912193122.png)

*好像需要进入 graphical.target 才能正常使用。gdm 可以在 multi-user.target 下 通过  sudo systemctl start gdm 启动图形界面。lightdm systemctl start 报错*
#### gdm3

选中用户，输入密码时右下脚才会出现齿轮来切换桌面环境。

切换 wayland 和 xorg[How to Enable or Disable Wayland on Ubuntu 22.04 Desktop – TecAdmin](https://tecadmin.net/how-to-enable-or-disable-wayland-on-ubuntu-22-04-desktop/)

```
vim /etc/gdm3/custom.conf

[daemon]
# Uncomment the line below to force the login screen to use Xorg
#WaylandEnable=false
```

也可以配置是否自动登陆

```
[daemon]
AutomaticLoginEnable=True
AutomaticLogin=yfy
```

### gnome

### xfce

参考资料

- [xfce:getting-started [Xfce Docs]](https://docs.xfce.org/xfce/getting-started)
- 设置 display manager：[xfce:display_managers [Xfce Docs]](https://docs.xfce.org/xfce/display_managers)
  - ubuntu 22.04 位于 `/usr/share/xsessions/xfce.desktop`

#### 安装

debian
- ubuntu 貌似直接安装 xubuntu-desktop 即可，但是我试了 debian 安装方式也没问题
```
apt install xfce4 xfce4-goodies
```

xfce4: This package is a metapackage; it depends on the core packages of the Xfce4 desktop environment and recommends some extra Xfce4 packages.  If you intend to use Xfce4 and want the full experience then installing this package and the packages it Recommends is a great place to start.

[xfce4-goodies](https://packages.debian.org/xfce4-goodies "DebianPkg") is a metapackage that will install many useful plugins and applications related to Xfce. It's a suggested package for standard users that want a complete Xfce desktop experience, however you may have a more "minimal" installation by only installing the specific packages that you want from the list below.

### KDE

参考资料

- ubuntu 安装 KDE：[How to Install KDE on Ubuntu [Beginner's Guide] (itsfoss.com)](https://itsfoss.com/install-kde-on-ubuntu/)


KDE 和 KDE Plasma
> Since they were not essentially a desktop environment anymore, a few years ago, they segregated the desktop environment. Plasma is the desktop environment and KDE is the umbrella project responsible for the development of Plasma desktop and a bunch of other applications.

- kde-full: 1 GB
- kde-standard: 273 MB
- kde-plasma-desktop: 175 MB

```
sudo apt install kde-standard
```

SDDM: KDE 自带的 diskplay manager


## 系统

### 遇到的问题

#### 打不开 setting

[Settings window does not open in Ubuntu 22.04 - Ask Ubuntu](https://askubuntu.com/questions/1420736/settings-window-does-not-open-in-ubuntu-22-04)
```
sudo apt-get install --reinstall gnome-control-center
```

#### 无法 X11 forwarding

想要测试 x11 需要配置 XServer，在 git bash 等终端是不行的，需要使用 mobaxterm

```shell
debug1: Remote: /staff/fyyuan/.ssh/authorized_keys:3: key options: agent-forwarding port-forwarding pty user-rc x11-forwarding
debug1: Remote: /staff/fyyuan/.ssh/authorized_keys:3: key options: agent-forwarding port-forwarding pty user-rc x11-forwarding
debug1: Requesting X11 forwarding with authentication spoofing.
debug1: Remote: No xauth program; cannot forward X11.
X11 forwarding request failed on channel 0
```

[ssh - No xauth program; cannot forward X11 - Unix & Linux Stack Exchange](https://unix.stackexchange.com/questions/552601/no-xauth-program-cannot-forward-x11)

解决
```
apt install xauth
```


# 硬件相关

## 关闭 beep/bell

[Turn off beep / bell on linux terminal - Linux Tutorials - Learn Linux Configuration](https://linuxconfig.org/turn-off-beep-bell-on-linux-terminal)

## 查看 CPU,cache

查看 cache 大小

- vim /proc/cpuinfo
  - cache_size 不知道具体含义，L2/per core？
  - cache_alignment 为 L1 cache line 大小？

```
cache size      : 512 KB
clflush size    : 64
cache_alignment : 64
address sizes   : 48 bits physical, 48 bits virtual
```

- lscpu
  - 很详细，可以看到 cpu flag, numa, cache

```
Caches (sum of all):
  L1d:                   256 KiB (8 instances)
  L1i:                   256 KiB (8 instances)
  L2:                    4 MiB (8 instances)
  L3:                    32 MiB (1 instance)
NUMA:
  NUMA node(s):          1
  NUMA node0 CPU(s):     0-15
```

- getconf -a | grep CACHE
  - 可以看到 cache line 大小

```
LEVEL1_ICACHE_SIZE                 32768
LEVEL1_ICACHE_ASSOC
LEVEL1_ICACHE_LINESIZE             64
LEVEL1_DCACHE_SIZE                 32768
LEVEL1_DCACHE_ASSOC                8
LEVEL1_DCACHE_LINESIZE             64
LEVEL2_CACHE_SIZE                  524288
LEVEL2_CACHE_ASSOC                 8
LEVEL2_CACHE_LINESIZE              64
LEVEL3_CACHE_SIZE                  33554432
LEVEL3_CACHE_ASSOC                 0
LEVEL3_CACHE_LINESIZE              64
LEVEL4_CACHE_SIZE
LEVEL4_CACHE_ASSOC
LEVEL4_CACHE_LINESIZE
```

## lspci

```
apt install pciutils
```

### 常用选项

```
lspci -k  #查看内核驱动

lspci -nn #查看设备id

lspci -vv # 查看pcie链路速度：LnkCap, LnkSta
- 2.5 GT/s = PCI-e gen 1
- 5 GT/s = PCI-e gen 2
- 8 GT/s = PCI-e gen 3
```

### 指定设备

```
-s [[[[<domain>]:]<bus>]:][<device>][.[<func>]]
```

- domain: 0 to ffff
- bus: 0-ff
- device: 0-ff
- function: 0-7
- 可以省去或者设置为`*`表示任意值

```
-d [vendor]:[device][:class[:prog-if]]
```

- vendor: e.g. 10de
- device: : e.g. 1c02

### 查看树状结构

```
lspci -tv
```

- 03.1：是 slot and function number of the PCIe root hub
- [08]表示在其后面的设备的 bus 为 08
- 00.0 为 device 和 function 编号

```
+-03.1-[08]--+-00.0  NVIDIA Corporation GP106 [GeForce GTX 1060 3GB]
           |            \-00.1  NVIDIA Corporation GP106 High Definition Audio Controller
```

## 监控 (温度、功耗)

### SSD 温度

[Linux find NVMe SSD temperature using command line - nixCraft (cyberciti.biz)](https://www.cyberciti.biz/faq/linux-find-nvme-ssd-temperature-using-command-line/)

```
apt install nvme-cli

sudo nvme smart-log /dev/nvme0
```

### CPU 频率、功耗

```
lscpu -e
CPU NODE SOCKET CORE L1d:L1i:L2:L3 ONLINE    MAXMHZ    MINMHZ      MHZ
  0    0      0    0 0:0:0:0           是 4850.1948 2200.0000 3023.077
  1    0      0    1 1:1:1:0           是 4850.1948 2200.0000 3167.647
  2    0      0    2 2:2:2:0           是 4850.1948 2200.0000 2529.517
  3    0      0    3 3:3:3:0           是 4850.1948 2200.0000 2895.147
  4    0      0    4 4:4:4:0           是 4850.1948 2200.0000 3068.640
  5    0      0    5 5:5:5:0           是 4850.1948 2200.0000 2814.150
  6    0      0    6 6:6:6:0           是 4850.1948 2200.0000 3097.454
  7    0      0    7 7:7:7:0           是 4850.1948 2200.0000 3148.684
  8    0      0    0 0:0:0:0           是 4850.1948 2200.0000 2938.599
  9    0      0    1 1:1:1:0           是 4850.1948 2200.0000 3376.774
 10    0      0    2 2:2:2:0           是 4850.1948 2200.0000 4420.665
 11    0      0    3 3:3:3:0           是 4850.1948 2200.0000 2996.655
 12    0      0    4 4:4:4:0           是 4850.1948 2200.0000 3100.166
 13    0      0    5 5:5:5:0           是 4850.1948 2200.0000 2894.990
 14    0      0    6 6:6:6:0           是 4850.1948 2200.0000 3244.797
 15    0      0    7 7:7:7:0           是 4850.1948 2200.0000 2897.287
```

[CPU frequency scaling - ArchWiki (archlinux.org)](https://wiki.archlinux.org/title/CPU_frequency_scaling)

查看功耗

```
sudo turbostat
```

## 音频

### ALSA

```
yfy@TianYi310 ➜  /dev aplay -l
**** PLAYBACK 硬體裝置清單 ****
card 0: PCH [HDA Intel PCH], device 0: CX20751/2 Analog [CX20751/2 Analog]
  子设备: 1/1
  子设备 #0: subdevice #0
card 0: PCH [HDA Intel PCH], device 3: HDMI 0 [HDMI 0]
  子设备: 1/1
  子设备 #0: subdevice #0
card 0: PCH [HDA Intel PCH], device 7: HDMI 1 [HDMI 1]
  子设备: 1/1
  子设备 #0: subdevice #0
card 0: PCH [HDA Intel PCH], device 8: HDMI 2 [HDMI 2]
  子设备: 1/1
  子设备 #0: subdevice #0
card 0: PCH [HDA Intel PCH], device 9: HDMI 3 [HDMI 3]
  子设备: 1/1
  子设备 #0: subdevice #0
card 0: PCH [HDA Intel PCH], device 10: HDMI 4 [HDMI 4]
  子设备: 1/1
  子设备 #0: subdevice #0
```

```
root@p2w \u@\h:\w\$ cat /proc/asound/modules
 0 snd_usb_audio
 
root@p2w \u@\h:\w\$ arecord -l
**** List of CAPTURE Hardware Devices ****
card 0: Lanseyaoji [Lanseyaoji], device 0: USB Audio [USB Audio]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
```

#### arecord, aplay

arecord, aplay - command-line sound recorder and player for ALSA soundcard driver

`arecord -d 10 -f cd -t wav -D copy foobar.wav` will record foobar.wav as a 10-second, CD-quality wave file

aplay 播放貌似只支持 WAVE 格式，mp3 播放是噪音

```
yfy@TianYi310 ➜  Downloads aplay 'Laco - NEXUS.mp3'
正在播放 原始資料 'Laco - NEXUS.mp3' : Signed 16 bit Little Endian, 频率8000Hz， Mono
^C被信号 中断...退出
yfy@TianYi310 ➜  Downloads aplay filename.wav
正在播放 WAVE 'filename.wav' : Signed 16 bit Little Endian, 频率44100Hz， Stereo
```

##### aplay -l 没有设备

但是 root 用户有。这也导致 pulseaudio list sinks 时只有伪设备。

[alsa - How do I get sound with an HDA card? - Ask Ubuntu](https://askubuntu.com/questions/706602/how-do-i-get-sound-with-an-hda-card)
[audio - ALSA does not find sound devices as user but can as root after kernel upgrade - Super User](https://superuser.com/questions/469036/alsa-does-not-find-sound-devices-as-user-but-can-as-root-after-kernel-upgrade)

没有尝试参考 1，而是直接修改了/dev/snd 的权限 777（添加用户到 audio 组没有作用），问题解决。

### PulseAudio

#### system-wide 模式和 per-user 模式

推荐使用 per-user 模式，system-wide 模式不安全。[Running PulseAudio as System-Wide Daemon – PulseAudio (www.freedesktop.org)](https://www.freedesktop.org/wiki/Software/PulseAudio/Documentation/User/SystemWide/)

per-user 模式，每个用户需要使用时启动 pulseaudio。system 模式适合没有普通用户的嵌入式设备

#### 运行 server

[Running (www.freedesktop.org)](https://www.freedesktop.org/wiki/Software/PulseAudio/Documentation/User/Running/)

有桌面环境情况下一般情况下会自动启动。也可以手动启动

```
pulseaudio --kill # 关闭pulseaudio server

pulseaudio # 运行在前台，ctrl-C结束。便于实时查看日志
pulseaudio --daemonize # daemon模式，运行在后台
pulseaudio -vv --log-time # 显示更多log
```

`~/.config/pulse/`优先级高于`/etc/pulse/`

- default.pa : **The default PulseAudio Startup Script** Commands in this file run when the daemon is started or restarted. Run `man default.pa` for documentation.
- daemon.conf: **The PulseAudio daemon configuration file** Run `man pulse-daemon.conf` for documentation.
- system.pa：仅用于 system-wide 模式

#### 控制命令 pactl

[CLI (www.freedesktop.org)](https://www.freedesktop.org/wiki/Software/PulseAudio/Documentation/User/CLI/)

通过`pactl`命令和 pulseaudio daemon 进行交互

```
pactl list sources # 查看输入设备
pactl list sinks # 查看输出设备

# 调节音量
pactl set-sink-mute <device> toggle/true/false  # device tab自动补全
pactl set-sink-volume <device> 30%
```

#### 让麦克风输出到扬声器

[sound - How to hear my voice in speakers with a mic? - Ask Ubuntu](https://askubuntu.com/questions/123798/how-to-hear-my-voice-in-speakers-with-a-mic)

```
pactl load-module module-loopback latency_msec=1

# stop
pactl unload-module module-loopback
```

另一个办法直接使用 alsa 命令。

```
arecord -f cd - | aplay - # 延迟很高
arecord -f cd - | tee output.wav | aplay - #  play while saving

arecord --buffer-time=1 - | aplay --buffer-time=1 - # 改善延迟
```

##### 将指定 source 输出到指定 sink

[Modules – PulseAudio (www.freedesktop.org)](https://www.freedesktop.org/wiki/Software/PulseAudio/Documentation/User/Modules/#module-loopback)

```
pactl load-module module-loopback latency_msec=1 source=2 sink=0  # 数字为index
```

#### 录指定应用声音

*p.s 关键点*

- 直接对输出到扬声器的声音录制，自己就听不到声音了。使用 combined，对输出到 headphone 的声音复制一份，然后对其进行录制

参考：[Linux audio recording guide (ro-che.info)](https://ro-che.info/articles/2017-07-21-record-audio-linux)

1. Create a “null” sink that you will be recording. Let’s call it `recording`.
2. **Create a combined sink that will send its input to both headphones and the `recording` sink.** Otherwise, you will be able to record a stream but not hear it yourself. So, let’s call this sink `combined`.
3. Direct the sound from the specific applications you want to record into the combined sink.
4. Record the monitor of the `recording` sink to a file.

添加 combined 设备

```
pacmd load-module module-null-sink sink_name=recording sink_properties=device.description=recording
pacmd load-module module-combine-sink sink_name=combined sink_properties=device.description=combined \
  slaves=recording,alsa_output.pci-0000_00_1f.3.analog-stereo
```

将 combined 设置为默认输出，然后开始录制

```
parecord --channels=1 -d recording.monitor filename.wav
```

- parecord 录制没有压缩，只能使用 parecord 录制吗？

### 音频网络串流

#### 参考

- linux 到安卓设备：[How to stream my GNU/Linux audio output to Android devices over WI-FI? - Super User](https://superuser.com/questions/605445/how-to-stream-my-gnu-linux-audio-output-to-android-devices-over-wi-fi)
- windows 到 linux：[Streaming audio from Windows to Linux using PulseAudio - Super User](https://superuser.com/questions/323329/streaming-audio-from-windows-to-linux-using-pulseaudio)
  - windows 上安装音频驱动，linux 上安装 scream receiver：[duncanthrax/scream: Virtual network sound card for Microsoft Windows (github.com)](https://github.com/duncanthrax/scream)
- windows 到 android

- 手机到 laptop, 通过 pulseaudio：[How to stream audio from your phone to your laptop with PulseAudio | Hacker News (ycombinator.com)](https://news.ycombinator.com/item?id=24441112)

#### pulseaudio

[Network Setup – PulseAudio (www.freedesktop.org)](https://www.freedesktop.org/wiki/Software/PulseAudio/Documentation/User/Network/#index2h3)

##### direct 模式

最简单的方式

- 在需要实际播放声音的设备上（server 端），开启`module-native-protocol-tcp`允许网络连接。
- 然后在客户端上，设置 PULSE_SERVER。这样客户端的声音就会交给服务端输出
  - 可以通过环境变量`PULSE_SERVER`
  - Alternatively you can modify `~/.pulse/client.conf` or `/etc/pulse/client.conf` and set `default-server`.

  ```
  export PULSE_SERVER=tcp:<server_ip>:4713
  ```

android 上有 pulse server 软件：[XServer XSDL - Google Play 上的应用](https://play.google.com/store/apps/details?id=x.org.server)

- 延迟挺低的

##### tunnel 模式

通过 tunnel，可以创建一个新的 sink，将所有音频通过网络发送到另一个 server 上（source 也一样）。好处是可以无缝切换使用本地还是远程设备。

[Modules – PulseAudio (www.freedesktop.org)](https://www.freedesktop.org/wiki/Software/PulseAudio/Documentation/User/Modules/#module-tunnel-sinksource)

假设 A，B 两个机器，A 有麦克风，B 有扬声器。可以通过以下配置，让 A 获得 B 的扬声器，B 获得 A 的麦克风。

```
# A
load-module module-native-protocol-tcp auth-anonymous=1
load-module module-tunnel-sink server=192.168.36.215

# B
load-module module-native-protocol-tcp auth-anonymous=1
load-module module-tunnel-source server=192.168.36.230
```

##### RTP

> RTP is the *Realtime Transfer Protocol*. It is a well-known protocol for transferring audio and video data over IP. Two related protocols are SDP and SAP. SDP is the *Session Description Protocol* and can be used to describe RTP sessions. SAP is the *Session Announcement Protocol* and can be used to announce RTP sessions that are described with SDP. (Modern SIP based VoIP phones use RTP/SDP for their sessions, too) All three protocols are defined in IETF RFCs (RFC3550, RFC3551, RFC2327, RFC2327). They can be used in both multicast and unicast fashions. PulseAudio exclusively uses multicast RTP/SDP/SAP containing audio data.

- 可以用于 1 对多，多对多等场景。
- RTP 基于 IP 层的协议延迟可能更低？

- pulseaudio 目前只支持 LAN 内。没法在跨 LAN 的两台设备中实现。

> **The current implementation is designed to be used exclusively in local area networks,** though Internet use is theoretically supported. Only uncompressed audio is supported, hence you won't be able to transmit more than a few streams at the same time over a standard LAN.

##### Rygel

> Your best bet is probably to setup a proper media server (like Rygel, which works well with Pulseaudio) to transcode the raw audio to something like MP3 and stream that instead.

##### 其它 module

module-simple-protocol-tcp

An implementation of a simple protocol which allows playback by using simple tools like netcat. Just connect to the listening socket of this module and write the audio data to it, or read it from it for playback, resp. recording.

#### vlc 进行 http 串流

- 优点：客户端不用安装软件，只需要打开浏览器
- 缺点：延迟有 3-4s，不适用于播放视频场景

*关键点：source 中默认有一个 monitor 的源，该源就可以获得输出到扬声器的声音*

```
cvlc -vvv pulse://XXXX --sout '#transcode{acodec=mp3,ab=128,channels=2}:standard{access=http,dst=0.0.0.0:8888/pc.mp3}'
```

设备上

```
http://your.local.ip.address:8888/pc.mp3
```

#### 各种串流

##### windows to linux

##### linux to anything

![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/picgo/20230322144833.png)

## 视频

### v4l2

列出所有设备

```
root@tianyi ➜  ~ v4l2-ctl --list-devices
USB2 Video: USB2 Video (usb-0000:00:14.0-4):
        /dev/video2
        /dev/video3
        /dev/media1

EasyCamera: EasyCamera (usb-0000:00:14.0-5):
        /dev/video0
        /dev/video1
        /dev/media0
```

笔记本自带摄像头

```
root@tianyi ➜  ~ v4l2-ctl -d /dev/video0 --all
Driver Info:
        Driver name      : uvcvideo
        Card type        : EasyCamera: EasyCamera
        Bus info         : usb-0000:00:14.0-5
        Driver version   : 6.2.16
        Capabilities     : 0x84a00001
                Video Capture
                Metadata Capture
                Streaming
                Extended Pix Format
                Device Capabilities
        Device Caps      : 0x04200001
                Video Capture
                Streaming
                Extended Pix Format

Priority: 2
Video input : 0 (Input 1: ok)
Format Video Capture:
        Width/Height      : 640/480
        Pixel Format      : 'YUYV' (YUYV 4:2:2)
        Field             : None
        Bytes per Line    : 1280
        Size Image        : 614400
        Colorspace        : sRGB
        Transfer Function : Rec. 709
        YCbCr/HSV Encoding: ITU-R 601
        Quantization      : Default (maps to Limited Range)
        Flags             :
Crop Capability Video Capture:
        Bounds      : Left 0, Top 0, Width 640, Height 480
        Default     : Left 0, Top 0, Width 640, Height 480
        Pixel Aspect: 1/1
Selection Video Capture: crop_default, Left 0, Top 0, Width 640, Height 480, Flags:
Selection Video Capture: crop_bounds, Left 0, Top 0, Width 640, Height 480, Flags:
Streaming Parameters Video Capture:
        Capabilities     : timeperframe
        Frames per second: 30.000 (30/1)
        Read buffers     : 0

```

采集卡

```
root@tianyi ➜  ~ v4l2-ctl -d /dev/video2 --all
Driver Info:
        Driver name      : uvcvideo
        Card type        : USB2 Video: USB2 Video
        Bus info         : usb-0000:00:14.0-4
        Driver version   : 6.2.16
        Capabilities     : 0x84a00001
                Video Capture
                Metadata Capture
                Streaming
                Extended Pix Format
                Device Capabilities
        Device Caps      : 0x04200001
                Video Capture
                Streaming
                Extended Pix Format
Priority: 2
Video input : 0 (Input 1: ok)
Format Video Capture:
        Width/Height      : 2560/1600
        Pixel Format      : 'MJPG' (Motion-JPEG)
        Field             : None
        Bytes per Line    : 0
        Size Image        : 8192000
        Colorspace        : sRGB
        Transfer Function : Rec. 709
        YCbCr/HSV Encoding: ITU-R 601
        Quantization      : Default (maps to Full Range)
        Flags             :
Crop Capability Video Capture:
        Bounds      : Left 0, Top 0, Width 2560, Height 1600
        Default     : Left 0, Top 0, Width 2560, Height 1600
        Pixel Aspect: 1/1
Selection Video Capture: crop_default, Left 0, Top 0, Width 2560, Height 1600, Flags:
Selection Video Capture: crop_bounds, Left 0, Top 0, Width 2560, Height 1600, Flags:
Streaming Parameters Video Capture:
        Capabilities     : timeperframe
        Frames per second: 30.000 (30/1)
        Read buffers     : 0
```
