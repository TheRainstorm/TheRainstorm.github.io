---
title: 体验纯 IPv6 网络
date: 2024-10-07 19:26:22
tags:
  - ipv6
categories:
  - 折腾记录
---

起因是给 wolf 的开发者提建议时，涉及到了通过 HE(Hurricane Electric) 提供的 6in4 服务接入 ipv6 网络 。既然给别人介绍了，感觉自己不能没有实操过，因此就尝试在自己的网络连入 HE。

```
I want to streaming over ipv6 network. However wolf only listen on ipv4 for now.

ABeltramo — 2024/10/06 23:42
Probably not, I don't have IPv6 in my LAN/WAN so not sure how to implement it.. Might be worth opening up an issue in Github!

TheRainstorm — 2024/10/06 23:49
Doesn't your ISP provide IPv6? Otherwise, enabling IPv6 should only require enabling it on the home router.

ABeltramo — 昨天00:59
Nope, no IPv6 over here..

TheRainstorm — 昨天14:56
If you want to try out IPv6, there's another way to get the full IPv6 experience, which is through a 6in4 tunnel. Some free services, like Hurricane Electric, allow you to connect to the IPv6 network. However, this requires you to have a public IPv4 address and a router that supports 6in4 functionality (if you're using open-source router firmware like OpenWRT, it is supported by default).

I can provide you with some useful links:
https://www.youtube.com/watch?v=LJPXz8eA3b8&t=64s
https://openwrt.org/docs/guide-user/network/ipv6/ipv6tunnel-luci

ABeltramo — 昨天15:02
Thanks, that's probably my best bet on trying IPv6. I have a WAN IPv4 IP and I use OPNSense in my custom router so it should be possible.
I'm working on a few other bits at the moment, not sure when I'll have the time to look properly into this
```

接着意识到到，既然我可以 6in4 到国外，岂不是可以直接访问国外 v6 网站？不过由于只有 v6 地址，因此只能访问纯 ipv6 网站。于是我就好奇，在 2024 年纯 ipv6 的体验是怎么样的，因此就有了这篇博客。

秀下最后大大的 **No IPv4 address detected**

