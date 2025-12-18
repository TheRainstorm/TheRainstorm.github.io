---
title: Wireguard 组网
date: 2022-10-31 22:17:42
tags:
- wireguard
- iptables
- ip-rule
- openwrt
- 如何实现网络自由
categories:
- 折腾记录
---

wireguard 是一种基于 UDP 的隧道协议，可以在不同设备间建立虚拟隧道，从而连接不同子网。本文总结了不同使用场景

<!-- more -->

## 异地组网

异地组网就是通过隧道技术，将两个独立的网络打通，让其中的设备能够通过内网地址直接相互访问。

### wg 三层隧道

由于工作在三层，所以关键在于路由表的设置。

阿里云有 VPC 的概念，VPC 之间是隔离的。阿里云提供了一些方式让其相互连接。这和我们的需求是非常类似的。
[云企业网和 VPN 网关连接不同 VPC 的优势和方法_专有网络 VPC-阿里云帮助中心 (aliyun.com)](https://help.aliyun.com/zh/vpc/user-guide/cross-vpc-interconnection-overview?spm=a2c4g.11186623.0.0.5e973905ohCbG9#b010e75036zhl)

这里列出两种通用网络结构

- 点对点连接。多个 VPC 间两两连接，保证延迟最低
- 星型结构，每个节点只需要配置和中心节点的连接
![image.png](https://imagebed.yfycloud.site/2025/12/e6bed01a693962f06c78c6d7b1b71c71.png)

![image.png](https://imagebed.yfycloud.site/2025/12/1586661f4c3fccbd44f018a51ed4d0e9.png)

### wg+gretap 二层隧道

TODO

## openwrt 异地组网实例

### 我的网络结构例子

三个路由器通过 wg 两两连接（其实不一定需要这个结构，也可以配置成 op2-op1-op3 这种链状结构，这种结构主要降低了一次转发，延迟一般更短）

![](https://imagebed.yfycloud.site/2025/12/16e0ab611f09adaa806929d5366a36c2.png)

### wg site to site 配置

#### 接口

在路由器上新建 wg_s2s 接口

- 协议选择 Wireguard VPN
- 分配私有地址
- 配置好监听端口（之后在防火墙中设置 allow input）

两边均创建好后再相互添加 peer

op1
![image.png](https://imagebed.yfycloud.site/2025/12/0032f54f93477d9c73a05fda22873fbd.png)
![image.png](https://imagebed.yfycloud.site/2025/12/a5fe917e7d1e4559ef76cd4169c9fd2d.png)

op2
![image.png](https://imagebed.yfycloud.site/2025/12/d7372ac5cd0e974ec59b3b34a0cb408e.png)
![image.png](https://imagebed.yfycloud.site/2025/12/3af4f5969ed2421881628e572f031eb5.png)

op1 上 op2 peer 设置例子

- allowed ip 填写 op2 wg_s2s 接口设置的私有地址，并填写 op2 所在的子网网段
- route allow ip 需要勾选，作用是让 openwrt 根据 allowed ip 生成路由
![image.png](https://imagebed.yfycloud.site/2025/12/18831d8618cf8158532ea57e54560856.png)

#### 防火墙

两边需要添加以下防火墙规则，保证 wg 能从 wan 正常连接。协议勾选 UDP 即可
![image.png](https://imagebed.yfycloud.site/2025/12/0f01b068304c6e35d5224bc770cc51f1.png)

然后是关于 zone 的设置。

wg_s2s 接口可以配置成 lan zone，在接口中勾选 lan 即可，如下图所示。
![image.png](https://imagebed.yfycloud.site/2025/12/94beecb15506e5dcefa480bb2f193873.png)
这样后面的 zone 之间转发规则就不需要修改。以下段落可以跳过。

以下设置适合对防火墙原理感兴趣的用户：

为 wg_s2s 单独设置一个防火墙 zone，可以使以后的配置更灵活。

op1 和 op2 lan,wan, wg_s2s zone 的设置如下图：

- `lan -> wan, wg_s2s`：表示一个局域网的流量可以（1）访问互联网 (wan) （2）通过 wg_s2s 接口访问对面子网 (wg_s2s)
- `wg_s2s -> lan`：表示允许从 wg_s2s 进入的流量（对面子网通过 wg_s2s）可以访问本子网
  - 这里还允许了 wg_s2s -> wan 是为了另一个子网通过本子网访问互联网的情况
- wg_s2s 的**masquerading**可以勾选也可以不勾选
  - 勾选：表示从 wg_s2s 出去的流量会经过 SNAT，即将源地址（可能是 lan 设备的地址）换为 wg_s2s 的地址。这样从一个子网访问另一个子网时，另一个子网只能看到经过 NAT 后的地址，而不知道发起设备的 lan 地址。
  - 不勾选：好处就是两个子网相互访问时能保留 ip 信息。缺点是由于只为 wg_s2s 设置了两边 lan 网段的路由（上一节的 allowed ip），一个路由器上的其它接口（如 wg1）无法通过 wg_s2s 访问另外一个子网。
    - 没有太多接口的简单网络情况下，建议是不勾选
![image.png](https://imagebed.yfycloud.site/2025/12/a5dca9f0e713a94e1692a9dd043e154a.png)

#### 路由

上面 op2 在添加 op1 peer 时，allowed ip 设置了 0.0.0.0/0，表示所有流量都走 wg_s2s 出去。即 op2 通过 op1 上网。
![image.png](https://imagebed.yfycloud.site/2025/12/573493dcf6e00240ce1dd0f10441c6bf.png)

wg_s2s peer 设置好 allowed ip 的情况下，openwrt 已经正确生成了路由规则，如下所示

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

#### 问题 1：原路返回

如果一个子网通过另一个子网上网（上面配置中 op2 通过 op1 上网），则会遇到以下问题：
从外面访问 op2 wan 口的 ipv4 地址时，返回的包却从 wg_s2s 出去了（默认路由），这导致无法通过 wan 访问 op2 了。

解决办法：添加一条源地址的策略路由，表示只要 src 地址是 wan 口地址，均从 wan 口出去。

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

p.s: 不过该原路返回也会导致无法从 lan 访问 wan（不过应该也没人会这么用吧）
从 lan 访问 wan 时，会由于策略路由（src 地址为 wan 地址时全部从 wan 出去）将响应从 wan 发出去，从而无法访问

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

#### 问题 2：其它接口跨网络访问

之前提到，如果 wg_s2s 不设置**masquerading**，那么一个路由器下除了 lan 外的其它接口，均无法访问对面路由器的子网。

比如通常需要一个 wg0 用于从外面连接到内网。而该接口的私有地址和 wg_s2s 是不一样的。

在开启了 masquerading 时，不会出问题。比如手机通过 wg0 连回 op1，再访问 op2 的 lan。网络包的转发过程如下

![image.png](https://imagebed.yfycloud.site/2025/12/fb3355ef4326a32e7a9f9348451215e2.png)

解决该问题的方法和上图是一样的，就是通过 iptable，只针对 wg1 流量通过 wg_s2s 时进行 SNAT

```
iptables -t nat -A POSTROUTING -s 172.16.0.0/24 -o wg_s2s -j MASQUERADE
```

该命令重启后失效，可以把它写入`/etc/rc.local`，在 openwrt 重启后自动运行。

更方便的是直接使用 openwrt 提供的 NAT 设置，设置会保存在`/etc/config/firewall`的`nat` section 中。
![image.png](https://imagebed.yfycloud.site/2025/12/140393c0f323c91549a30b3f0d07c136.png)

### wg 其它相关问题

- wg allowip 可以看作防火墙 input 规则。
- wg allowip 默认情况下又会作为路由规则，表示哪些地址需要通过 wg 接口路由出去
  - openwrt 支持一个选项，是否开启通过 allow ip 自动添加路由表

- **wg 的 allow ip 同时设置了防火墙**
  - 对于发包来说，allow ip 是路由。对于收包来说，allow ip 是防火墙。而有时候我们希望这两个功能是分开的。
wg0 allowed ip 如果设置为 10.0.31.102/32，则表示其它 src addr 的包都会被丢弃。想要匀速任意包，需要设置为 0.0.0.0/0。如下显示了一个 wg0 接口接受其它流量的效果。

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

推荐的功能，peer 建立了连接时，才设置路由，而不是目前的提前设置好路由。这样能简化以下问题的解决。

##### 问题 1

问题：两个 op 上均有 wg0，用于手机等设备从外网连回。为了简化配置文件，分配了相同地址段，因此两个 op 的 peer 配置可以复用。然而这导致 client 通过 wg0 连入 op1 时，无法访问 op2 的网络。因为 op2 上收到包返回时，会从本地的 wg0 出去。

如果 wg 支持动态路由，那么目的地址是 wg0 client 的包就不会从本地 wg0 发出。而是走默认路由，通过 op1-op2 间的隧道发给 op1。

**通过 SNAT 解决**

针对这个问题的一种可接受的解决办法是：针对源地址是 wg0 的包，对 wg_s2s 出去的流量进行 SNAT

- 缺点是，这样一个 lan 访问另一个 lan 时，是看不到细节的，只能看到一个路由器访问另一个 lan。不过由于 wg0 只是在外临时使用，因此也能接受。

```
iptables -t nat -A POSTROUTING -s 10.0.31.0/24 -o wg_s2s -j MASQUERADE
iptables -t nat -A POSTROUTING -s 10.0.33.0/24 -o wg_s2s -j MASQUERADE
```

##### 问题 2

问题 2：想要把 wg 地址作为某个设备绑定的地址。只要设备通过 wg 接入内网，那么在自己的网络中任何地方都能够访问该设备。然而现实是，**只有设备连接的那个子网可以访问**。
因为在两个 op 上只要设置了 peer，那么无论是否和 peer 连接，都会设置到 peer 的路由。这使得 op 上访问 wg0 时，会从自己的 wg0 发出。

发现造成这个的原因在于，**wg 无法在连接时动态地添加路由表**。如果是 peer 连接 op1 时，op1 生成一条路由表。而 op2 上由于没有连接，便没有关于 peer wg0 地址的路由表。因此 op2 上访问 peer 时就会通过默认网关，而只需要在 wg_s2s 上添加一个 wg0/24 的路由表便可以一劳永逸了。

**妥协的方法**
wg0 client 同时和连接两个 op

- 这种对于树莓派这种还好，如果是手机可能就不行了。

## OSPF？

上面 3 个子网通过 wg 组网时，需要手动设置路由表。有没有一种方式，彻底让路由器自动配置呢？

这其实就是路由协议的作用，避免手动设置路由，而是让路由器自动学习路由表。常见的路由协议有：RIP，OSPF。但是**OSPF 能否运行在 wg 构成的虚拟链路上呢？**

> **路由协定**（英语：Routing protocol）是一种指定[封包](https://zh.wikipedia.org/wiki/%E5%B0%81%E5%8C%85 "封包")转送方式的网路协定。[Internet](https://zh.wikipedia.org/wiki/Internet "Internet")网络的主要节点设备是[路由器](https://zh.wikipedia.org/wiki/%E8%B7%AF%E7%94%B1%E5%99%A8 "路由器")，路由器通过[路由表](https://zh.wikipedia.org/wiki/%E8%B7%AF%E7%94%B1%E8%A1%A8 "路由表")来转发接收到的数据。转发策略可以是人工指定的（通过[静态路由](https://zh.wikipedia.org/wiki/%E9%9D%9C%E6%85%8B%E8%B7%AF%E7%94%B1 "静态路由")、[策略路由](https://zh.wikipedia.org/wiki/%E7%AD%96%E7%95%A5%E8%B7%AF%E7%94%B1 "策略路由")等方法）。在具有较小规模的网络中，人工指定转发策略没有任何问题。但是在具有较大规模的网络中（如跨国企业网络、[ISP](https://zh.wikipedia.org/wiki/ISP "ISP")网络），如果通过人工指定转发策略，将会给网络管理员带来巨大的工作量，并且在管理、维护路由表上也变得十分困难。为了解决这个问题，动态路由协议应运而生。动态路由协议可以让路由器自动学习到其他路由器的网络，并且网络拓扑发生改变后自动更新路由表。网络管理员只需要配置动态路由协议即可，相比人工指定转发策略，工作量大大减少。

## wg 使用场景

按照用途，列举几种使用场景

### 内网穿透

即需要从外网访问 NAT 后设备。

可以在路由器（有公网地址）上装 wg，设置允许 wg 转发到 wan 和 lan。其它设备（如手机）通过 wg 连接到路由器，从而可以访问路由器下局域网和通过路由器上网。

### 网络转发

#### 一级网络转发

一台设备通过另一台设备上网。

如实验室 A 服务器无法上网，B 服务器可以上网（比如登录了网络通账号），A 可以访问 B。可以通过 wg 在 A, B 间建立隧道，设置 A 的默认路由器为 wg，从而将 A 的流量都转发给 B。B 上再开启 ipv4 路由转发，A 便可以上网。

*p.s 这里 A 和 B 虽同属于学校内网，但仍然不是同一个网段。**如果 A 和 B 位于同一个局域网**，则不需要使用 wg，而是将 A 的网关设置为 B，然后在 B 中设置将 A 的流量 NAT 即可。*

底层过程其实和上面内网穿透是一样的，不过有个不同的地方：

- **原路返回问题**：我们 (假设为 C) 仍需要通过一个 ip 去直接访问 A，请求 ip 包为 (src=C, dst=A)。照理来说响应包的源地址应该是 A，但是配置 wg 后，A 的默认路由是 wg，因此按照路由规则，响应包会变为 (src=wg, dst=C)，并发送给 B。B 无法将私有地址的包发送到公网上去，因此 C 无法收到响应。
- 解决办法：使用**策略路由**，在应用 wg 的 default 路由前，提前将**源地址为 A**的按照对应接口发送出去

#### 二级网络转发

同上，但是 B 服务器也是通过 wg 转发给另一台服务器 C 的。此时会遇到新的问题：

- 在按照上述配置完 A 后，会发现 A 仍然无法上网。过程如下：
  - A 请求的包 (src=wgA, dst=B 站)
  - B 接收后，转发给 C(src=wgA, dst=B 站)
  - C 接收后，进行 SNAT(src=C_WAN, dst=B 站)，记录 ip 端口映射关系
  - B 站响应 (src=B 站，dst=C_WAN)
  - C 接收后，进行 DNAT(src=B 站，dst=wgA)
  - 此时可以发现，dst=wgA，C 是无法路由给 A 的

解决方法：

- B 上为 wg 接口**设置 NAT**。过程如下：
  - A 请求的包 (src=wgA, dst=B 站)
  - B 接收后，进行 SNAT(src=wgB, dst=B 站)，转发给 C
  - C 接收后，进行 SNAT(src=C_WAN, dst=B 站)，记录 ip 端口映射关系
  - B 站响应 (src=B 站，dst=C_WAN)
  - C 接收后，进行 DNAT(src=B 站，dst=wgB)，转发给 B
  - B 接收后，进行 DNAT(src=B 站，dst=wgA)，转发给 A
  - A 接收到响应

上面二级网络转发的解决方法是，为从 wg 出去的流量设置 NAT。

```bash
 iptables -t nat -A POSTROUTING -s 10.0.0.2 -o wg0 -j MASQUERADE
```

### 连接子网

连接两台路由器对应的子网，连接任一台路由器均可访问两个子网的设备。

即我的网络结构

## 原路返回问题/多网关设置

在客户端配置 wireguard allowip 为 0.0.0.0/0 后，会出现无法访问客户端自身的情况（ping, ssh）。

这是因为：
> linux 默认没有“流量原路返回”的功能

考虑有两个 ISP 的网络（多出口），如何做到数据原路返回呢

参考：[Routing for multiple uplinks/providers (lartc.org)](https://lartc.org/howto/lartc.rpdb.multiple-links.html#AEN267)

![image-20221031222237862](https://imagebed.yfycloud.site/2025/12/1ac5b183d2252ea76b04bd29d957b254.png)

1. 首先，在 main 路由表中添加到两个 ISP 网段的路由，这保证可以访问到两个 ISP 的网关

2. 接着，添加默认路由。
   - 可以之后再添加策略路由，使得某些 ip 走 IPS1，剩余走 IPS2

3. （接下来两步用于保证数据能够原路返回，不会出现来自 IPS1 的流量，从 IPS2 出去）

4. 然后，创建两个新的路由表 T1 和 T2，各自将对应的 ISP 设置为默认路由

5. 最后，添加路由策略。该规则根据包的源地址选择使用对应 ISP 的路由表（T1, T2）。
   - 这里，**重点在于需要原路返回的包，已经获得 src 地址了**？不需要原路返回的包，则根据之前的策略选择 ISP 出口后，设置 src 地址。

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

## Wiregaurd + L2 隧道组网

### L2 隧道优点 vs 缺点

[I really like wireguard, but one thing that bugs me is the fact that it's layer ... | Hacker News (ycombinator.com)](https://news.ycombinator.com/item?id=22467869)

In most scenarios, you want to avoid L2 tunnels to reduce complexity and/or performance issues.
The chain of thought typically goes like this:

- Remote networks are connected via L2 tunnel.
- **ARP requests are broadcasted over L2 tunnel to all connected networks, introducing scalability issues**
- Proxy ARP is introduced to cache ARP responses
- Proxy ARP may become out of date or not scale as the L2 domain grows.
- BGP is introduced to keep track of and broadcast all topology changes
- How do you mitigate issues caused if Proxy ARP fails?

**Most of these issues go away if you use IP tunnels instead of Ethernet because IP was designed to be routable.**

### 各种隧道对比

各种隧道对比：[An introduction to Linux virtual interfaces: Tunnels | Red Hat Developer](https://developers.redhat.com/blog/2019/05/17/an-introduction-to-linux-virtual-interfaces-tunnels#gue)

- ipip
- gre, gretap

GRE tunnels
![gre](https://imagebed.yfycloud.site/2025/12/3fc11414671a30af4bb89fa91ac922b3.png)

GRETAP
![](https://imagebed.yfycloud.site/2025/12/6bb7a6bd6c55bbdbe4acd778291cf29c.png)

一种协同使用多种隧道例子

- udp2raw：wg 基于 udp，可能被运营商 qos。使用 udp2raw 实现 udp in tcp
- wg：L3 隧道
- gre: 图中的是 tun，仍是三层隧道
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

## openwrt gre 配置

参考资料：

- openwrt gre 配置：[[OpenWrt Wiki] Tunneling interface protocols](https://openwrt.org/docs/guide-user/network/tunneling_interface_protocols#protocol_gretap_ethernet_gre_tunnel_over_ipv4)
- [[OpenWrt Wiki] Routing example: GRE](https://openwrt.org/docs/guide-user/network/routing/examples/routing_in_gre)
- GRE ip 包中 protocol number 为 47：[List of IP protocol numbers - Wikipedia](https://en.wikipedia.org/wiki/List_of_IP_protocol_numbers)

### 背景

背景：学校宿舍楼没有分配 PD，而实验楼分配了/64 的 PD。因此想通过 L2 隧道，将宿舍楼的接口桥接到实验楼路由器的 wan 口上，从而获得一个 PD 地址。之后利用该 PD 在 lan 上开启 ipv6 ra server，给 lan 分配 ipv6 地址。

思路：两台路由器 op1, op2 通过 wg 连接，基于 wg 接口 ip 建立 gretap 隧道。op1 将该 tap 桥接到 br-wan 上。op2 在该 tap 上开启 dhcpv6 client，申请一个 PD。

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

如果是 pve 的话，通常没有加载。需要手动 modprobe，并添加到`/etc/module`中

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

安装了 gre 后，luci 中创建接口时可能还是无法选择 gre，此时需要重启 network: `/etc/init.d/network restart`

### 配置

#### op1 和 op2 上都创建 gre1 接口

- protocal 选择 gretap over ipv4
- local 和 remote 地址填 wg 接口地址
- 创建成功后，ip a 可以看到多出一个 gre4t-gre1 的接口
![](https://imagebed.yfycloud.site/2025/12/8d14e145a5c53ff7f8301adf32cf0466.png)

如果使用 wan 口 ipv6 创建 gre tap，两端都需要添加 allow gre input 的防火墙规则。默认是没有 gre 类型的，在 custom 中输入 47 或则 gre 回车便会出现该类型。
![](https://imagebed.yfycloud.site/2025/12/274a0a0bb861b29d9c38a2775c0e996b.png)

#### op1 将 gre device 添加到 bridge

- 名字填@gre1（也可以直接写 gre4t-gre1）
![](https://imagebed.yfycloud.site/2025/12/63ccc811ce5bfceafd5b95afb4cfcccb.png)

#### op1 设置防火墙 wan forward

- 将 gre1 设置为 wan
- 防火墙中，设置**wan zone forward 为 accept**（默认为 reject）。**否则 gre1 设备上来包无法从 wan 转发出去**，从而无法访问互联网。
![](https://imagebed.yfycloud.site/2025/12/36961066107102239e346cec05679897.png)

![](https://imagebed.yfycloud.site/2025/12/d8d6e8002d15a81d3d2e9d4721edf4e5.png)

#### op2 设置 dhcpv6

在 gre1 tap 上启用 dhcpv6 client，openwrt 上该操作为创建一个 interface，协议选择 dhcpv6 client

- 该接口高级设置中可以勾选 source route，这样对于有多个 uplink，就能自动处理路由
  - 源地址为该 pd 的地址，走 tap 接口
  - 源地址为 wan 口 slaac 的地址，走原来的 wan 口
![](https://imagebed.yfycloud.site/2025/12/5306a881a9a6eb2dd4f77335e5d5b8c0.png)

## ubuntu gre 配置

- 先使用 wg0，建立 wiregaurd 连接
- 再使用 gretap 建立二层隧道
  - 接着 op 端在 gretap device 上创建 dhcp6 的 client（由于只需要 ipv6 PD，因此可以不设置 dhcpv4）
  - ubuntu 端将 gretap 和 br0(ustcnet bridge) 桥接
- 此时 op 已经可以获得 ipv6 PD 了
- lan interface 上勾线 ipv6 prefix，开启 ra server。之后 lan 内设备就可以获得 ipv6 地址了
- 此时 lan 内设备 ipv6 仍无法上网，**需要在 ubuntu 上开启 ipv6 forward**

```
sudo systemctl start wg-quick@op2-gre-wg0
sudo ip link add op2-gre1 type gretap  local 10.0.31.10 remote 10.0.31.2 ttl 255
sudo ip link set op2-gre1 up
sudo ip link set op2-gre1 master br0
```

## gre 不通，chatgpt 回复

我创建了一个 pve lxc 容器，分配的网络接口 eth0 对应 pve 的 vmbr0，容器内 eth0 接在 br-wan 上。然后我在 pve lxc 容器中创建了一个 gretap 设备，桥接到 br-wan 上，但是 gretap 上的 ipv6 rs 报文无法通过 br-wan 发送到 eth0，从而无法正确发送到 pve 外的 vmbr0，我该怎么做

ChatGPT

您的网络拓扑中包含了多层虚拟化网络（PVE 容器内的 GRETAP 设备、LXC 容器和 PVE 宿主机）。为了确保 GRETAP 设备的 IPv6 RS 报文能够正确传递到 PVE 宿主机的 vmbr0 以外的网络，您需要进行一些网络配置。以下是可能的解决方法：

1. **检查 IPv6 Forwarding 设置**：首先，确保 PVE 宿主机上启用了 IPv6 转发功能。可以使用以下命令检查：
    `sysctl net.ipv6.conf.all.forwarding`
    如果返回值为 1，表示已启用 IPv6 转发。如果返回值为 0，可以使用以下命令启用它：
    `sysctl -w net.ipv6.conf.all.forwarding=1`
    为了使此更改持久化，您可以将它添加到 `/etc/sysctl.conf` 文件中。

1. **LXC 容器网络配置**：确保 LXC 容器内的 GRETAP 设备和 br-wan 接口正确配置。检查 GRETAP 设备的 IPv6 地址、子网和路由是否正确设置。确保 GRETAP 设备能够正确路由 IPv6 流量。

1. **容器内防火墙规则**：如果 LXC 容器内有防火墙规则，确保它们不会阻止 IPv6 流量从 GRETAP 设备传递到 br-wan 接口。您可能需要在容器内的防火墙规则中添加允许 IPv6 流量通过的规则。

1. **PVE 宿主机网络桥配置**：确保 PVE 宿主机上的网络桥（vmbr0 和 br-wan）正确配置，以允许 IPv6 流量正确传递。检查它们的 IPv6 地址、子网和路由设置。

1. **LXC 容器间隔离设置**：请确保在 PVE 宿主机的网络配置中，LXC 容器之间的网络隔离设置不会阻止 IPv6 流量的传递。这可能需要调整安全组或网络隔离规则。

1. **MTU 设置**：在多层虚拟化网络中，MTU（最大传输单元）问题可能会导致通信问题。确保各个网络设备的 MTU 设置正确，并且不会导致分段或丢失数据包。

1. **网络抓包**：如果问题仍然存在，您可以在不同的网络设备上使用抓包工具（如 Wireshark 或 tcpdump）来捕获 IPv6 流量，以便更详细地分析问题并找出故障的位置。

请根据上述建议逐步检查和调整您的网络配置，以解决 IPv6 RS 报文无法正确传递的问题。确保在更改网络配置之前备份重要数据，以防意外发生。

上面提到的：
> 确保它们不会阻止 IPv6 流量从 GRETAP 设备传递到 br-wan 接口。

真的让我找到了问题！

## 相关小实验

### 绕路返回：wan 口进入，wg 接口返回

网络情况

- op2（发起 ping）
  - eth0: 114.214.173.252
- king3399（响应 ping）
  - eth0: 222.195.90.107
  - wg0: endpoint op1, default route
- op1（路由中转）
  - br-wan: 114.214.236.72

icmp request
op2(eth0) -> king(eth0)

- route 走学校

icmp reply
king(eth0) -> op2(eth0)

- route 通过 wg0，发送给 op1
- op1 再转发，从 br-wan 出去，到达 op2

op1 收到 king 的 icmp reply 再转发，实际有两个障碍

1. op1 将 wg0 收到的 src 地址为 op2(eth0) 的包丢弃，因为不在 allow ip 中。解决办法：allow ip 设置为 0.0.0.0，关闭自动添加路由
2. op1 wg0 收到包后，却发现并没有从 wan 口发送出去

以下是对问题 2 的探究

首先 king 上符合预期，从 eth0 收到 icmp request，从 wg0 返回 icmp reply

```
tcpdump -ni any icmp and host 222.195.90.107

22:08:20.292237 eth0  In  IP 114.214.173.252 > 222.195.90.107: ICMP echo request, id 65124, seq 5, length 64
22:08:20.292430 wg0   Out IP 222.195.90.107 > 114.214.173.252: ICMP echo reply, id 65124, seq 5, length 64
```

问题出现在 op1，可以看到 wg0 收到了包，但是却没有任何 output

```
root@op1 ➜  ~ tcpdump -ni any icmp and host 114.214.173.252

22:09:22.298394 wg0   In  IP 222.195.90.107 > 114.214.173.252: ICMP echo reply, id 65124, seq 67, length 64
22:09:23.298654 wg0   In  IP 222.195.90.107 > 114.214.173.252: ICMP echo reply, id 65124, seq 68, length 64
```

研究后发现使用 nft trace 可以追踪包在防火墙中的处理顺序

- trace id 标识一个包
- 可以看到依次经过以下 chain 处理，结尾的 verdict（判决）表示处理结果
  - raw_prerouting
  - mangle_prerouting
  - prerouting
  - mangle_forward
  - forward
    - 在这里匹配`meta nfproto ipv4 oifname { "br-wan", "gre4t-gre1" } ct state invalid counter drop`规则，然后被 drop 了

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

通过 nft 修改掉该 drop，发现就能 ping 通了
op1 上 tcpdump 可以看到正确从 br-wan 转发

```
23:38:13.018068 wg0   In  IP 222.195.90.107 > 114.214.173.252: ICMP echo reply, id 14312, seq 2631, length 64
23:38:13.018089 br-wan Out IP 222.195.90.107 > 114.214.173.252: ICMP echo reply, id 14312, seq 2631, length 64
```

op2 和 king 上都能看到 conntrack 信息

```
root@op2 ➜  ~ conntrack -L -p icmp -d 222.195.90.107
icmp     1 29 src=114.214.173.252 dst=222.195.90.107 type=8 code=0 id=31588 packets=112 bytes=9408 src=222.195.90.107 dst=114.214.173.252 type=0 code=0 id=31588 packets=104 bytes=8736 mark=0 use=1
conntrack v1.4.8 (conntrack-tools): 1 flow entries have been shown.
```

不过 op1 上没有（难道转发不算？）

```
root@op1 ➜  ~ conntrack -L -p icmp |grep 222.195.90.107
conntrack v1.4.8 (conntrack-tools): 151 flow entries have been shown.
```

但是该规则到底是什么意思呢？ct invalid 为什么会匹配？

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

fw4 规则注释中提到的 Prevent NAT leakage，搜索
[LuCI option to enable/disable "NAT Leakage Prevention" - Installing and Using OpenWrt - OpenWrt Forum](https://forum.openwrt.org/t/luci-option-to-enable-disable-nat-leakage-prevention/49536/12)
> This rule is only generated for firewall zones with masquerading
> how in blazes would non-NATted/martian packets leak to the WAN?

[NAT leakage on 22.03 [fw4] - Installing and Using OpenWrt - OpenWrt Forum](https://forum.openwrt.org/t/nat-leakage-on-22-03-fw4/140790)
知道了有`masq_allow_invalid`这么一个选项[[OpenWrt Wiki] Firewall configuration /etc/config/firewall](https://openwrt.org/docs/guide-user/firewall/firewall_configuration)

|   |   |   |   |   |
|---|---|---|---|---|
|`masq_allow_invalid`|boolean|no|`0`|Do not add `DROP INVALID` rules, if masquerading is used. The `DROP` rules are supposed to prevent NAT leakage (see [commit in firewall3](https://git.lede-project.org/?p=project/firewall3.git;a=commit;h=e751cde8954a09ea32f67a8bf7974b4dc1395f2e "https://git.lede-project.org/?p=project/firewall3.git;a=commit;h=e751cde8954a09ea32f67a8bf7974b4dc1395f2e")).|

GUI 中解释：
> Do not install extra rules to reject forwarded traffic with conntrack state *invalid*. This may be required for complex asymmetric route setups.

[NAT: Masquerade can leak private IP, why&how? - MikroTik](https://forum.mikrotik.com/viewtopic.php?t=177210)

- 大概就是接口 down 再 up，有一些包没有正确的 ct 状态，不会经过 masq。
