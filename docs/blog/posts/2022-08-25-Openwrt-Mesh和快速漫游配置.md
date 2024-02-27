---
title: Openwrt Mesh和快速漫游配置
date: 2022-08-25 22:17:13
tags:
- openwrt
- mesh
categories:
- 折腾
---

## 背景

家里原本有两个路由器，一个负责楼上，一个负责楼下。但是仍然有许多覆盖不到的地方，比如厨房。并且更影响体验的是楼上楼下的WIFI使用不同的SSID，手机无法很好地自动切换。经常是楼上连接到楼下的网络导致信号很差。因此决定对家里的网络改造一番。

以前听过mesh这个技术，可以将很多台路由器通过无线连接起来，共同提供一个网络。于是去搜索了openwrt是否支持mesh，发现是可以的。并且经过进一步的了解，纠正了自己之前对无线网络的一些错误认知。
- 首先，mesh解决的并不是如何让设备自动切换网络，而是如何进行**无线组网**，可以避免布线的困难。mesh节点通过同一个信道的的无线相互连接，而通过另一个无线提供WIFI。
- **快速漫游**(fast roaming)协议，准确来说叫做802.11r协议，可以减少设备切换无线网络的耗时。

硬件设备上，我选择使用小米路由3G来搭建，主要是因为硬件配置上在wifi5的路由器中算是很不错的了，且某鱼上一个只需要50元。于是又买了两个，加上原本的，现在有4台openwrt路由器，一个红米AC2100作为主路由，3个R3G作为AP节点。