![image.png](https://imagebed.yfycloud.site/2025/12/a41d966b21f47bca911ecf592dc98568.png)

并且 /48 的前缀，我可以划分 65536 个子网！

<!-- more -->

有用链接

- ipw.cn
- ipv6.test-ipv6.com

## 纯 IPv6 网站体验排行榜

这里是最后使用手机接入一个纯 ipv6 网络后的体验

### 国外

google 是真 nb，google 搜索，youtube 都支持 ipv6，并且体验还不错，搜索响应很快，能够提示推荐词，youtube 能观看 1080p 视频（跳转大概缓冲 4s）。

其中 youtube 刚开始图标显示有问题，后来就完全正常了。

![image.png](https://imagebed.yfycloud.site/2025/12/22d279dc0b3870bd5d02854fb51e1cad.png)

支持

- google 系（google 搜索，YouTube.com）
- telegram

不支持

- discord
- x.com
- reddit
- twitch
- instagram

### 国内

淘宝系也是真 nb，手机 app 流畅的一笔，基本用不出区别。并且软件甚至会检测你的 ip 让你切换到全球地区

![image.png](https://imagebed.yfycloud.site/2025/12/32cd01e4e4660fa652c569e9580f0fca.png)

视频网站

- youku.com：优酷牛逼，国内唯一一个能够使用的视频网站
- B 站不支持（网页手机 app 都不行），网上好像说 CDN 支持
- 爱奇艺、西瓜视频、抖音都不支持

聊天软件

- 微信，qq 都支持

购物

- 支付宝也支持
  - 淘票票小程序支持，但是有点卡
- 微信

资讯

- 支持
  - 知乎
  - 微博
- 不支持
  - 贴吧
  - 小红书
  - 豆瓣

## OpenWRT HE tunnel 配置

计划是通过 HE tunnel 获得一个 IPv6 的 PD 前缀（HE 默认给一个 64，可以申请一个 48），然后创建一个新的 LAN，作为 RA server 和 DHCPv6 server，为 lan 内所有设备分配 ipv6 地址。

![image.png](https://imagebed.yfycloud.site/2025/12/84915f035cb8029d7563321e30200678.png)

最后效果
![image.png](https://imagebed.yfycloud.site/2025/12/ef119dcf41154b2f1a48f89ad40cc0a8.png)

### 参考资料

<https://www.youtube.com/watch?v=LJPXz8eA3b8>
[[OpenWrt Wiki] IPv6 with Hurricane Electric using LuCI](https://openwrt.org/docs/guide-user/network/ipv6/ipv6tunnel-luci)

### 安装依赖

6in4 需要

```
opkg install 6in4
```

如果使用 PVE LXC 容器搭建的 openwrt，pve 中还需要另外 modprobe `sit, ip_tunnel` 模块

```
root@ryzen-pve ➜  ~ lsmod | grep -E 'ipv6|sit|ip_tunnel|nf_conntrack_ipv6'
sit                    36864  0
tunnel4                12288  1 sit
nf_reject_ipv6         24576  1 nft_reject_inet
nf_defrag_ipv6         24576  1 nf_conntrack
ip_tunnel              32768  2 ip_gre,sit
```

### 6in4 接口配置

![image.png](https://imagebed.yfycloud.site/2025/12/7cb3b1d9b7954c3a6b3bc5bab188cffd.png)

Advanced Setting 中不勾选使用默认路由，避免覆盖掉 WAN6 口的默认路由。

>Use default gateway: If unchecked, no default route is configured

### lan 接口设置

tunnel 起来后，需要创建一个 lan2 接口，作为 ra server 和 dhcpv6 server

协议选择静态地址，和正常 lan 不同的是，我们不需要指定 ipv4 地址，因为我们要打造一个存 ipv4 环境。因此 ipv4 server 啥的都不需要勾选。

分配 ipv6 prefix 长度选择 48（全部用掉），prefix filter 选择从 HE tunnel 接口获得
![image.png](https://imagebed.yfycloud.site/2025/12/4f7b3638b075c3a4f807f8de4a3d6638.png)

不要开启 ipv4 dhcp server，选择 ignore
![image.png](https://imagebed.yfycloud.site/2025/12/3030b516e0573fee41da85a042aa3493.png)

启用 ipv6 ra, dhcpv6 server
![image.png](https://imagebed.yfycloud.site/2025/12/401d6e07b7d552798886e4d42024b6e6.png)

### 路由问题

6in4 tunnel 本质还是一个三层隧道。**openwrt 对其配置也中少了一个叫做 source routing 的选项**（dhcpv6 和 pppoe 都有该选项），作用是会根据源地址匹配默认路由。这样在有多个上游 v6 地址时，可以根据包的源地址选择不同上游接口出去。
> IPv6 Sourcing routing: Automatically handle multiple uplink interfaces using source-based policy routing.

没有这个选项，加上我们关闭了默认路由，因此**此时没有 ipv6 包会从隧道路由出去**。

由于 HE tunnel 的 prefix 是不会变的，因此手动设置即可

```
root@op1 ➜  ~ ip6 ro
default from 2001:470:fab1::/48 dev 6in4-HE_tunnel metric 1024 pref medium
```

因为这个 v6 **前缀是可路由的**，因此我可以在我的 op2 移动家宽网络测试 op1 lan2 接口的 v6 是否能通。

果然是能通的，不过延迟来到了 569ms，感觉来回了两下美国。神奇的是 op2 lan 下设备延迟反而更低

op2 路由器上测试

```
root@op2 ➜  ping 2001:470:fab1:0:be24:11ff:fec1:6c9d
PING 2001:470:fab1:0:be24:11ff:fec1:6c9d (2001:470:fab1:0:be24:11ff:fec1:6c9d): 56 data bytes

--- 2001:470:fab1:0:be24:11ff:fec1:6c9d ping statistics ---
5 packets transmitted, 5 packets received, 0% packet loss
round-trip min/avg/max = 562.041/569.224/594.678 ms
```

op2 lan 下设备测试，延迟只有 338 ms

```
$ ping 2001:470:fab1:0:be24:11ff:fec1:6c9d -t
正在 Ping 2001:470:fab1:0:be24:11ff:fec1:6c9d 具有 32 字节的数据:
2001:470:fab1:0:be24:11ff:fec1:6c9d 的 Ping 统计信息:
    数据包: 已发送 = 15，已接收 = 15，丢失 = 0 (0% 丢失)，
往返行程的估计时间(以毫秒为单位):
    最短 = 334ms，最长 = 369ms，平均 = 338ms
```

抓包都是从 pppoe-wan 口出去的，感觉唯一区别就是 src ip 不同。暂不清楚为何延迟有区别。

```
root@op2 ➜  ~ tcpdump -ni any icmp6 and host 2001:470:fab1:0:be24:11ff:fec1:6c9d
18:19:59.885930 pppoe-wan In  IP6 2001:470:fab1:0:be24:11ff:fec1:6c9d > 2409:8a30:4ad:d140::10: ICMP6, echo reply, id 41070, seq 18, length 64
18:20:00.324036 pppoe-wan Out IP6 2409:8a30:4ad:d140::10 > 2001:470:fab1:0:be24:11ff:fec1:6c9d: ICMP6, echo request, id 41070, seq 19, length 64

18:20:06.662907 eth1  In  IP6 2409:8a30:4ad:d140:5dfe:907a:ae21:23e8 > 2001:470:fab1:0:be24:11ff:fec1:6c9d: ICMP6, echo request, id 1, seq 129, length 40
18:20:06.662958 pppoe-wan Out IP6 2409:8a30:4ad:d140:5dfe:907a:ae21:23e8 > 2001:470:fab1:0:be24:11ff:fec1:6c9d: ICMP6, echo request, id 1, seq 129, length 40
18:20:06.996932 pppoe-wan In  IP6 2001:470:fab1:0:be24:11ff:fec1:6c9d > 2409:8a30:4ad:d140:5dfe:907a:ae21:23e8: ICMP6, echo reply, id 1, seq 129, length 40
18:20:06.996975 eth1  Out IP6 2001:470:fab1:0:be24:11ff:fec1:6c9d > 2409:8a30:4ad:d140:5dfe:907a:ae21:23e8: ICMP6, echo reply, id 1, seq 129, length 40
```

### 防火墙问题：RS, RA 不通

刚开始给创建的 lan 分配的一个单独的防火墙 zone，结果发现 op1 **lan 下设备都无法获得 ipv6 地址**。但是 op1 上 lan 接口有 ipv6 地址（并且测试是能够通过 HE tunnel 访问网络的）

op1 上抓包是能看到 lan 下设备发送了 RS 请求的，但是路由器没有返回 RA。因此怀疑是防火墙问题。

发现我创建的防火墙 input 默认是 reject，这导致 lan 下设备无法访问路由器自身。可能这使得路由器接收不到来自设备的所有 icmp6 包，而 ipv6 大量依赖 icmp6 进行工作，因此这可能就是原因。

设置成 accept 后，果然 lan 下的设备就能获得获得 ipv6 地址了。

思考后，发现我这里创建的 lan2 和我 原本的 lan 的行为基本是一摸一样的。我对原本 lan 的控制也适用于 lan2，因此简单起见，**我将 HE_tunnel 划分为 WAN，lan2 划分为 LAN**。

### DNS 问题

现在 lan 下设备能获得 ipv6 地址，但是还是不能上网。原因有这些

- 默认 dns 为 op1 路由器 lan2 接口 ipv6 地址，使用该接口解析（国外域名）会得到 fake-ip
- 手动改用其它 dns，仍然会被劫持

#### dns 下发

openwrt 下发了本地接口作为 dns，我的本地 dns 使用了 fake ip 技术，没法直接使用

解决：openwrt lan 接口添加自定义的 dns

效果

```
无线局域网适配器 WLAN:

   连接特定的 DNS 后缀 . . . . . . . :
   描述. . . . . . . . . . . . . . . : Intel(R) Wi-Fi 6 AX201 160MHz
   物理地址. . . . . . . . . . . . . : 28-11-A8-27-40-3E
   DHCP 已启用 . . . . . . . . . . . : 是
   自动配置已启用. . . . . . . . . . : 是
   IPv6 地址 . . . . . . . . . . . . : 2001:470:fabxxxx:9b56(首选)
   临时 IPv6 地址. . . . . . . . . . : 2001:470:fabxxxx:f4ba(首选)
   本地链接 IPv6 地址. . . . . . . . : fe80::47f7:23bf:d0d9:506%3(首选)
   自动配置 IPv4 地址  . . . . . . . : 169.254.23.70(首选)
   子网掩码  . . . . . . . . . . . . : 255.255.0.0
   默认网关. . . . . . . . . . . . . : fe80::9cc5:xxxx:8c2c%3
   DHCPv6 IAID . . . . . . . . . . . : 69734824
   DHCPv6 客户端 DUID  . . . . . . . : 00-01-00-01-29-89-29-F7-28-11-A8-27-40-3E
   DNS 服务器  . . . . . . . . . . . : 2001:4860:4860::8888
   TCPIP 上的 NetBIOS  . . . . . . . : 已启用
```

#### dns 劫持

我的 openwrt 使用了透明代理，劫持了 udp 53 的 dns

解决：添加绕过 openclash 的 nft 规则

```
nft insert rule inet fw4 dstnat udp dport 53 ip daddr {223.5.5.5, 119.29.29.29, 8.8.8.8} return comment "Disable_OpenClash_DNS_Hijack"

nft insert rule inet fw4 dstnat udp dport 53 ip6 daddr {2001:4860:4860::8888} return comment "IPv6_Disable_OpenClash_DNS_Hijack"
```

#### DoT, DoH?

另一种避免 dns 污染的方式是不使用明文的 dns 请求。如 DoH，现代浏览器都支持设置。

但是设置了后发现还是不行，问题貌似在于解析 DoH 域名也需要 dns 请求。因此还是需要使用上面方法。

[DNS-over-TLS  |  Public DNS  |  Google for Developers](https://developers.google.com/speed/public-dns/docs/dns-over-tls)
[DNS-over-HTTPS (DoH)  |  Public DNS  |  Google for Developers](https://developers.google.com/speed/public-dns/docs/doh)
[Firefox DNS-over-HTTPS | Firefox Help (mozilla.org)](https://support.mozilla.org/en-US/kb/firefox-dns-over-https)

#### dns 污染

解决劫持后不知为何解析 youtube 解析不到 ipv6 地址。

```
yfy@kali:~$ nslookup www.youtube.com
Server:         2001:4860:4860::8888
Address:        2001:4860:4860::8888#53

Non-authoritative answer:
Name:   www.youtube.com
Address: 31.13.68.169
Name:   www.youtube.com
Address: 2001::1
```

但是手机连接后，却能够正常访问 `www.youtube.com`（自动跳转到 `m.youtube.com`），暂不清楚原因

理论上由于我已经设置让所有流量走隧道，而且 DNS 使用的是 google 的，因此虽然是明文也不会产生污染？

## 二层组网

由于 HE 需要有公网 ipv4，而我目前只有学校的教育网有公网 ipv4。因此必须在 op1 上才能搭建，但是我想要在 op2（出租屋）也能使用。于是再次需要以前用过的 L2 组网技术。

令人吃惊的事，由于 vlan 的隔离性，使得 L2 这么底层的技术，要让让流量从学校精确到我的出租屋，再到我的无线路由器，不能对其它网络造成干扰，**居然只需要添加 1 个 vid，点点点就行了**。简单到令人感觉到 vlan 真神奇

### vxlan 本来就可以复用链路

本来还在思考能否复用已有的 L2 隧道（原本已经基于 wg 两端搭建了一个 vxlan0 接口），比如**在隧道上运行 vlan** 是否支持。然后才意识到 vxlan 本来就是 vlan，有一个 vid，因此完全可以在两端再创建一个 vxlan1，指定不同的 vid 即可。

op2 添加 eth3，分配 vlan id 30

![image.png](https://imagebed.yfycloud.site/2025/12/2a1fd9902ae2c877efc2b52ce2bc92fa.png)

op2 需要增加一个 eth3 设备，和 vxlan 设备桥接在一起

![image.png](https://imagebed.yfycloud.site/2025/12/676deef342bce1908ae4b10c6b46ef56.png)

!!! note "openwrt 创建的 bridge 起不来"

    现象为 ip a 看不到 br-lan3。eth3 也看不到 master 标记。解决办法为 ip link 手动创建。
    ```
    ip link add name br-lan3 type bridge
    ip link set br-lan3 up              
    ip link set eth3 master br-lan3     
    ip link set vxlan1 master br-lan3 
    ```

### AP 节点

trunk 接口（刚好使用了原本的 WAN 口，这样接线时容易记起来）增加一个 vid 即可接入 vlan

![image.png](https://imagebed.yfycloud.site/2025/12/526b80c2e227cad241a8618726a666a1.png)

创建一个 interface，然后将 SSID 绑定到这个 interface 上，一切就完成了。连接该 SSID 即可连入 ipv6 only 的网络！

![image.png](https://imagebed.yfycloud.site/2025/12/b7380eaa724d2470791b2d37eeed8684.png)

![image.png](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20241007222617.png)

### 遇到的问题

刚开始连接 wifi 后还是不通，排查方法

- op1 上 kali 虚拟机是否能够获得地址
  - 不能 -》op1 检查防火墙
  - 还是不行，重启 lan2 接口
  - 能，继续下一步
- op2 上能否通过 vxlan 隧道 ping 通 op1 br-lan2 的 ipv6 链路地址
  - 能
- op2 下设备能否 ping 通op1 br-lan2 ipv6 链路地址
  - 不能 -》检查 AP 的 vlan 设置，发现没问题
  - op2 上创建 lan3 接口，使用 dhcpv6 client 协议
    - 能否获得 v6 地址
  - AP 上创建 lan3 接口，使用 dhcpv6 client 协议
    - 也可以获得 v6 地址
- 此时设备突然可以通过 wifi 获得 v6 地址了
- 后面发现，重点检查 vxlan 和 eth 接口的 master 是否确实是 br-lan。后面又遇到一次不通网，便是该问题。可以手动设置。

```
ip link set dev vxlan1 master br-lan3
```
