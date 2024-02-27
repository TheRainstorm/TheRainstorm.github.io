---
title: Wireguard组网
date: 2022-10-31 22:17:42
tags:
- wireguard
- iptables
- ip-rule
- openwrt
categories:
- 折腾
- 如何实现网络自由
---

wireguard是一种基于UDP的隧道协议，可以在不同设备间建立虚拟隧道，从而连接不同子网。本文总结了不同使用场景

<!-- more -->

## 异地组网

异地组网就是通过隧道技术，将两个独立的网络打通，让其中的设备能够通过内网地址直接相互访问。
### wg三层隧道

由于工作在三层，所以关键在于路由表的设置。

阿里云有VPC的概念，VPC之间是隔离的。阿里云提供了一些方式让其相互连接。这和我们的需求是非常类似的。
[云企业网和VPN网关连接不同VPC的优势和方法_专有网络 VPC-阿里云帮助中心 (aliyun.com)](https://help.aliyun.com/zh/vpc/user-guide/cross-vpc-interconnection-overview?spm=a2c4g.11186623.0.0.5e973905ohCbG9#b010e75036zhl)

这里列出两种通用网络结构
- 点对点连接。多个VPC间两两连接，保证延迟最低
- 星型结构，每个节点只需要配置和中心节点的连接
![image.png](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20231119113553.png)

![image.png](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20231119113807.png)

### wg+gretap二层隧道

TODO
## openwrt异地组网实例

### 我的网络结构例子

三个路由器通过wg两两连接（其实不一定需要这个结构，也可以配置成op2-op1-op3这种链状结构，这种结构主要降低了一次转发，延迟一般更短）

![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/picgo/20230218185024.png)
### wg site to site配置

#### 接口

在路由器上新建wg_s2s接口
- 协议选择Wireguard VPN
- 分配私有地址
- 配置好监听端口（之后在防火墙中设置allow input）

两边均创建好后再相互添加peer

op1
![image.png](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20231119200543.png)
![image.png](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20231119200631.png)

op2
![image.png](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20231119200722.png)
![image.png](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20231119200800.png)

op1上op2 peer设置例子
- allowed ip填写op2 wg_s2s接口设置的私有地址，并填写op2所在的子网网段
- route allow ip需要勾选，作用是让openwrt根据allowed ip生成路由
![image.png](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20231119201040.png)

#### 防火墙

两边需要添加以下防火墙规则，保证wg能从wan正常连接。协议勾选UDP即可
![image.png](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20231119203752.png)

然后是关于zone的设置。

wg_s2s接口可以配置成lan zone，在接口中勾选lan即可，如下图所示。
![image.png](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20231119204543.png)
这样后面的zone之间转发规则就不需要修改。以下段落可以跳过。

以下设置适合对防火墙原理感兴趣的用户：

为wg_s2s单独设置一个防火墙zone，可以使以后的配置更灵活。

op1和op2 lan,wan, wg_s2s zone的设置如下图：
- `lan -> wan, wg_s2s`：表示一个局域网的流量可以（1）访问互联网(wan) （2）通过wg_s2s接口访问对面子网(wg_s2s)
- `wg_s2s -> lan`：表示允许从wg_s2s进入的流量（对面子网通过wg_s2s）可以访问本子网
  - 这里还允许了wg_s2s -> wan是为了另一个子网通过本子网访问互联网的情况
- wg_s2s的**masquerading**可以勾选也可以不勾选
  - 勾选：表示从wg_s2s出去的流量会经过SNAT，即将源地址（可能是lan设备的地址）换为wg_s2s的地址。这样从一个子网访问另一个子网时，另一个子网只能看到经过NAT后的地址，而不知道发起设备的lan地址。
  - 不勾选：好处就是两个子网相互访问时能保留ip信息。缺点是由于只为wg_s2s设置了两边lan网段的路由（上一节的allowed ip），一个路由器上的其它接口（如wg1）无法通过wg_s2s访问另外一个子网。
    - 没有太多接口的简单网络情况下，建议是不勾选
![image.png](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20231119201258.png)

#### 路由

上面op2在添加op1 peer时，allowed ip设置了0.0.0.0/0，表示所有流量都走wg_s2s出去。即op2通过op1上网。
![image.png](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20231119205004.png)

wg_s2s peer设置好allowed ip的情况下，openwrt已经正确生成了路由规则，如下所示
```
root@op1 ➜  ~ ip ro
10.0.32.2 dev wg_s2s proto static scope link
192.168.36.0/24 dev wg_s2s proto static scope link
```

```
root@op2 ➜  ~ ip ro
default dev wg_s2s proto static scope link
10.0.32.1 dev wg_s2s proto static scope link
192.168.35.0/24 dev wg_s2s proto static scope link
```

以上异地组网已经完成了，可以尝试一个从子网访问另一个子网。
### 问题

#### 问题1：原路返回

如果一个子网通过另一个子网上网（上面配置中op2通过op1上网），则会遇到以下问题：
从外面访问op2 wan口的ipv4地址时，返回的包却从wg_s2s出去了（默认路由），这导致无法通过wan访问op2了。

解决办法：添加一条源地址的策略路由，表示只要src地址是wan口地址，均从wan口出去。
```
echo "10 wan" >> /etc/iproute2/rt_tables

ip ru add from <wan_ip> lookup wan prior 3
ip ro add default via <gateway> dev <wan_dev> proto static table wan
```

结果
```
root@op2 ➜  ~ ip ru
0:      from all lookup local
3:      from xxx lookup wan
32766:  from all lookup main
32767:  from all lookup default

root@op2 ➜  ~ ip ro show table wan
default via yyy dev eth0 proto static
```

p.s: 不过该原路返回也会导致无法从lan访问wan（不过应该也没人会这么用吧）
从lan访问wan时，会由于策略路由（src地址为wan地址时全部从wan出去）将响应从wan发出去，从而无法访问
```
root@op1 ➜  opkg tcpdump -ni any tcp and port 8000
tcpdump: data link type LINUX_SLL2
tcpdump: verbose output suppressed, use -v[v]... for full protocol decode
listening on any, link-type LINUX_SLL2 (Linux cooked v2), snapshot length 262144 bytes
19:07:00.982145 eth1  In  IP 192.168.35.2.50214 > 114.214.236.72.8000: Flags [S], seq 1381384154, win 64240, options [mss 1460,sackOK,TS val 2655701923 ecr 0,nop,wscale 7], length 0
19:07:00.982145 br-lan In  IP 192.168.35.2.50214 > 114.214.236.72.8000: Flags [S], seq 1381384154, win 64240, options [mss 1460,sackOK,TS val 2655701923 ecr 0,nop,wscale 7], length 0
19:07:00.982180 br-wan Out IP 114.214.236.72.8000 > 192.168.35.2.50214: Flags [S.], seq 256274565, ack 1381384155, win 65160, options [mss 1460,sackOK,TS val 2164672905 ecr 2655701923,nop,wscale 7], length 0
19:07:00.982181 eth0  Out IP 114.214.236.72.8000 > 192.168.35.2.50214: Flags [S.], seq 256274565, ack 1381384155, win 65160, options [mss 1460,sackOK,TS val 2164672905 ecr 2655701923,nop,wscale 7], length 0
```
#### 问题2：其它接口跨网络访问

之前提到，如果wg_s2s不设置**masquerading**，那么一个路由器下除了lan外的其它接口，均无法访问对面路由器的子网。

比如通常需要一个wg0用于从外面连接到内网。而该接口的私有地址和wg_s2s是不一样的。

在开启了masquerading时，不会出问题。比如手机通过wg0连回op1，再访问op2的lan。网络包的转发过程如下

![image.png](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20231119212900.png)

解决该问题的方法和上图是一样的，就是通过iptable，只针对wg1流量通过wg_s2s时进行SNAT
```
iptables -t nat -A POSTROUTING -s 172.16.0.0/24 -o wg_s2s -j MASQUERADE
```
该命令重启后失效，可以把它写入`/etc/rc.local`，在openwrt重启后自动运行。

更方便的是直接使用openwrt提供的NAT设置，设置会保存在`/etc/config/firewall`的`nat` section中。
![image.png](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20231119213524.png)

### wg其它相关问题

- wg allowip可以看作防火墙input规则。
- wg allowip默认情况下又会作为路由规则，表示哪些地址需要通过wg接口路由出去
    - openwrt支持一个选项，是否开启通过allow ip自动添加路由表

- **wg的allow ip同时设置了防火墙**
    - 对于发包来说，allow ip是路由。对于收包来说，allow ip是防火墙。而有时候我们希望这两个功能是分开的。
wg0 allowed ip如果设置为10.0.31.102/32，则表示其它src addr的包都会被丢弃。想要匀速任意包，需要设置为0.0.0.0/0。如下显示了一个wg0接口接受其它流量的效果。
```
root@op1 ➜  ~ tcpdump -ni any icmp and host 222.195.90.107
tcpdump: data link type LINUX_SLL2
tcpdump: verbose output suppressed, use -v[v]... for full protocol decode
listening on any, link-type LINUX_SLL2 (Linux cooked v2), snapshot length 262144 bytes
15:52:11.410653 wg0   In  IP 222.195.90.107 > 114.214.173.252: ICMP echo reply, id 26710, seq 561, length 64
15:52:12.410918 wg0   In  IP 222.195.90.107 > 114.214.173.252: ICMP echo reply, id 26710, seq 562, length 64
15:52:13.411181 wg0   In  IP 222.195.90.107 > 114.214.173.252: ICMP echo reply, id 26710, seq 563, length 64
```
#### 无法动态设置路由

推荐的功能，peer建立了连接时，才设置路由，而不是目前的提前设置好路由。这样能简化以下问题的解决。
##### 问题1
问题：两个op上均有wg0，用于手机等设备从外网连回。为了简化配置文件，分配了相同地址段，因此两个op的peer配置可以复用。然而这导致client通过wg0连入op1时，无法访问op2的网络。因为op2上收到包返回时，会从本地的wg0出去。

如果wg支持动态路由，那么目的地址是wg0 client的包就不会从本地wg0发出。而是走默认路由，通过op1-op2间的隧道发给op1。

**通过SNAT解决**

针对这个问题的一种可接受的解决办法是：针对源地址是wg0的包，对wg_s2s出去的流量进行SNAT
- 缺点是，这样一个lan访问另一个lan时，是看不到细节的，只能看到一个路由器访问另一个lan。不过由于wg0只是在外临时使用，因此也能接受。

```
iptables -t nat -A POSTROUTING -s 10.0.31.0/24 -o wg_s2s -j MASQUERADE
iptables -t nat -A POSTROUTING -s 10.0.33.0/24 -o wg_s2s -j MASQUERADE
```
##### 问题2
问题2：想要把wg地址作为某个设备绑定的地址。只要设备通过wg接入内网，那么在自己的网络中任何地方都能够访问该设备。然而现实是，**只有设备连接的那个子网可以访问**。
因为在两个op上只要设置了peer，那么无论是否和peer连接，都会设置到peer的路由。这使得op上访问wg0时，会从自己的wg0发出。

发现造成这个的原因在于，**wg无法在连接时动态地添加路由表**。如果是peer连接op1时，op1生成一条路由表。而op2上由于没有连接，便没有关于peer wg0地址的路由表。因此op2上访问peer时就会通过默认网关，而只需要在wg_s2s上添加一个wg0/24的路由表便可以一劳永逸了。

**妥协的方法**
wg0 client同时和连接两个op
- 这种对于树莓派这种还好，如果是手机可能就不行了。

## OSPF？

上面3个子网通过wg组网时，需要手动设置路由表。有没有一种方式，彻底让路由器自动配置呢？

这其实就是路由协议的作用，避免手动设置路由，而是让路由器自动学习路由表。常见的路由协议有：RIP，OSPF。但是**OSPF能否运行在wg构成的虚拟链路上呢？**

> **路由协定**（英语：Routing protocol）是一种指定[封包](https://zh.wikipedia.org/wiki/%E5%B0%81%E5%8C%85 "封包")转送方式的网路协定。[Internet](https://zh.wikipedia.org/wiki/Internet "Internet")网络的主要节点设备是[路由器](https://zh.wikipedia.org/wiki/%E8%B7%AF%E7%94%B1%E5%99%A8 "路由器")，路由器通过[路由表](https://zh.wikipedia.org/wiki/%E8%B7%AF%E7%94%B1%E8%A1%A8 "路由表")来转发接收到的数据。转发策略可以是人工指定的（通过[静态路由](https://zh.wikipedia.org/wiki/%E9%9D%9C%E6%85%8B%E8%B7%AF%E7%94%B1 "静态路由")、[策略路由](https://zh.wikipedia.org/wiki/%E7%AD%96%E7%95%A5%E8%B7%AF%E7%94%B1 "策略路由")等方法）。在具有较小规模的网络中，人工指定转发策略没有任何问题。但是在具有较大规模的网络中（如跨国企业网络、[ISP](https://zh.wikipedia.org/wiki/ISP "ISP")网络），如果通过人工指定转发策略，将会给网络管理员带来巨大的工作量，并且在管理、维护路由表上也变得十分困难。为了解决这个问题，动态路由协议应运而生。动态路由协议可以让路由器自动学习到其他路由器的网络，并且网络拓扑发生改变后自动更新路由表。网络管理员只需要配置动态路由协议即可，相比人工指定转发策略，工作量大大减少。

## wg使用场景

按照用途，列举几种使用场景
### 内网穿透

即需要从外网访问NAT后设备。

可以在路由器（有公网地址）上装wg，设置允许wg转发到wan和lan。其它设备（如手机）通过wg连接到路由器，从而可以访问路由器下局域网和通过路由器上网。
### 网络转发

#### 一级网络转发

一台设备通过另一台设备上网。

如实验室A服务器无法上网，B服务器可以上网（比如登录了网络通账号），A可以访问B。可以通过wg在A, B间建立隧道，设置A的默认路由器为wg，从而将A的流量都转发给B。B上再开启ipv4路由转发，A便可以上网。

*p.s 这里A和B虽同属于学校内网，但仍然不是同一个网段。**如果A和B位于同一个局域网**，则不需要使用wg，而是将A的网关设置为B，然后在B中设置将A的流量NAT即可。*

底层过程其实和上面内网穿透是一样的，不过有个不同的地方：

- **原路返回问题**：我们(假设为C)仍需要通过一个ip去直接访问A，请求ip包为(src=C, dst=A)。照理来说响应包的源地址应该是A，但是配置wg后，A的默认路由是wg，因此按照路由规则，响应包会变为(src=wg, dst=C)，并发送给B。B无法将私有地址的包发送到公网上去，因此C无法收到响应。
- 解决办法：使用**策略路由**，在应用wg的default路由前，提前将**源地址为A**的按照对应接口发送出去

#### 二级网络转发

同上，但是B服务器也是通过wg转发给另一台服务器C的。此时会遇到新的问题：

- 在按照上述配置完A后，会发现A仍然无法上网。过程如下：
  - A请求的包(src=wgA, dst=B站)
  - B接收后，转发给C(src=wgA, dst=B站)
  - C接收后，进行SNAT(src=C_WAN, dst=B站)，记录ip端口映射关系
  - B站响应(src=B站, dst=C_WAN)
  - C接收后，进行DNAT(src=B站, dst=wgA)
  - 此时可以发现，dst=wgA，C是无法路由给A的

解决方法：

- B上为wg接口**设置NAT**。过程如下：
  - A请求的包(src=wgA, dst=B站)
  - B接收后，进行SNAT(src=wgB, dst=B站)，转发给C
  - C接收后，进行SNAT(src=C_WAN, dst=B站)，记录ip端口映射关系
  - B站响应(src=B站, dst=C_WAN)
  - C接收后，进行DNAT(src=B站, dst=wgB)，转发给B
  - B接收后，进行DNAT(src=B站, dst=wgA)，转发给A
  - A接收到响应

上面二级网络转发的解决方法是，为从wg出去的流量设置NAT。
```bash
 iptables -t nat -A POSTROUTING -s 10.0.0.2 -o wg0 -j MASQUERADE
```

### 连接子网

连接两台路由器对应的子网，连接任一台路由器均可访问两个子网的设备。

即我的网络结构

## 原路返回问题/多网关设置

在客户端配置wireguard allowip为0.0.0.0/0后，会出现无法访问客户端自身的情况（ping, ssh）。

这是因为：
> linux 默认没有“流量原路返回”的功能

考虑有两个ISP的网络（多出口），如何做到数据原路返回呢

参考：[Routing for multiple uplinks/providers (lartc.org)](https://lartc.org/howto/lartc.rpdb.multiple-links.html#AEN267)

![image-20221031222237862](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/picgo/image-20221031222237862.png)

1. 首先，在main路由表中添加到两个ISP网段的路由，这保证可以访问到两个ISP的网关

2. 接着，添加默认路由。
   - 可以之后再添加策略路由，使得某些ip走IPS1，剩余走IPS2

3. （接下来两步用于保证数据能够原路返回，不会出现来自IPS1的流量，从IPS2出去）

4. 然后，创建两个新的路由表T1和T2，各自将对应的ISP设置为默认路由

5. 最后，添加路由策略。该规则根据包的源地址选择使用对应ISP的路由表（T1, T2）。
   - 这里，**重点在于需要原路返回的包，已经获得src地址了**？不需要原路返回的包，则根据之前的策略选择ISP出口后，设置src地址。

```bash
ip route add 211.200.0.0/30 dev eth1 src 221.200.0.2 table main
ip route add 58.56.0.0/30 dev eth2 src 58.56.0.2 table main

ip route add default via 221.200.0.1

ip route add 211.200.0.0/30 dev eth1 src 221.200.0.2 table T1
ip route add default via 221.200.0.1 table T1
ip route add 58.56.0.0/30 dev eth2 src 58.56.0.2 table T2
ip route add default via 58.56.0.1 table T2

ip rule add from 221.200.0.2 table T1
ip rule add from 58.56.0.2 table T2
```

## Wiregaurd + L2隧道组网

### L2隧道优点 vs 缺点

[I really like wireguard, but one thing that bugs me is the fact that it's layer ... | Hacker News (ycombinator.com)](https://news.ycombinator.com/item?id=22467869)

In most scenarios, you want to avoid L2 tunnels to reduce complexity and/or performance issues.
The chain of thought typically goes like this:

* Remote networks are connected via L2 tunnel.
* **ARP requests are broadcasted over L2 tunnel to all connected networks, introducing scalability issues**
* Proxy ARP is introduced to cache ARP responses
* Proxy ARP may become out of date or not scale as the L2 domain grows.
* BGP is introduced to keep track of and broadcast all topology changes
* How do you mitigate issues caused if Proxy ARP fails?

**Most of these issues go away if you use IP tunnels instead of Ethernet because IP was designed to be routable.**
### 各种隧道对比

各种隧道对比：[An introduction to Linux virtual interfaces: Tunnels | Red Hat Developer](https://developers.redhat.com/blog/2019/05/17/an-introduction-to-linux-virtual-interfaces-tunnels#gue)
- ipip
- gre, gretap

GRE tunnels
![gre](https://developers.redhat.com/blog/wp-content/uploads/2019/03/gre.png)

GRETAP
![](https://developers.redhat.com/blog/wp-content/uploads/2019/03/gretap.png)


一种协同使用多种隧道例子
- udp2raw：wg基于udp，可能被运营商qos。使用udp2raw 实现udp in tcp
- wg：L3隧道
- gre: 图中的是tun，仍是三层隧道
[wireguard, wireguard layer 2, wireguard over TCP (github.com)](https://gist.github.com/zOrg1331/a2a7ffb3cfe3b3b821d45d6af00cb8f6)

```
 Host on private LAN                                         Host on the Internet
 +---------------------------------+                       +-------------------------------+
 |   brtun bridge                  |                       |                  brtun bridge |
 | +-------------+                 |                       |                 +--------+    |
 | | ethX gretun |<->wg0<->udp2raw | <-Internet, TCP 443-> | udp2raw<->wg0<->| gretun |    |
 | +-------------+                 |                       |                 +--------+    |
 +---------------------------------+                       +-------------------------------+
 
 brtun: 192.168.0.200/24                                    brtun: 192.168.0.50/24
 wg0: 12.12.12.2/24                                         wg0: 12.12.12.1/24
 gretun: 12.12.12.2->12.12.12.1                             gretun: 12.12.12.1->12.12.12.2
```
## openwrt gre配置

参考资料：

- openwrt gre配置：[[OpenWrt Wiki] Tunneling interface protocols](https://openwrt.org/docs/guide-user/network/tunneling_interface_protocols#protocol_gretap_ethernet_gre_tunnel_over_ipv4)
- [[OpenWrt Wiki] Routing example: GRE](https://openwrt.org/docs/guide-user/network/routing/examples/routing_in_gre)
- GRE ip包中protocol number为47：[List of IP protocol numbers - Wikipedia](https://en.wikipedia.org/wiki/List_of_IP_protocol_numbers)
### 背景

背景：学校宿舍楼没有分配PD，而实验楼分配了/64的PD。因此想通过L2隧道，将宿舍楼的接口桥接到实验楼路由器的wan口上，从而获得一个PD地址。之后利用该PD在lan上开启ipv6 ra server，给lan分配ipv6地址。

思路：两台路由器op1, op2通过wg连接，基于wg接口ip建立gretap隧道。op1将该tap桥接到br-wan上。op2在该tap上开启dhcpv6 client，申请一个PD。
### 安装

确保安装了以下依赖
```
root@op1 ➜  ~ opkg list-installed |grep gre
gre - 13
kmod-gre - 5.10.146-1
kmod-gre6 - 5.10.146-1
luci-proto-gre - git-21.158.43143-b4c394f
```

确保以下内核模块已加载
```
root@op1 ➜  ~ lsmod |grep gre
gre                    16384  1 ip_gre
ip_gre                 36864  0
ip_tunnel              32768  1 ip_gre
```

如果是pve的话，通常没有加载。需要手动modprobe，并添加到`/etc/module`中
```
modprobe ip_gre
```

```
gre
ip_gre
ip_tunnel
ip6_gre
ip6_tunnel
```

安装了gre后，luci中创建接口时可能还是无法选择gre，此时需要重启network: `/etc/init.d/network restart`

### 配置

#### op1和op2上都创建gre1接口
- protocal选择gretap over ipv4
- local和remote地址填wg接口地址
- 创建成功后，ip a可以看到多出一个gre4t-gre1的接口
![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20230915185240.png)

如果使用wan口ipv6创建gre tap，两端都需要添加allow gre input的防火墙规则。默认是没有gre类型的，在custom中输入47或则gre回车便会出现该类型。
![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20240227171647.png)

#### op1将gre device添加到bridge

- 名字填@gre1（也可以直接写gre4t-gre1）
![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20230915185229.png)

#### op1设置防火墙 wan forward

- 将gre1设置为wan
- 防火墙中，设置**wan zone forward为accept**（默认为reject）。**否则gre1设备上的包无法转发给wan下面的其他设备**
![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20230915190627.png)

![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20230915190345.png)

#### op2设置dhcpv6

在gre1 tap上启用dhcpv6 client，openwrt上该操作为创建一个interface，协议选择dhcpv6 client
- 该接口高级设置中可以勾选source route，这样对于有多个uplink，就能自动处理路由
    - 源地址为该pd的地址，走tap接口
    - 源地址为wan口slaac的地址，走原来的wan口
![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20230915185518.png)

## ubuntu gre配置

- 先使用wg0，建立wiregaurd连接
- 再使用gretap建立二层隧道
  - 接着op端在gretap device上创建dhcp6的client（由于只需要ipv6 PD，因此可以不设置dhcpv4）
  - ubuntu端将gretap和br0(ustcnet bridge)桥接
- 此时op已经可以获得ipv6 PD了
- lan interface上勾线ipv6 prefix，开启ra server。之后lan内设备就可以获得ipv6地址了
- 此时lan内设备ipv6仍无法上网，**需要在ubuntu上开启ipv6 forward**

```
sudo systemctl start wg-quick@op2-gre-wg0
sudo ip link add op2-gre1 type gretap  local 10.0.31.10 remote 10.0.31.2 ttl 255
sudo ip link set op2-gre1 up
sudo ip link set op2-gre1 master br0
```

## gre不通，chatgpt回复

我创建了一个pve lxc容器，分配的网络接口eth0对应pve的vmbr0，容器内eth0接在br-wan上。然后我在pve lxc容器中创建了一个gretap设备，桥接到br-wan上，但是gretap上的ipv6 rs报文无法通过br-wan发送到eth0，从而无法正确发送到pve外的vmbr0，我该怎么做

ChatGPT

您的网络拓扑中包含了多层虚拟化网络（PVE容器内的GRETAP设备、LXC容器和PVE宿主机）。为了确保GRETAP设备的IPv6 RS报文能够正确传递到PVE宿主机的vmbr0以外的网络，您需要进行一些网络配置。以下是可能的解决方法：
1. **检查IPv6 Forwarding设置**：首先，确保PVE宿主机上启用了IPv6转发功能。可以使用以下命令检查：
    `sysctl net.ipv6.conf.all.forwarding`
    如果返回值为1，表示已启用IPv6转发。如果返回值为0，可以使用以下命令启用它：
    `sysctl -w net.ipv6.conf.all.forwarding=1`
    为了使此更改持久化，您可以将它添加到 `/etc/sysctl.conf` 文件中。
    
1. **LXC容器网络配置**：确保LXC容器内的GRETAP设备和br-wan接口正确配置。检查GRETAP设备的IPv6地址、子网和路由是否正确设置。确保GRETAP设备能够正确路由IPv6流量。
    
3. **容器内防火墙规则**：如果LXC容器内有防火墙规则，确保它们不会阻止IPv6流量从GRETAP设备传递到br-wan接口。您可能需要在容器内的防火墙规则中添加允许IPv6流量通过的规则。
    
4. **PVE宿主机网络桥配置**：确保PVE宿主机上的网络桥（vmbr0和br-wan）正确配置，以允许IPv6流量正确传递。检查它们的IPv6地址、子网和路由设置。
    
5. **LXC容器间隔离设置**：请确保在PVE宿主机的网络配置中，LXC容器之间的网络隔离设置不会阻止IPv6流量的传递。这可能需要调整安全组或网络隔离规则。
    
6. **MTU设置**：在多层虚拟化网络中，MTU（最大传输单元）问题可能会导致通信问题。确保各个网络设备的MTU设置正确，并且不会导致分段或丢失数据包。
    
7. **网络抓包**：如果问题仍然存在，您可以在不同的网络设备上使用抓包工具（如Wireshark或tcpdump）来捕获IPv6流量，以便更详细地分析问题并找出故障的位置。
    
请根据上述建议逐步检查和调整您的网络配置，以解决IPv6 RS报文无法正确传递的问题。确保在更改网络配置之前备份重要数据，以防意外发生。

上面提到的：
> 确保它们不会阻止IPv6流量从GRETAP设备传递到br-wan接口。

真的让我找到了问题！



## 相关小实验

### 绕路返回：wan口进入, wg接口返回

网络情况
- op2（发起ping）
    - eth0: 114.214.173.252
- king3399（响应ping）
    - eth0: 222.195.90.107
    - wg0: endpoint op1, default route
- op1（路由中转）
    - br-wan: 114.214.236.72

icmp request
op2(eth0) -> king(eth0)
- route走学校

icmp reply
king(eth0) -> op2(eth0)
- route通过wg0，发送给op1
- op1再转发，从br-wan出去，到达op2

op1收到king的icmp reply再转发，实际有两个障碍
1. op1将wg0收到的src地址为op2(eth0)的包丢弃，因为不在allow ip中。解决办法：allow ip设置为0.0.0.0，关闭自动添加路由
2. op1 wg0收到包后，却发现并没有从wan口发送出去

以下是对问题2的探究

首先king上符合预期，从eth0收到icmp request，从wg0返回icmp reply
```
tcpdump -ni any icmp and host 222.195.90.107

22:08:20.292237 eth0  In  IP 114.214.173.252 > 222.195.90.107: ICMP echo request, id 65124, seq 5, length 64
22:08:20.292430 wg0   Out IP 222.195.90.107 > 114.214.173.252: ICMP echo reply, id 65124, seq 5, length 64
```

问题出现在op1，可以看到wg0收到了包，但是却没有任何output
```
root@op1 ➜  ~ tcpdump -ni any icmp and host 114.214.173.252

22:09:22.298394 wg0   In  IP 222.195.90.107 > 114.214.173.252: ICMP echo reply, id 65124, seq 67, length 64
22:09:23.298654 wg0   In  IP 222.195.90.107 > 114.214.173.252: ICMP echo reply, id 65124, seq 68, length 64
```

研究后发现使用nft trace可以追踪包在防火墙中的处理顺序
- trace id标识一个包
- 可以看到依次经过以下chain处理，结尾的verdict（判决）表示处理结果
    - raw_prerouting
    - mangle_prerouting
    - prerouting
    - mangle_forward
    - forward
        - 在这里匹配`meta nfproto ipv4 oifname { "br-wan", "gre4t-gre1" } ct state invalid counter drop`规则，然后被drop了
```c++
trace id 146d2af5 inet fw4 debug packet: iif "wg0" ip saddr 222.195.90.107 ip daddr 114.214.173.252 ip dscp cs0 ip ecn not-ect ip ttl 64 ip id 19723 ip protocol icmp ip length 84 icmp type echo-reply icmp code net-unreachable icmp id 14312 icmp sequence 881 @th,64,96 0x8cdff2c20000000000000000
trace id 146d2af5 inet fw4 debug rule iifname "wg0" ip saddr 222.195.90.107 meta nftrace set 1 counter packets 4 bytes 336 (verdict continue)
trace id 146d2af5 inet fw4 debug verdict continue
trace id 146d2af5 inet fw4 debug policy accept
trace id 146d2af5 inet fw4 raw_prerouting packet: iif "wg0" ip saddr 222.195.90.107 ip daddr 114.214.173.252 ip dscp cs0 ip ecn not-ect ip ttl 64 ip id 19723 ip protocol icmp ip length 84 icmp type echo-reply icmp code net-unreachable icmp id 14312 icmp sequence 881 @th,64,96 0x8cdff2c20000000000000000
trace id 146d2af5 inet fw4 raw_prerouting verdict continue
trace id 146d2af5 inet fw4 raw_prerouting policy accept
trace id 146d2af5 inet fw4 mangle_prerouting packet: iif "wg0" ip saddr 222.195.90.107 ip daddr 114.214.173.252 ip dscp cs0 ip ecn not-ect ip ttl 64 ip id 19723 ip protocol icmp ip length 84 icmp type echo-reply icmp code net-unreachable icmp id 14312 icmp sequence 881 @th,64,96 0x8cdff2c20000000000000000
trace id 146d2af5 inet fw4 mangle_prerouting verdict continue
trace id 146d2af5 inet fw4 mangle_prerouting policy accept
trace id 146d2af5 inet fw4 prerouting packet: iif "wg0" ip saddr 222.195.90.107 ip daddr 114.214.173.252 ip dscp cs0 ip ecn not-ect ip ttl 64 ip id 19723 ip protocol icmp ip length 84 icmp type echo-reply icmp code net-unreachable icmp id 14312 icmp sequence 881 @th,64,96 0x8cdff2c20000000000000000
trace id 146d2af5 inet fw4 prerouting rule iifname { "wg0", "br-lan", "ztyou4dlov" } jump helper_lan comment "!fw4: Handle lan IPv4/IPv6 helper assignment" (verdict jump helper_lan)
trace id 146d2af5 inet fw4 helper_lan verdict continue
trace id 146d2af5 inet fw4 prerouting verdict continue
trace id 146d2af5 inet fw4 prerouting policy accept
trace id 146d2af5 inet fw4 mangle_forward packet: iif "wg0" oif "br-wan" ip saddr 222.195.90.107 ip daddr 114.214.173.252 ip dscp cs0 ip ecn not-ect ip ttl 63 ip id 19723 ip protocol icmp ip length 84 icmp type echo-reply icmp code net-unreachable icmp id 14312 icmp sequence 881 @th,64,96 0x8cdff2c20000000000000000
trace id 146d2af5 inet fw4 mangle_forward verdict continue
trace id 146d2af5 inet fw4 mangle_forward policy accept
trace id 146d2af5 inet fw4 forward packet: iif "wg0" oif "br-wan" ip saddr 222.195.90.107 ip daddr 114.214.173.252 ip dscp cs0 ip ecn not-ect ip ttl 63 ip id 19723 ip protocol icmp ip length 84 icmp type echo-reply icmp code net-unreachable icmp id 14312 icmp sequence 881 @th,64,96 0x8cdff2c20000000000000000
trace id 146d2af5 inet fw4 forward rule iifname { "wg0", "br-lan", "ztyou4dlov" } jump forward_lan comment "!fw4: Handle lan IPv4/IPv6 forward traffic" (verdict jump forward_lan)
trace id 146d2af5 inet fw4 forward_lan rule jump accept_to_wan comment "!fw4: Accept lan to wan forwarding" (verdict jump accept_to_wan)
trace id 146d2af5 inet fw4 accept_to_wan rule meta nfproto ipv4 oifname { "br-wan", "gre4t-gre1" } ct state invalid counter packets 31820 bytes 3109375 drop comment "!fw4: Prevent NAT leakage" (verdict drop)
```

通过nft修改掉该drop，发现就能ping通了
op1上tcpdump可以看到正确从br-wan转发
```
23:38:13.018068 wg0   In  IP 222.195.90.107 > 114.214.173.252: ICMP echo reply, id 14312, seq 2631, length 64
23:38:13.018089 br-wan Out IP 222.195.90.107 > 114.214.173.252: ICMP echo reply, id 14312, seq 2631, length 64
```

op2和king上都能看到conntrack信息
```
root@op2 ➜  ~ conntrack -L -p icmp -d 222.195.90.107
icmp     1 29 src=114.214.173.252 dst=222.195.90.107 type=8 code=0 id=31588 packets=112 bytes=9408 src=222.195.90.107 dst=114.214.173.252 type=0 code=0 id=31588 packets=104 bytes=8736 mark=0 use=1
conntrack v1.4.8 (conntrack-tools): 1 flow entries have been shown.
```
不过op1上没有（难道转发不算？）
```
root@op1 ➜  ~ conntrack -L -p icmp |grep 222.195.90.107
conntrack v1.4.8 (conntrack-tools): 151 flow entries have been shown.
```

但是该规则到底是什么意思呢？ct invalid为什么会匹配？

连接跟踪是 Linux 内核中的一项功能，用于跟踪网络连接的状态。以下是一些常见的连接跟踪状态：
1. **`new`（新连接）**：表示这是一个新的、尚未建立的连接。
2. **`established`（已建立）**：表示连接已经成功建立，数据可以在源和目标之间传输。
3. **`related`（相关连接）**：表示这是与现有连接相关的新连接，例如 FTP 数据连接与 FTP 控制连接的关系。
4. **`untracked`（未跟踪）**：表示连接未被连接跟踪系统跟踪。
5. **`snat`（源 NAT）**：表示连接经过源地址转换。
6. **`dnat`（目标 NAT）**：表示连接经过目标地址转换。
7. **`tracert`（跟踪路由）**：表示这是一个 ICMP 跟踪路由的连接。
8. **`dying`（关闭中）**：表示连接即将关闭。
9. **`reply`（回复）**：表示这是一个 ICMP Echo Reply 报文。
10. **`timeout`（超时）**：表示连接已超时。
11. **`closed`（已关闭）**：表示连接已关闭。
12. **`invalid`（无效）**：表示连接出现异常或不合法的状态，例如，连接的报文顺序不正确等。

`ct state invalid` 就是匹配连接跟踪状态为 "invalid" 的报文，通常表示连接出现了一些问题，可能是由于报文的顺序不正确或其他异常情况。

fw4规则注释中提到的Prevent NAT leakage，搜索
[LuCI option to enable/disable "NAT Leakage Prevention" - Installing and Using OpenWrt - OpenWrt Forum](https://forum.openwrt.org/t/luci-option-to-enable-disable-nat-leakage-prevention/49536/12)
> This rule is only generated for firewall zones with masquerading
> how in blazes would non-NATted/martian packets leak to the WAN?

[NAT leakage on 22.03 [fw4] - Installing and Using OpenWrt - OpenWrt Forum](https://forum.openwrt.org/t/nat-leakage-on-22-03-fw4/140790)
知道了有`masq_allow_invalid`这么一个选项[[OpenWrt Wiki] Firewall configuration /etc/config/firewall](https://openwrt.org/docs/guide-user/firewall/firewall_configuration)

|   |   |   |   |   |
|---|---|---|---|---|
|`masq_allow_invalid`|boolean|no|`0`|Do not add `DROP INVALID` rules, if masquerading is used. The `DROP` rules are supposed to prevent NAT leakage (see [commit in firewall3](https://git.lede-project.org/?p=project/firewall3.git;a=commit;h=e751cde8954a09ea32f67a8bf7974b4dc1395f2e "https://git.lede-project.org/?p=project/firewall3.git;a=commit;h=e751cde8954a09ea32f67a8bf7974b4dc1395f2e")).|

GUI中解释：
> Do not install extra rules to reject forwarded traffic with conntrack state _invalid_. This may be required for complex asymmetric route setups.

[NAT: Masquerade can leak private IP, why&how? - MikroTik](https://forum.mikrotik.com/viewtopic.php?t=177210)
- 大概就是接口down再up，有一些包没有正确的ct状态，不会经过masq。