为了方便配置还实现了一个自动配置脚本放在github：[TheRainstorm/my-openwrt-config (github.com)](https://github.com/TheRainstorm/my-openwrt-config)

<!-- more -->
### 名词

- Wireless Access Point
  无线接入点，通常简称为AP。AP其实隐含dumb的含义。路由器设置里一般会有：路由器模式、AP模式等选项。AP模式下，路由器不提供路由、DHCP、DNS等功能，而是通过主路由来提供。
  - AP通常的作用是为现有的网络提供额外的无线覆盖，比如主路由器在二楼，通过AP将网络覆盖到一楼。
  - 实现上，AP将无线接口和LAN接口桥接在一起，可以理解为一个**二级交换机**。
- SSID、BSSID
  SSID是无线网络的名称，不同的AP可以提供相同的SSID。BSSID是无线网络的MAC地址，是唯一的。


802.11k:无线局域网频谱资源测量协议，由AP扫描周围邻居AP信息，配合终端扫描潜在漫游目标信息，解决何时漫游问题。  
802.11v:无线网络管理协议，终端请求漫游目标（非必要），AP建议终端漫游目标，解决漫游到何处问题。  
802.11r:快速BSS转换协议，消除无线重关联过程中的握手开销，极大减少漫游时间，解决如何关重关联问题。

一、要有自动切换Wi-Fi 信号的效果，只需要支持80.11k和802.11v，然后改相同的Wi-Fi 名称和密码即可，只要终端也支持k和v主会主切换，而802.11r不是必需的。  
  
二、MESH组网与自动切换是两回事，没有直接关系。MESH是一种组网方式，而绝大多数MESH组网后就会支持k和v，至少在当今的Wi-Fi 6时代是这样。
三、无缝漫游，是指自动切换的时间做到尽量的短，从而达到切换过程不会出现断线现象，怎么做到最短呢？这跟“漫游阀值”、“强信号重叠范围”有关，而绝大多数无线路由器一般没有漫游阀值可设置，那最简单可控的就是强信号重叠范围了，通过摆放位置或降低信号强度即可。如有弱信号剔除功能就更有可控性

### 无线漫游的过程

需要明白两件事
- 第一，设备倾向于赖在同一个网络上。当WIFI的信号强度弱于-70dB，且新WIFI的信号强度比原信号高8-12dB时才会选择切换网络。
- 第二，连接一个网络需要经过一些耗时过程。
  1. 需要进行密钥交换、协商加密算法
  2. 设备需要获得一个IP地址（通常通过DHCP协议）

第一个问题，理论上路由器可以给设备发送信号使其选择切换无线网络，不过不知道目前有没有这么做。
第二个问题
- 对于密钥交换和协商的过程很明显是可以避免的，802.11s协议应该就是节约了这部分的时间。只要配置成同一个域，那么在不同BSSID间切换就可以利用原有的连接。
- 而对于获得IP，只要路由器是AP模式，那么便可以直接使用原本的IP地址，因此也可以使用原本的IP地址。

### 802.11s是否需要硬件支持

理论上不需要，但是有些硬件的wifi驱动可能会有问题（开源驱动基本不会有问题）
可以通过iw查看驱动是否有mesh选项。
```
iw list | grep "Supported interface modes" -A 9
```

## 配置

可以详细参考这篇文章：[OpenWrt 802.11s mesh | My wiki (bmaupin.github.io)](https://bmaupin.github.io/wiki/other/openwrt/openwrt-80211s.html)
自己写了一个自动配置脚本：[TheRainstorm/my-openwrt-config (github.com)](https://github.com/TheRainstorm/my-openwrt-config)

主路由只需要设置802.11r快速漫游即可，而AP则需要设置mesh(802.11s)，并在提供wifi的网络上设置802.11r

#### 安装wpad

openwrt wifi功能由wpad包提供。openwrt提供了多种wpad包，针对不同功能进行了剪裁，大小不同。不同包会冲突，只能使用一个。使用wpad-mesh-openssl即可。
- wpad：最完整
- wpad-openssl
- **wpad-mesh-openssl**
- wpad-basic-openssl：精简
> Install either `wpad-mesh-openssl` (for devices with a lot of storage/memory) or `wpad-mesh-wolfssl` (for devices with low storage/memory)

#### dummy AP配置

官方文档：[[OpenWrt Wiki\] Wireless Access Point / Dumb Access Point](https://openwrt.org/docs/guide-user/network/wifi/dumbap)

##### 关闭DHCP服务器

ipv4勾选ignore interface即可

![image-20220825185126933](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/picgo/image-20220825185126933.png)

ipv6需要将ra, dhcpv6, ndp均设置为disabled

![image-20220825185217075](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/picgo/image-20220825185217075.png)

##### LAN接口ip地址

LAN接口需要设置ip地址，有两种方式（推荐第二种方法）
- 设置静态地址，需要同时设置网关、DNS为主路由

  ![image-20220825185519836](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/picgo/image-20220825185519836.png)

  ![image-20220825185451076](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/picgo/image-20220825185451076.png)

- 更简单的方式为将LAN设置为dhcp客户端。这样好处是不用配置，重启后路由器加入mesh后便可以成功上网。在之后可以在主路由DHCP设置中分配静态地址，这样路由器下次重启便会获得指定ip地址了。

  ![image-20220825185619578](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/picgo/image-20220825185619578.png)

##### 关闭防火墙, dns等服务

system->starup中关闭一些不必要的服务，如firewall, dnsmasq, odhcpd

![image-20220825185835670](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/picgo/image-20220825185835670.png)

主要部分已经配置完成。接下来是一些可选操作

- 删除掉WAN, WAN6等其余接口
- 删除掉所有防火墙zone

#### mesh配置(802.11s)

mesh需要占掉一个无线频段，这里我选择使用2.4GHz。因为家里的宽带是100MHz，因此2.4GHz的144Mbps带宽足够，然后就是2.4GHz的穿墙性能要好得多。
- 选择一个radio新建一个网络，比如2.4GHz radio

  ![image-20220825200934634](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/picgo/image-20220825200934634.png)

- 设置WIFI信道，所有mesh节点需要使用相同信道

  ![image-20220825221157178](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/picgo/image-20220825221157178.png)

- 然后然后选择mesh point模式。mesh id为一个字符串，保证mesh节点一致即可。加密必须选择wpa3-SAE加密。

  ![image-20220825200917273](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/picgo/image-20220825200917273.png)

#### 无线802.11r配置

另一个radio用于提供上网，可以新建一个接口选择AP模式（默认已经存在）

![image-20220825220833532](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/picgo/image-20220825220833532.png)

为了实现快速漫游需要设置802.11r，主要需要设置Mobility Domain，保证所有节点相同

![image-20220825220609260](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/picgo/image-20220825220609260.png)

FT协议的区别，个人感觉不太明显。

## 效果

二楼是一台RM2100作为主路由，提供2.4GHz和5GHz WIFI。5GHz使用52信道。

一楼有3台R3G，通过mesh无线相互连接。其中一台通过网线连接到二楼RM2100。3台R3G启用5GHz WIFI名字相同，分别占用36信道，52信道，100信道。不同信道间刚好相差80MHz等于WIFI5的频宽，因此可以相互不干扰。

下图分别是二楼主路由和一楼一台路由的信道分析图

![image-20220825190223518](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/picgo/image-20220825190223518.png)

![image-20220825214252429](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/picgo/image-20220825214252429.png)

#### 结果

在主路由上开启iperf3服务，手机上安装iperf3客户端测速，并在一楼和二楼走动。经验证确实可以自动实现网络漫游，走到某些位置时网速在降速后马上可以恢复。


## 例子

rm2100: 
- 2.4G mesh + 2.4 Wifi (disabled)
- 5G wifi
r3g x 3
- 2.4G mesh
- 5G wifi
### 参考

- 设置AP和快速漫游：[CHEAP WI-FI MESH ALTERNATIVE with fast roaming OpenWrt Wi-Fi Access points - YouTube](https://www.youtube.com/watch?v=kMgs2XFClaM)
- batman，更复杂也功能更多的mesh协议: [DIY MESH WiFi with batman-adv and OpenWrt - YouTube](https://www.youtube.com/watch?v=t4A0kfg2olo)
- 802.11k, v, r的介绍：[Fast Roaming with 802.11k, 802.11v, and 802.11r - Windows drivers | Microsoft Docs](https://docs.microsoft.com/en-us/windows-hardware/drivers/network/fast-roaming-with-802-11k--802-11v--and-802-11r)
- FT over DS还是FT over Air[When does 802.11r "FT over DS" make sense to use? - Installing and Using OpenWrt / Network and Wireless Configuration - OpenWrt Forum](https://forum.openwrt.org/t/when-does-802-11r-ft-over-ds-make-sense-to-use/88893/2)
  - [802.11r Fast Roaming configuration (channels and FT) - Installing and Using OpenWrt - OpenWrt Forum](https://forum.openwrt.org/t/802-11r-fast-roaming-configuration-channels-and-ft/118917/8)
    - Over-the-Air—The client communicates directly with the target AP using IEEE 802.11 authentication with the FT authentication algorithm. 
    - Over-the-DS—The client communicates with the target AP through the current AP.

```
daemon.debug hostapd: wlan0: STA e0:...:30 WPA: FT authentication already completed - do not start 4-way handshake
```

## 遇到问题

### mesh 设备未激活
rm2100开启mesh，radio0设备显示设备未激活
```
Sat Feb  3 21:55:53 2024 daemon.notice hostapd: phy0-ap0: AP-DISABLED
Sat Feb  3 21:55:53 2024 daemon.err hostapd: hostapd_free_hapd_data: Interface phy0-ap0 wasn't started
Sat Feb  3 21:55:53 2024 daemon.notice hostapd: nl80211: deinit ifname=phy0-ap0 disabled_11b_rates=0
Sat Feb  3 21:55:53 2024 kern.info kernel: [  970.826050] device phy0-ap0 left promiscuous mode
Sat Feb  3 21:55:53 2024 kern.info kernel: [  970.831019] br-lan: port 5(phy0-ap0) entered disabled state
Sat Feb  3 21:55:54 2024 daemon.notice hostapd: phy0-ap0: interface state ACS->DISABLED
Sat Feb  3 21:55:54 2024 daemon.notice netifd: lan (2365): udhcpc: sending renew to server 192.168.33.1
Sat Feb  3 21:55:54 2024 daemon.notice netifd: lan (2365): udhcpc: lease of 192.168.33.212 obtained from 192.168.33.1, lease time 43200
Sat Feb  3 21:55:55 2024 daemon.notice wpa_supplicant[1248]: phy0-mesh0: interface state UNINITIALIZED->ENABLED
Sat Feb  3 21:55:55 2024 daemon.notice wpa_supplicant[1248]: phy0-mesh0: AP-ENABLED
Sat Feb  3 21:55:55 2024 daemon.notice wpa_supplicant[1248]: phy0-mesh0: joining mesh my_mesh
Sat Feb  3 21:55:55 2024 daemon.err wpa_supplicant[1248]: phy0-mesh0: mesh join error=-1
```

手动设置使用channel 1, 设置40MHz频宽后突然可以了
```
Sat Feb  3 22:05:21 2024 daemon.notice wpa_supplicant[1248]: Set new config for phy phy0
Sat Feb  3 22:05:21 2024 daemon.notice hostapd: Set new config for phy phy0: /var/run/hostapd-phy0.conf
Sat Feb  3 22:05:21 2024 daemon.notice hostapd: Restart interface for phy phy0
Sat Feb  3 22:05:21 2024 daemon.notice hostapd: Remove interface 'phy0'
Sat Feb  3 22:05:21 2024 daemon.notice hostapd: phy0-ap0: interface state DISABLED->DISABLED
Sat Feb  3 22:05:21 2024 daemon.notice hostapd: phy0-ap0: AP-DISABLED
Sat Feb  3 22:05:21 2024 daemon.notice hostapd: phy0-ap0: CTRL-EVENT-TERMINATING
Sat Feb  3 22:05:21 2024 daemon.err hostapd: rmdir[ctrl_interface=/var/run/hostapd]: Permission denied
Sat Feb  3 22:05:21 2024 daemon.err hostapd: hostapd_free_hapd_data: Interface phy0-ap0 wasn't started
Sat Feb  3 22:05:21 2024 daemon.notice hostapd: nl80211: deinit ifname=phy0-ap0 disabled_11b_rates=0
Sat Feb  3 22:05:21 2024 kern.info kernel: [ 1538.873046] device phy0-ap0 left promiscuous mode
Sat Feb  3 22:05:21 2024 kern.info kernel: [ 1538.878005] br-lan: port 4(phy0-ap0) entered disabled state
Sat Feb  3 22:05:22 2024 daemon.notice netifd: Network device 'phy0-ap0' link is down
Sat Feb  3 22:05:22 2024 daemon.notice netifd: lan (2365): udhcpc: sending renew to server 192.168.33.1
Sat Feb  3 22:05:22 2024 daemon.notice netifd: lan (2365): udhcpc: lease of 192.168.33.212 obtained from 192.168.33.1, lease time 43200
Sat Feb  3 22:05:22 2024 daemon.notice hostapd: Configuration file: data: driver=nl80211 logger_syslog=127 logger_syslog_level=2 logger_stdout=127 logger_stdout_level=2 country_code=CN ieee80211d=1 hw_mode=g supported_rates=60 90 120 180 240 360 480 540 basic_rates=60 120 240 beacon_int=100 chanlist=1 #num_global_macaddr=1 ieee80211n=1 ht_coex=0 ht_capab=[HT40+][SHORT-GI-20][SHORT-GI-40][TX-STBC][RX-STBC1] channel=1  interface=phy0-ap0 bssid=9c:9d:7e:c6:de:32 ctrl_interface=/var/run/hostapd ap_isolate=1 bss_load_update_period=60 chan_util_avg_period=600 disassoc_low_ack=1 skip_inactivity_poll=0 preamble=1 wmm_enabled=1 ignore_broadcast_ssid=0 uapsd_advertisement_enabled=1 utf8_ssid=1 multi_ap=0 wpa_passphrase=15797678348 wpa_psk_file=/var/run/hostapd-phy0-ap0.psk auth_algs=1 wpa=2 wpa_pairwise=CCMP ssid=爱琴 bridge=br-lan wds_bridge= snoop_iface=br-lan ft_iface=br-lan mobility_domain=123d ft_psk_generate_local=1 ft_over_ds=0 reassociation_deadline=1000 wpa_disable_eapol_key_retries=0 wpa_key_mgmt=WPA-PSK FT-PSK okc=0 disable
Sat Feb  3 22:05:22 2024 kern.info kernel: [ 1539.839661] br-lan: port 4(phy0-ap0) entered blocking state
Sat Feb  3 22:05:22 2024 kern.info kernel: [ 1539.845252] br-lan: port 4(phy0-ap0) entered disabled state
Sat Feb  3 22:05:22 2024 kern.info kernel: [ 1539.851406] device phy0-ap0 entered promiscuous mode
Sat Feb  3 22:05:22 2024 kern.info kernel: [ 1539.856659] br-lan: port 4(phy0-ap0) entered blocking state
Sat Feb  3 22:05:22 2024 kern.info kernel: [ 1539.862310] br-lan: port 4(phy0-ap0) entered forwarding state
Sat Feb  3 22:05:22 2024 daemon.notice hostapd: phy0-ap0: interface state UNINITIALIZED->COUNTRY_UPDATE
Sat Feb  3 22:05:22 2024 daemon.notice hostapd: phy0-ap0: interface state COUNTRY_UPDATE->HT_SCAN
Sat Feb  3 22:05:22 2024 kern.info kernel: [ 1539.873538] device phy0-ap0 left promiscuous mode
Sat Feb  3 22:05:22 2024 kern.info kernel: [ 1539.878707] br-lan: port 4(phy0-ap0) entered disabled state
Sat Feb  3 22:05:23 2024 kern.info kernel: [ 1539.980798] br-lan: port 4(phy0-ap0) entered blocking state
Sat Feb  3 22:05:23 2024 kern.info kernel: [ 1539.986408] br-lan: port 4(phy0-ap0) entered disabled state
Sat Feb  3 22:05:23 2024 kern.info kernel: [ 1539.992532] device phy0-ap0 entered promiscuous mode
Sat Feb  3 22:05:23 2024 kern.info kernel: [ 1539.997983] br-lan: port 4(phy0-ap0) entered blocking state
Sat Feb  3 22:05:23 2024 kern.info kernel: [ 1540.003617] br-lan: port 4(phy0-ap0) entered forwarding state
Sat Feb  3 22:05:23 2024 kern.info kernel: [ 1540.010314] br-lan: port 4(phy0-ap0) entered disabled state
Sat Feb  3 22:05:23 2024 daemon.notice netifd: lan (2365): udhcpc: sending renew to server 192.168.33.1
Sat Feb  3 22:05:23 2024 daemon.notice netifd: lan (2365): udhcpc: lease of 192.168.33.212 obtained from 192.168.33.1, lease time 43200
Sat Feb  3 22:05:23 2024 daemon.notice netifd: Wireless device 'radio0' is now up
Sat Feb  3 22:05:23 2024 daemon.notice netifd: lan (2365): udhcpc: sending renew to server 192.168.33.1
Sat Feb  3 22:05:23 2024 daemon.notice netifd: lan (2365): udhcpc: lease of 192.168.33.212 obtained from 192.168.33.1, lease time 43200
Sat Feb  3 22:05:26 2024 daemon.notice hostapd: 20/40 MHz operation not permitted on channel pri=1 sec=5 based on overlapping BSSes
Sat Feb  3 22:05:26 2024 daemon.notice hostapd: Fallback to 20 MHz
Sat Feb  3 22:05:27 2024 kern.info kernel: [ 1544.109128] IPv6: ADDRCONF(NETDEV_CHANGE): phy0-ap0: link becomes ready
Sat Feb  3 22:05:27 2024 kern.info kernel: [ 1544.116051] br-lan: port 4(phy0-ap0) entered blocking state
Sat Feb  3 22:05:27 2024 kern.info kernel: [ 1544.121714] br-lan: port 4(phy0-ap0) entered forwarding state
Sat Feb  3 22:05:27 2024 daemon.notice netifd: Network device 'phy0-ap0' link is up
Sat Feb  3 22:05:27 2024 daemon.notice hostapd: phy0-ap0: interface state HT_SCAN->ENABLED
Sat Feb  3 22:05:27 2024 daemon.notice hostapd: phy0-ap0: AP-ENABLED
Sat Feb  3 22:05:31 2024 kern.info kernel: [ 1548.239427] device phy0-ap0 left promiscuous mode
Sat Feb  3 22:05:31 2024 kern.info kernel: [ 1548.244375] br-lan: port 4(phy0-ap0) entered disabled state
Sat Feb  3 22:05:31 2024 daemon.notice netifd: lan (2365): udhcpc: sending renew to server 192.168.33.1
Sat Feb  3 22:05:31 2024 daemon.notice netifd: lan (2365): udhcpc: lease of 192.168.33.212 obtained from 192.168.33.1, lease time 43200
Sat Feb  3 22:05:32 2024 daemon.notice wpa_supplicant[1248]: Set new config for phy phy0
Sat Feb  3 22:05:32 2024 daemon.notice hostapd: Set new config for phy phy0: /var/run/hostapd-phy0.conf
Sat Feb  3 22:05:32 2024 daemon.notice hostapd: Restart interface for phy phy0
Sat Feb  3 22:05:32 2024 daemon.notice hostapd: Remove interface 'phy0'
Sat Feb  3 22:05:32 2024 daemon.notice hostapd: phy0-ap0: interface state ENABLED->DISABLED
Sat Feb  3 22:05:32 2024 daemon.notice hostapd: phy0-ap0: AP-DISABLED
Sat Feb  3 22:05:32 2024 daemon.notice hostapd: phy0-ap0: CTRL-EVENT-TERMINATING
Sat Feb  3 22:05:32 2024 daemon.err hostapd: rmdir[ctrl_interface=/var/run/hostapd]: Permission denied
Sat Feb  3 22:05:32 2024 daemon.notice hostapd: nl80211: deinit ifname=phy0-ap0 disabled_11b_rates=0
Sat Feb  3 22:05:32 2024 daemon.notice hostapd: nl80211: Failed to remove interface phy0-ap0 from bridge br-lan: Invalid argument
Sat Feb  3 22:05:33 2024 daemon.notice hostapd: Configuration file: data: driver=nl80211 logger_syslog=127 logger_syslog_level=2 logger_stdout=127 logger_stdout_level=2 country_code=CN ieee80211d=1 hw_mode=g supported_rates=60 90 120 180 240 360 480 540 basic_rates=60 120 240 beacon_int=100 chanlist=1 noscan=1 #num_global_macaddr=1 ieee80211n=1 ht_coex=0 ht_capab=[HT40+][SHORT-GI-20][SHORT-GI-40][TX-STBC][RX-STBC1] channel=1  interface=phy0-ap0 bssid=9c:9d:7e:c6:de:32 ctrl_interface=/var/run/hostapd ap_isolate=1 bss_load_update_period=60 chan_util_avg_period=600 disassoc_low_ack=1 skip_inactivity_poll=0 preamble=1 wmm_enabled=1 ignore_broadcast_ssid=0 uapsd_advertisement_enabled=1 utf8_ssid=1 multi_ap=0 wpa_passphrase=15797678348 wpa_psk_file=/var/run/hostapd-phy0-ap0.psk auth_algs=1 wpa=2 wpa_pairwise=CCMP ssid=爱琴 bridge=br-lan wds_bridge= snoop_iface=br-lan ft_iface=br-lan mobility_domain=123d ft_psk_generate_local=1 ft_over_ds=0 reassociation_deadline=1000 wpa_disable_eapol_key_retries=0 wpa_key_mgmt=WPA-PSK FT-PSK okc=
Sat Feb  3 22:05:33 2024 kern.info kernel: [ 1550.139564] br-lan: port 4(phy0-ap0) entered blocking state
Sat Feb  3 22:05:33 2024 kern.info kernel: [ 1550.145154] br-lan: port 4(phy0-ap0) entered disabled state
Sat Feb  3 22:05:33 2024 kern.info kernel: [ 1550.151284] device phy0-ap0 entered promiscuous mode
Sat Feb  3 22:05:33 2024 kern.info kernel: [ 1550.156508] br-lan: port 4(phy0-ap0) entered blocking state
Sat Feb  3 22:05:33 2024 kern.info kernel: [ 1550.162130] br-lan: port 4(phy0-ap0) entered forwarding state
Sat Feb  3 22:05:33 2024 daemon.notice hostapd: phy0-ap0: interface state UNINITIALIZED->COUNTRY_UPDATE
Sat Feb  3 22:05:33 2024 kern.info kernel: [ 1550.172408] device phy0-ap0 left promiscuous mode
Sat Feb  3 22:05:33 2024 kern.info kernel: [ 1550.177434] br-lan: port 4(phy0-ap0) entered disabled state
Sat Feb  3 22:05:33 2024 kern.info kernel: [ 1550.240954] br-lan: port 4(phy0-ap0) entered blocking state
Sat Feb  3 22:05:33 2024 kern.info kernel: [ 1550.246577] br-lan: port 4(phy0-ap0) entered disabled state
Sat Feb  3 22:05:33 2024 kern.info kernel: [ 1550.252919] device phy0-ap0 entered promiscuous mode
Sat Feb  3 22:05:33 2024 kern.info kernel: [ 1550.258413] br-lan: port 4(phy0-ap0) entered blocking state
Sat Feb  3 22:05:33 2024 kern.info kernel: [ 1550.264021] br-lan: port 4(phy0-ap0) entered forwarding state
Sat Feb  3 22:05:33 2024 daemon.notice netifd: lan (2365): udhcpc: sending renew to server 192.168.33.1
Sat Feb  3 22:05:33 2024 daemon.notice netifd: lan (2365): udhcpc: lease of 192.168.33.212 obtained from 192.168.33.1, lease time 43200
Sat Feb  3 22:05:33 2024 daemon.notice netifd: lan (2365): udhcpc: sending renew to server 192.168.33.1
Sat Feb  3 22:05:33 2024 daemon.notice netifd: lan (2365): udhcpc: lease of 192.168.33.212 obtained from 192.168.33.1, lease time 43200
Sat Feb  3 22:05:33 2024 daemon.notice netifd: Network device 'phy0-ap0' link is up
Sat Feb  3 22:05:33 2024 kern.info kernel: [ 1550.479613] IPv6: ADDRCONF(NETDEV_CHANGE): phy0-ap0: link becomes ready
Sat Feb  3 22:05:33 2024 daemon.notice hostapd: phy0-ap0: interface state COUNTRY_UPDATE->ENABLED
Sat Feb  3 22:05:33 2024 daemon.notice hostapd: phy0-ap0: AP-ENABLED
Sat Feb  3 22:05:33 2024 kern.info kernel: [ 1550.608140] br-lan: port 6(phy0-mesh0) entered blocking state
Sat Feb  3 22:05:33 2024 kern.info kernel: [ 1550.613930] br-lan: port 6(phy0-mesh0) entered disabled state
Sat Feb  3 22:05:33 2024 kern.info kernel: [ 1550.620473] device phy0-mesh0 entered promiscuous mode
Sat Feb  3 22:05:33 2024 daemon.notice netifd: lan (2365): udhcpc: sending renew to server 192.168.33.1
Sat Feb  3 22:05:33 2024 daemon.notice netifd: lan (2365): udhcpc: lease of 192.168.33.212 obtained from 192.168.33.1, lease time 43200
Sat Feb  3 22:05:33 2024 daemon.notice wpa_supplicant[1248]: Set new config for phy phy0
Sat Feb  3 22:05:33 2024 daemon.notice netifd: Wireless device 'radio0' is now up
Sat Feb  3 22:05:35 2024 daemon.notice netifd: Network device 'phy0-ap0' link is down
Sat Feb  3 22:05:35 2024 kern.info kernel: [ 1552.740076] br-lan: port 4(phy0-ap0) entered disabled state
```

### AP模式无法联网

AP模式通常只保留了一个lan interface，如果设置为静态ip，那么要保证以下设置才能正常上网
- 设置gateway
- 设置custom dns
- 禁用dnsmasq

检查
- ip ro查看是否有默认路由
- vim /etc/resolve.conf是否是自定义的dns

### 有线回程 + mesh导致延迟400ms

op3
- --- ax6s - - mesh
- --- r3g-mesh1 - - mesh -- r3g-mesh2

是不是造成循环了
- 开启mesh节点，连接的其它mesh节点不能连接有线？

ax6s
- 2.4G AP: 1, 40MHz, AU, 20(27) dbm
- 5G AP: 149, 80MHz, **AU, 27dbm**
rm2100
- 2.4G AP: disabled
- 5G AP: 36, 80MHz, AU, 23dbm

r3g-mesh1
- 2.4G mesh + AP: 1, 40MHz, AU, 26dbm
- 5G AP: 149, 80MHz, AU, 23dbm

r3g-mesh2
- 2.4G mesh + AP: 1, 40MHz, default, 20dbm
- 5G AP: 52, 80MHz, CN, 23dbm
## 理论

[CCIE Wireless: 802.11r (wirelessccie.blogspot.com)](http://wirelessccie.blogspot.com/2016/01/80211r.html?m=1)

- The **reassociation timeout** determines the duration for which the newly negotiated key is valid. By default, if the client does not make the jump within 20 seconds, the next AP cancels the PMK-R1, considering that the client went elsewhere.

无线抓包很难办到
- 需要专门的网卡和驱动
- [在Windows电脑上通过wireshark直接无线抓包的方式 - 知了社区 (h3c.com)](https://zhiliao.h3c.com/theme/details/183006)
## 测试

```

```

正常无线连接op3
```
Thu Aug 17 22:58:44 2023 daemon.debug hostapd: wlan1: STA 2a:85:8f:ff:be:e3 IEEE 802.11: authentication OK (open system)
Thu Aug 17 22:58:44 2023 daemon.debug hostapd: wlan1: STA 2a:85:8f:ff:be:e3 WPA: event 0 notification
Thu Aug 17 22:58:44 2023 daemon.debug hostapd: wlan1: STA 2a:85:8f:ff:be:e3 MLME: MLME-AUTHENTICATE.indication(2a:85:8f:ff:be:e3, OPEN_SYSTEM)
Thu Aug 17 22:58:44 2023 daemon.debug hostapd: wlan1: STA 2a:85:8f:ff:be:e3 MLME: MLME-DELETEKEYS.request(2a:85:8f:ff:be:e3)
Thu Aug 17 22:58:44 2023 daemon.info hostapd: wlan1: STA 2a:85:8f:ff:be:e3 IEEE 802.11: authenticated
Thu Aug 17 22:58:44 2023 daemon.debug hostapd: wlan1: STA 2a:85:8f:ff:be:e3 IEEE 802.11: association OK (aid 7)
Thu Aug 17 22:58:44 2023 daemon.info hostapd: wlan1: STA 2a:85:8f:ff:be:e3 IEEE 802.11: associated (aid 7)
Thu Aug 17 22:58:44 2023 daemon.debug hostapd: wlan1: STA 2a:85:8f:ff:be:e3 MLME: MLME-ASSOCIATE.indication(2a:85:8f:ff:be:e3)
Thu Aug 17 22:58:44 2023 daemon.debug hostapd: wlan1: STA 2a:85:8f:ff:be:e3 MLME: MLME-DELETEKEYS.request(2a:85:8f:ff:be:e3)
Thu Aug 17 22:58:44 2023 daemon.debug hostapd: wlan1: STA 2a:85:8f:ff:be:e3 IEEE 802.11: binding station to interface 'wlan1'
Thu Aug 17 22:58:44 2023 daemon.debug hostapd: wlan1: STA 2a:85:8f:ff:be:e3 WPA: event 1 notification
Thu Aug 17 22:58:44 2023 daemon.debug hostapd: wlan1: STA 2a:85:8f:ff:be:e3 WPA: start authentication
Thu Aug 17 22:58:44 2023 daemon.debug hostapd: wlan1: STA 2a:85:8f:ff:be:e3 IEEE 802.1X: unauthorizing port
Thu Aug 17 22:58:44 2023 daemon.debug hostapd: wlan1: STA 2a:85:8f:ff:be:e3 WPA: sending 1/4 msg of 4-Way Handshake
Thu Aug 17 22:58:45 2023 daemon.debug hostapd: wlan1: STA 2a:85:8f:ff:be:e3 WPA: EAPOL-Key timeout
Thu Aug 17 22:58:45 2023 daemon.debug hostapd: wlan1: STA 2a:85:8f:ff:be:e3 WPA: sending 1/4 msg of 4-Way Handshake
Thu Aug 17 22:58:45 2023 daemon.debug hostapd: wlan1: STA 2a:85:8f:ff:be:e3 WPA: received EAPOL-Key frame (2/4 Pairwise)
Thu Aug 17 22:58:45 2023 daemon.debug hostapd: wlan1: STA 2a:85:8f:ff:be:e3 WPA: sending 3/4 msg of 4-Way Handshake
Thu Aug 17 22:58:45 2023 daemon.debug hostapd: wlan1: STA 2a:85:8f:ff:be:e3 WPA: received EAPOL-Key frame (4/4 Pairwise)
Thu Aug 17 22:58:45 2023 daemon.notice hostapd: wlan1: AP-STA-CONNECTED 2a:85:8f:ff:be:e3
Thu Aug 17 22:58:45 2023 daemon.debug hostapd: wlan1: STA 2a:85:8f:ff:be:e3 IEEE 802.1X: authorizing port
Thu Aug 17 22:58:45 2023 daemon.info hostapd: wlan1: STA 2a:85:8f:ff:be:e3 WPA: pairwise key handshake completed (RSN)
Thu Aug 17 22:58:45 2023 daemon.notice hostapd: wlan1: EAPOL-4WAY-HS-COMPLETED 2a:85:8f:ff:be:e3
Thu Aug 17 22:58:45 2023 daemon.info dnsmasq-dhcp[1]: DHCPREQUEST(br-lan) 192.168.33.218 2a:85:8f:ff:be:e3
Thu Aug 17 22:58:45 2023 daemon.info dnsmasq-dhcp[1]: DHCPACK(br-lan) 192.168.33.218 2a:85:8f:ff:be:e3 Redmi-Note-11T-Pro
```

FT漫游到r3g
```
Thu Aug 17 23:01:41 2023 daemon.notice hostapd: wlan1: AP-STA-DISCONNECTED 2a:85:8f:ff:be:e3
Thu Aug 17 23:01:41 2023 daemon.err hostapd: nl80211: kernel reports: key addition failed
Thu Aug 17 23:01:41 2023 daemon.debug hostapd: wlan1: STA 2a:85:8f:ff:be:e3 IEEE 802.11: binding station to interface 'wlan1'
Thu Aug 17 23:01:41 2023 daemon.debug hostapd: wlan1: STA 2a:85:8f:ff:be:e3 IEEE 802.11: authentication OK (FT)
Thu Aug 17 23:01:41 2023 daemon.debug hostapd: wlan1: STA 2a:85:8f:ff:be:e3 MLME: MLME-AUTHENTICATE.indication(2a:85:8f:ff:be:e3, FT)
Thu Aug 17 23:01:41 2023 daemon.debug hostapd: wlan1: STA 2a:85:8f:ff:be:e3 IEEE 802.11: association OK (aid 1)
Thu Aug 17 23:01:41 2023 daemon.info hostapd: wlan1: STA 2a:85:8f:ff:be:e3 IEEE 802.11: associated (aid 1)
Thu Aug 17 23:01:41 2023 daemon.notice hostapd: wlan1: AP-STA-CONNECTED 2a:85:8f:ff:be:e3
Thu Aug 17 23:01:41 2023 daemon.debug hostapd: wlan1: STA 2a:85:8f:ff:be:e3 MLME: MLME-REASSOCIATE.indication(2a:85:8f:ff:be:e3)
Thu Aug 17 23:01:41 2023 daemon.debug hostapd: wlan1: STA 2a:85:8f:ff:be:e3 IEEE 802.11: binding station to interface 'wlan1'
Thu Aug 17 23:01:41 2023 daemon.debug hostapd: wlan1: STA 2a:85:8f:ff:be:e3 WPA: event 6 notification
Thu Aug 17 23:01:41 2023 daemon.debug hostapd: wlan1: STA 2a:85:8f:ff:be:e3 WPA: FT authentication already completed - do not start 4-way handshake
```

在op3上还能看到dhcp
```
Thu Aug 17 23:01:42 2023 daemon.info dnsmasq-dhcp[1]: DHCPDISCOVER(br-lan) 2a:85:8f:ff:be:e3
Thu Aug 17 23:01:42 2023 daemon.info dnsmasq-dhcp[1]: DHCPOFFER(br-lan) 192.168.33.218 2a:85:8f:ff:be:e3
Thu Aug 17 23:01:42 2023 daemon.info dnsmasq-dhcp[1]: DHCPREQUEST(br-lan) 192.168.33.218 2a:85:8f:ff:be:e3
Thu Aug 17 23:01:42 2023 daemon.info dnsmasq-dhcp[1]: DHCPACK(br-lan) 192.168.33.218 2a:85:8f:ff:be:e3 Redmi-Note-11T-Pro
```