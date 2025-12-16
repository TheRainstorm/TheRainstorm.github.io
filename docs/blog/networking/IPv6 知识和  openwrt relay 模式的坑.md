---
title: IPv6 知识和  openwrt relay 模式的坑
date: 2023-08-02 14:34:00
tags:
  - ipv6
  - slaac
  - dhcpv6
  - PD
  - relay
  - NDP
categories:
  - 博客 & 网络
---
ipv6 协议详细介绍了 ipv6 几种获得地址模式的区别：SLAAC, 无状态 DHCPv6 和 有状态 DHCPv6

另外介绍了下 openwrt 使用 relay 模式导致需要 ping wan 口才能通的原因

<!-- more -->
# ipv6 协议

## 参考资料

ipv6地址和协议：[Network Layer: IPv6 addressing and IPv6 protocol - ICTShore.com](https://www.ictshore.com/free-ccna-course/network-layer-ipv6-addressing/)

ipv6系列教学

- [IPv6 from scratch - the very basics of IPv6 explained](https://youtu.be/oItwDXraK1M)
- [IPv6 explained - SLAAC and DHCPv6 (IPv6 from scratch part 2)](https://www.youtube.com/watch?v=jlG_nrCOmJc&t=1s)
- openwrt ipv6设置：有PD情况，relay，VPN tunnel来获得PD：[IPv6 with OpenWrt - YouTube](https://www.youtube.com/watch?v=LJPXz8eA3b8)
- 对应ipv6 cheat sheet：[ipv6 cheat sheet](https://github.com/onemarcfifty/cheat-sheets/blob/main/networking/ipv6.md)

NDP

- [How to: IPv6 Neighbor Discovery | APNIC Blog](https://blog.apnic.net/2019/10/18/how-to-ipv6-neighbor-discovery/)
  - NS, NA用于实现arp
  - NS用于实现DAD(Duplicate Address Detection）

## ipv6 address

- 首先ipv6地址有不同的scope
- 在每个scope下为了实现一些特殊功能，需要使用不同的地址。比如link-local scope下实现广播。

**GLOBAL** - Everything (i.e. the whole internet),  
**UNIQUE LOCAL** - Everything in our LAN (behind the internet gateway),  
**LINK LOCAL** - Everything within the same collision domain that will not be routed (i.e. attached to the same switch).

|Range|Purpose|
|---|---|
|::1/128|Loopback Address (localhost)|
|::/128|Unspecified Address|
|2000::/3|GLOBAL Unicast (Internet)|
|fc00::/7|Unique-Local (LAN)|
|fe80::/10|Link-Local Unicast (Same switch)|

- **You should always use the smallest possible scope for communication.**  
- A host can have **multiple** addresses in different scopes, even on the same interface.

128 = 64(`Network` portion) + 64(`Host`)
64(network portion) = 48(`routing prefix`) + 16(`subnet id`)

multicast addresses  in in the link-local scope

|Range|Purpose|
|---|---|
|ff02::1|All Nodes within the network segment|
|ff02::2|All Routers within the network segment|
|ff02::fb|mDNSv6|
|ff02::1:2|All DHCP Servers and Agents|
|ff02::101|All NTP Servers|

## IPv6 addressing methods

ipv4

- unicast, multicast and broadcast
ipv6
- unicast, multicast, _link-local_ and _anycast_

### Link-local

An **IPv6 link-local address** is an address that is valid only _within the broadcast domain_ (it is local to it). This address is not routable, meaning that no router can have a route to it because it must be directly connected, and can be compared at a Layer 2 address, because it behaves the same way.

### Multicast

ipv6删除了广播地址，而是用多播进行替代。

a multicast address is an address “subscribed” by multiple nodes: these nodes will be listening to that address. All multicast addresses, in IPv6, belong to the `ff00::/8` prefix.

特殊的广播地址：

|Address|Scope|Description|
|---|---|---|
|`ff02::1`|Link|All nodes on the link. It effectively replaces a **broadcast** address.|
|`ff02::2`|Link|All routers on the link.|

### Anycast

将一个unicast地址分配给多个设备。这样
To be more specific, it is actually a _unicast address assigned to multiple devices_ around the world, and instead of identifying the device itself, it identifies the **services** it offers.

This allows other devices to point to that services and reach the nearest device offering that service, without actually knowing what is the nearest device.

## Neighbor Discovery & Router Discovery

NDP代替ipv4的ARP协议。NDP基于ICMPv6
there is the _Address Resolution Protocol (ARP)_, which is used to map IPv4 addresses to MAC addresses. With IPv6, we can completely get rid of this protocol using a more efficient one, the **Neighbor Discovery Protocol (NDP)**. NDP relies on the **Internet Control Message Protocol version 6 (ICMPv6)** packet to do its job.

icmp6报文格式
![icmp6](https://www.ictshore.com/wp-content/uploads/2016/12/1015-09-ICMPv6.png)

[RFC 5175: IPv6 Router Advertisement Flags Option (rfc-editor.org)](https://www.rfc-editor.org/rfc/rfc5175.html)
另外在**option**中有A flag和L flag（更具体是prefix info option）

- [The IPv6 Prefix Information Option or Fun with the L Flag (infoblox.com)](https://blogs.infoblox.com/ipv6-coe/the-ipv6-prefix-information-option-or-fun-with-the-l-flag/)
- [router - IPv6 RA flags and various combinations - Network Engineering Stack Exchange](https://networkengineering.stackexchange.com/questions/35373/ipv6-ra-flags-and-various-combinations)

```bash
root@op1 ➜  ~ tcpdump -vvv -n -ttt -i eth1 "icmp6 and (ip6[40] == 134 or ip6[40] == 133)"
tcpdump: listening on eth1, link-type EN10MB (Ethernet), capture size 262144 bytes
 00:00:00.000000 IP6 (class 0xe0, hlim 255, next-header ICMPv6 (58) payload length: 64) fe80::8261:6cff:fef5:4e01 > ff02::1: [icmp6 sum ok] ICMP6, router advertisement, length 64
        hop limit 64, Flags [managed, other stateful], pref medium, router lifetime 1800s, reachable time 0ms, retrans timer 0ms
          source link-address option (1), length 8 (1): 80:61:6c:f5:4e:01
            0x0000:  8061 6cf5 4e01
          mtu option (5), length 8 (1):  1500
            0x0000:  0000 0000 05dc
          prefix info option (3), length 32 (4): 2001:da8:d800:336::/64, Flags [onlink, auto], valid time 2592000s, pref. time 604800s
            0x0000:  40c0 0027 8d00 0009 3a80 0000 0000 2001
            0x0010:  0da8 d800 0336 0000 0000 0000 0000
```

- NS, NA
![](https://www.ictshore.com/wp-content/uploads/2016/12/1015-10-Neighbor_discovery.png)

- RS, RA
![](https://www.ictshore.com/wp-content/uploads/2016/12/1015-11-Router_solicitation.png)

## SLAAC, stateless DHCPv6, stateful

### Stateless Auto Address Configuration (SLAAC)

- When a device comes online, it sends a _Router Solicitation_ message. He’s basically asking “Are there some routers out there?”
- If we have a router on the same network, that router will reply with a **Router Advertisement** message. contain information:
  - Who is the default gateway (the link-local address of the router itself)
  - What is the global unicast prefix (for example, `2001:DB8:ACAD:10::/64`)
- the client is going to create a new global unicast address using the **EUI-64** technique

然而无法设置其它信息，如DNS

### Stateless DHCPv6

- Router Advertisement has a flag called `other-config` set to 1.
- client use SLAAC to craft its own IPv6 address
- After the SLAAC process succeeds, the client will craft a **DHCPv6 request** and send it through the network.

叫做stateless，因为dhcpv6 server不管理任何client的lease。而只是发送额外信息如DNS, domain name。

### Stateful DHCPv6

- Advertisement in reply contains the `managed-config` set to 1.
- The client will then generate a DHCPv6 request to get both addressing and extra information

## 不同OS ipv6地址分配方式

[IPv6 Address Allocation Is Operating System-Specific « ipSpace.net blog](https://blog.ipspace.net/2016/01/ipv6-address-allocation-is-operating.html)

三种不同地址分配方式

- 静态设置
- DHCPv6，在RA报文中，M(Managed configuration) flag设置，表示client可以发起DHCPv6来获得ipv6地址
- SLAAC，RA报文中，A(auto configuration) flag设置，设备通过prefix和自己MAC地址（或者还有随机数）生成ipv6地址。

不通操作系统有不通策略

- android不支持DHCPv6，无论M是否设置，也不会发起DHCP request。
- windows尽可能获得多的地址。即使手动设置了静态地址，也会获得DHCP地址和SLAAC地址。
  - 要想只有一个地址，可以将M flag关闭，这样windows就只有SLAAC地址。而如果把A关闭，那么安卓设备就无法使用了。
Other operating systems grab all they can: Windows will happily ask for a DHCPv6-assigned address whenever it receives an RA message with the M flag set regardless of whether it already has a static IPv6 address, and will add an autoconfigured address to the mix if the prefixes in the RA messages have the A flag set regardless of whether it already got static and/or DHCPv6-assigned addresses.

## DHCPv6-PD

[什么是DHCPv6-PD – 邹坤个人博客 (z0ukun.com)](https://blog.z0ukun.com/?p=3676)

DHCPv6-PD是DHCPv6的一个扩展功能。不同于DHCPv6用于申请ipv6地址，DHCPv6用于申请一个subnet地址。一般ISP边缘路由器(provider edge)是dhcpv6-pd server。而用户的直连路由器是dhcpv6-pd client。

用户路由器获得一个前缀后，可以自己再通过SLAAC配置下面的设备。

> 前面我们介绍的都是IPv6环境下的地址自动配置技术，其地址配置模式采用的是**“客户机-服务器”或“客户机-中继代理-服务器”**模式，这也是常见的地址配置模式，服务器直接面对客户主机。在这种模式下，当客户主机段越来越多时，地址分配及管理上就容易发生凌乱，特别是对于实施了层次化网络环境的运营商，网络核心如果直接面对用户主机的地址分配，一方面与层次化地址分配原则相悖，另一方面也会增加地址管理和服务器的负担。正因为如此，RFC3633中定义了一种DHCPv6-PD模式，专门用于自动分配前缀。

### 协议过程

1．PD客户端向PD服务器发送DHCPv6请求报文，此报文携带IA_PD选项，表明自己需要申请IPv6前缀。
2．PD服务器收到请求报文后，从自己的前缀列表池中取出可用的前缀，附带在IA_PD选项中，回复给PD客户端。
3．前缀分配到期后，PD客户端重新向PD服务器发送DHCPv6请求报文，请求更新前缀。
4．PD服务器重新为PD客户端分配前缀（在原有前缀未被占用的情况下，一般就是续租）。
5．PD客户端需要释放前缀时，向PD服务器发送快速请求报文，以释放前缀。
6．PD服务器接收快速请求报文后，回收前缀，并对PD客户端的快速请求报文进行回应。

# relay下设备需要ping下路由器才能上网

## 现象

lxd容器接入br1，获得了全局ipv6地址，但是确无法访问外网

#### 正常时

- 刚开始op2 ip neigh没有容器地址
- 容器ping 6.ipw.cn时，op2 ip neigh出现容器地址。并且可以ping通
  - 约40s从REACHABLE变为STALE。约90s neigh条目消失。

#### 不正常时

*在op2上ip -6 -statistics neigh flush dev eth1(lan接口)就可以复现_

- 容器无法ping通
- 此时op2上有一条错误的neigh项，显示lxd容器位于路由器wan口(eth0)。状态为INCOMPLETE或FAILED
  - 如果ip6 ro get lxd地址，也会发现会匹配到wan出口

```
root@op2 ➜  ~ ip6 neigh |grep 34a0
2001:da8:d800:611:216:3eff:fe75:34a0 dev eth0  INCOMPLETE
fe80::216:3eff:fe75:34a0 dev eth1 lladdr 00:16:3e:75:34:a0 STALE
```

- 此时tcpdump op2 wan口，可以抓到op2 NS lxd容器的包。但是监控lan口则抓不到。

```
root@op2 ➜  ~ tcpdump -i eth0 icmp6 |grep 34a0
tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
listening on eth0, link-type EN10MB (Ethernet), capture size 262144 bytes
17:45:11.488397 IP6 2001:da8:d800:611:216:3eff:feb9:4ff6 > ff02::1:ff75:34a0: ICMP6, neighbor solicitation, who has 2001:da8:d800:611:216:3eff:fe75:34a0, length 32
17:45:12.497482 IP6 2001:da8:d800:611:216:3eff:feb9:4ff6 > ff02::1:ff75:34a0: ICMP6, neighbor solicitation, who has 2001:da8:d800:611:216:3eff:fe75:34a0, length 32
```

lan口只能抓到fe80的NS消息

```
#tianyi tcpdump
17:42:14.961479 IP6 fe80::216:3eff:fe3d:6fdc > fe80::216:3eff:fe75:34a0: ICMP6, neighbor solicitation, who has fe80::216:3eff:fe75:34a0, length 32
17:42:14.961754 IP6 fe80::216:3eff:fe75:34a0 > fe80::216:3eff:fe3d:6fdc: ICMP6, neighbor advertisement, tgt is fe80::216:3eff:fe75:34a0, length 24
```

## 其它人的类似问题

- [relay mode does not work · Issue #37 · openwrt/odhcpd (github.com)](https://github.com/openwrt/odhcpd/issues/37)
- [NDP relay not working because NDP proxy entries are not added · Issue #92 · openwrt/odhcpd (github.com)](https://github.com/openwrt/odhcpd/issues/92)

遇到完全一样现象的
![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20230713185648.png)
但是设置ndproxy_slave后仍然不行

## 抓包

### 需要在其它地方ping LAN内机器，LAN机器才能上网

windows无法上网
路由器在wan口发送NS请求

```
root@op2 ➜  ~ tcpdump -vvvv -ttt -i eth0 "icmp6 and (ip6[40] == 136 or ip6[40] == 135)" |grep b006
tcpdump: listening on eth0, link-type EN10MB (Ethernet), capture size 262144 bytes
 00:00:00.418749 IP6 (hlim 255, next-header ICMPv6 (58) payload length: 32) 2001:da8:d800:611:6c4b:aaff:fe73:6e8c > ff02::1:ff6f:b006: [icmp6 sum ok] ICMP6, neighbor solicitation, length 32, who has 2001:da8:d800:611:5168:422:546f:b006
 00:00:00.641522 IP6 (hlim 255, next-header ICMPv6 (58) payload length: 32) 2001:da8:d800:611:6c4b:aaff:fe73:6e8c > ff02::1:ff6f:b006: [icmp6 sum ok] ICMP6, neighbor solicitation, length 32, who has 2001:da8:d800:611:5168:422:546f:b006
 00:00:00.259773 IP6 (hlim 255, next-header ICMPv6 (58) payload length: 32) 2001:da8:d800:611:6c4b:aaff:fe73:6e8c > ff02::1:ff6f:b006: [icmp6 sum ok] ICMP6, neighbor solicitation, length 32, who has 2001:da8:d800:611:5168:422:546f:b006
 00:00:00.133900 IP6 (hlim 255, next-header ICMPv6 (58) payload length: 32) 2001:da8:d800:611:6c4b:aaff:fe73:6e8c > ff02::1:ff6f:b006: [icmp6 sum ok] ICMP6, neighbor solicitation, length 32, who has 2001:da8:d800:611:5168:422:546f:b006
```

win ping ipw，路由器确实将icmp转发出去（此后win ip变为8295）。pve上抓bridge，每次能看到两条

```
root@tianyi ➜  ~ tcpdump -tttt -i vmbr1 "icmp6 and (ip6[40] == 128)"
tcpdump: verbose output suppressed, use -v[v]... for full protocol decode
listening on vmbr1, link-type EN10MB (Ethernet), snapshot length 262144 bytes
2023-07-19 17:07:45.544300 IP6 2001:da8:d800:611:fc9b:d4ed:c9c8:8295 > 2402:4e00:1013:e500:0:9671:f018:4947: ICMP6, echo request, id 1, seq 622, length 40
2023-07-19 17:07:45.544339 IP6 2001:da8:d800:611:fc9b:d4ed:c9c8:8295 > 2402:4e00:1013:e500:0:9671:f018:4947: ICMP6, echo request, id 1, seq 622, length 40
2023-07-19 17:07:50.540583 IP6 2001:da8:d800:611:fc9b:d4ed:c9c8:8295 > 2402:4e00:1013:e500:0:9671:f018:4947: ICMP6, echo request, id 1, seq 623, length 40
2023-07-19 17:07:50.540620 IP6 2001:da8:d800:611:fc9b:d4ed:c9c8:8295 > 2402:4e00:1013:e500:0:9671:f018:4947: ICMP6, echo request, id 1, seq 623, length 40
2023-07-19 17:07:55.545758 IP6 2001:da8:d800:611:fc9b:d4ed:c9c8:8295 > 2402:4e00:1013:e500:0:9671:f018:4947: ICMP6, echo request, id 1, seq 624, length 40
2023-07-19 17:07:55.545797 IP6 2001:da8:d800:611:fc9b:d4ed:c9c8:8295 > 2402:4e00:1013:e500:0:9671:f018:4947: ICMP6, echo request, id 1, seq 624, length 40
2023-07-19 17:08:00.553304 IP6 2001:da8:d800:611:fc9b:d4ed:c9c8:8295 > 2402:4e00:1013:e500:0:9671:f018:4947: ICMP6, echo request, id 1, seq 625, length 40
```

在另一台机器上访问win ip6，mtr，然后就通了

- 中间路由器wan口对win发起了icmp echo，不知为什么，是mtr的原因？
  - **这里和后面openwrt NDP proxy的行为对上了！！！**。WAN上接收到学校NS A的请求，会在LAN上发icmp-echo请求给A。可以看到时间是对上的。
- ustc域名那个是ryzen的ip

```
root@tianyi ➜  ~ tcpdump -tttt -i vmbr1 "icmp6 and (ip6[40] == 128 or ip6[40]==129)"
tcpdump: verbose output suppressed, use -v[v]... for full protocol decode
listening on vmbr1, link-type EN10MB (Ethernet), snapshot length 262144 bytes

2023-07-19 17:11:45.547363 IP6 2001:da8:d800:611:fc9b:d4ed:c9c8:8295 > 2402:4e00:1013:e500:0:9671:f018:4947: ICMP6, echo request, id 1, seq 670, length 40
2023-07-19 17:11:45.547401 IP6 2001:da8:d800:611:fc9b:d4ed:c9c8:8295 > 2402:4e00:1013:e500:0:9671:f018:4947: ICMP6, echo request, id 1, seq 670, length 40
2023-07-19 17:11:50.459330 IP6 2001:da8:d800:611:6c4b:aaff:fe73:6e8c > 2001:da8:d800:611:fc9b:d4ed:c9c8:8295: ICMP6, echo request, id 0, seq 0, length 8
2023-07-19 17:11:50.543230 IP6 2001:da8:d800:611:fc9b:d4ed:c9c8:8295 > 2402:4e00:1013:e500:0:9671:f018:4947: ICMP6, echo request, id 1, seq 671, length 40
2023-07-19 17:11:50.543270 IP6 2001:da8:d800:611:fc9b:d4ed:c9c8:8295 > 2402:4e00:1013:e500:0:9671:f018:4947: ICMP6, echo request, id 1, seq 671, length 40
2023-07-19 17:11:50.882113 IP6 2001:da8:d800:611:fc9b:d4ed:c9c8:8295 > 2001:da8:d800:611:6c4b:aaff:fe73:6e8c: ICMP6, echo reply, id 0, seq 0, length 8
2023-07-19 17:11:51.263499 IP6 2001:da8:d800:611:6c4b:aaff:fe73:6e8c > 2001:da8:d800:611:fc9b:d4ed:c9c8:8295: ICMP6, echo request, id 0, seq 0, length 8
2023-07-19 17:11:51.264817 IP6 2001:da8:d800:611:fc9b:d4ed:c9c8:8295 > 2001:da8:d800:611:6c4b:aaff:fe73:6e8c: ICMP6, echo reply, id 0, seq 0, length 8
2023-07-19 17:11:51.908027 IP6 ustc.edu.cn > 2001:da8:d800:611:fc9b:d4ed:c9c8:8295: ICMP6, echo request, id 23486, seq 33002, length 24
2023-07-19 17:11:51.930865 IP6 2001:da8:d800:611:fc9b:d4ed:c9c8:8295 > ustc.edu.cn: ICMP6, echo reply, id 23486, seq 33021, length 24
2023-07-19 17:11:51.996148 IP6 ustc.edu.cn > 2001:da8:d800:611:fc9b:d4ed:c9c8:8295: ICMP6, echo request, id 23486, seq 33022, length 24
2023-07-19 17:11:51.997453 IP6 2001:da8:d800:611:fc9b:d4ed:c9c8:8295 > ustc.edu.cn: ICMP6, echo reply, id 23486, seq 33022, length 24
2023-07-19 17:11:52.425085 IP6 ustc.edu.cn > 2001:da8:d800:611:fc9b:d4ed:c9c8:8295: ICMP6, echo request, id 23486, seq 33025, length 24
2023-07-19 17:11:55.544792 IP6 2001:da8:d800:611:fc9b:d4ed:c9c8:8295 > 2402:4e00:1013:e500:0:9671:f018:4947: ICMP6, echo request, id 1, seq 672, length 40
2023-07-19 17:11:55.592522 IP6 2402:4e00:1013:e500:0:9671:f018:4947 > 2001:da8:d800:611:fc9b:d4ed:c9c8:8295: ICMP6, echo reply, id 1, seq 672, length 40
2023-07-19 17:11:55.592560 IP6 2402:4e00:1013:e500:0:9671:f018:4947 > 2001:da8:d800:611:fc9b:d4ed:c9c8:8295: ICMP6, echo reply, id 1, seq 672, length 40
2023-07-19 17:11:56.550626 IP6 2001:da8:d800:611:fc9b:d4ed:c9c8:8295 > 2402:4e00:1013:e500:0:9671:f018:4947: ICMP6, echo request, id 1, seq 673, length 40
2023-07-19 17:11:56.598434 IP6 2402:4e00:1013:e500:0:9671:f018:4947 > 2001:da8:d800:611:fc9b:d4ed:c9c8:8295: ICMP6, echo reply, id 1, seq 673, length 40
```

期间软路由上终于抓到school对win公网ip6发起NS请求

- 比较神奇的是op对其进行了回应

```
2023-07-19 17:11:50.226090 IP6 2001:da8:d800:611::1 > ff02::1:ffc8:8295: ICMP6, neighbor solicitation, who has 2001:da8:d800:611:fc9b:d4ed:c9c8:8295, length 32
2023-07-19 17:11:51.263290 IP6 2001:da8:d800:611::1 > ff02::1:ffc8:8295: ICMP6, neighbor solicitation, who has 2001:da8:d800:611:fc9b:d4ed:c9c8:8295, length 32
2023-07-19 17:11:51.904962 IP6 2001:da8:d800:611:6c4b:aaff:fe73:6e8c > 2001:da8:d800:611::1: ICMP6, neighbor advertisement, tgt is 2001:da8:d800:611:fc9b:d4ed:c9c8:8295, length 32
```

## 未解之谜

折腾了很久，还是没能解决。因此总结下目前遇到的状况。迟早有一天能够理解这里的问题。

- 现在有两种情况，客户端均能获得ipv6，但是就是不通网
  - 第一种情况，客户端ping 路由器wan口，就可以上网了。
  - 第二种情况，ping wan口还是不行，此时路由器是可以ping客户端的。也将echo从wan口路由出去了，但是收不到reply。此时如果在外网ping一下客户端的ipv6地址（确实能ping通），客户端上网就正常了。

对应第一种情况的问题：

- 路由器为什么ping不通lan下windows的ip6地址（临时的随机地址和静态的）
  - 为什么路由器上ping lan内win11ipv6地址时，向wan口发送NS报文，却不向lan口发
    - **路由器在arp一个ipv6地址时，如何选择多播的接口呢**？照理来说应该是link local scope的接口。但是这里两个接口应该都是link-local的？但是这是不是和wan和lan的隔离性冲突呢？

对于第二种情况的问题
openwrt NDP-Proxy relay模式的说明：
>Forward NDP NS and NA messages between the designated master interface and downstream interfaces.

- windows网卡启动并配置完一个静态地址和一个随机地址后，会发送NA报文，广播给所有节点。**那么路由器有将其转发给wan口吗？![win10-%E8%AE%BE%E7%BD%AEslaac%20ip%E5%92%8C%E9%9A%8F%E6%9C%BAip%E5%90%8E%EF%BC%8C%E4%BC%9A%E5%8F%91%E4%B8%80%E6%9D%A1NS%E6%8A%A5%E6%96%87.jpg](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/win10-%E8%AE%BE%E7%BD%AEslaac%20ip%E5%92%8C%E9%9A%8F%E6%9C%BAip%E5%90%8E%EF%BC%8C%E4%BC%9A%E5%8F%91%E4%B8%80%E6%9D%A1NS%E6%8A%A5%E6%96%87.jpg)**
- 如果没有的话，是不是学校的路由器就不知道win11的存在，在转发echo请求时，发现ipv6地址没有记录，就直接丢掉了？（ipv4寝室图书馆之类的公共场所上游有 BRAS，必须触发认证才会把 v4 地址路由过来，这个触发动作就是 DHCP）

RA service relay模式：
> Forward RA messages received on the designated master interface to downstream interfaces

win上抓包发现.路由器返回的RA报文中flag设置了proxy。

tcpdump -tttt -n -i eth0 icmp6 -w eth0.pcap
tcpdump -tttt -n -i eth1 icmp6 -w eth1.pcap

wireshark filter

```
ipv6.addr!=2001:da8:d800:611::1


```

## 未解之谜的解开

[odhcpd 中继模式原理、局限以及解决方案 | Silent Blog (icpz.dev)](https://blog.icpz.dev/articles/notes/odhcpd-relay-mode-discuss/)
[OpenWRT IPv6 中继模式 - Zero's Blog (sourceforge.io)](https://l2dy.sourceforge.io/2021/05/11/openwrt-ipv6-relay.html)

### 中继行为

RS, RA的中继我自己也发现了，比较好理解
>
> 1. 从 slave interface 收到 RS 消息，odhcpd 会修改其源 MAC 地址为 master interface 再将其从 master interface 转发出去；
> 2. 从 master interface 收到的 RA 消息，odhcpd 会修改其中源 MAC 地址为 slave interface 再将其从 slave interface 转发出去；
> 3. 从 slave 收到的 RA 以及从 master 收到的 RS 消息会被忽略。

NS，NA的中继则比较trick
>对于 NDP 中继则不区分 master/slave 身份，以下仅以 M，S 两个 interface 做举例：
>
>1. 从 M 收到 NS 消息，odhcpd 会在 S 发送 icmp-echo 消息来让内核在 S interface 触发目的地址的 NDP 过程，若成功在 S 所在的链路发现了目的地址，则在 M 回复相应的 NA 消息，反之亦然；
>2. 在上述步骤中成功在 M/S 链路被发现的节点地址会被加入路由表，以方便后续通信的路由策略。

1. LAN 侧客户端 A （`2001:da8:abc:def::A/64`）发起了对全局路由地址（如 ipv6.google.com）的 echo-request 请求，该 IPv6 分组会被正常路由到 Google 的服务器；
2. 服务器 echo-reply 的分组到达 WAN 口的**上游**，此时上游会在各个节点端口广播目标是 A 地址的 NS 消息，当路由器的 WAN 收到该 NS 时，会按照前文中 NDP 中继的行为进行中继；
3. odhcpd 成功让内核在 LAN 侧发现了 A，从而在 WAN 侧回复了 NA 请求，并在路由表添加了 A 地址在 LAN 侧的表项；
4. WAN 口的**上游**收到了来自 odhcpd 的 NA 消息从而更新了 A 节点的邻居信息，并将来自服务器的 echo-reply 分组发送到 WAN 口；
5. WAN 口根据步骤 3 中建立的路由表项将发往 A 的分组路由到 LAN 侧并交付。

现象

- win11 ping op1，发现根本收不到echo request，也就是WAN上游根本没有对其转发。这里是1发生了问题
  - 其实问题在于win11获得ip地址后，上游没收到任何消息。
  - 上游有BRAS，ipv4需要dhcp触发，才会进行路由。ipv6看来也有类似行为，可能触发条件就是NS？
  - 发现上游好像在src ip地址没有触发认证前，是不会进行转发的。但是如果从其它地方ping一下该ip，则上游确实会尝试转发该包，并对WAN发送NS。
    - 但是并不是对所有ip都有这样的效果，我启用fake pd后，dhcp分配的短的地址就没用。上游根本不路由这个ip。
- pve ping op1，发现op1收到了request也reply了，但是pve收不到reply。
  - 这是由于2，上游没有发NS而是直接将reply发送给了WAN，没有触发odhcpd的NDP中继过程，因此op2不知道pve位于LAN。而根据现有路由表进行转发时，会从WAN发送NS来获得pve mac地址，因而因收不到NA而超时。
  - 具体过程类似
    1. 目的地是 LAN 侧客户端 A 的 IPv6 分组直接到达 WAN 口；
    2. 路由器内核根据现有路由表进行转发，发现该分组属于 WAN 口的 /64 子网，所以在 WAN 口发送 NS 寻找 A 的 MAC 地址；

解决

- 对于上游不NS，直接转发reply到wan，这种情况只需要设置路由表，添加prefix到lan接口的路由即可
- 对于上游不触发路由，需要其它设备ping后，才路由的情况。

上游到底怎样才会触发对包的处理啊，win的临时ipv6地址可以（每次重启网卡都会变化），但是lxc容器的slaac反而不行了？以下时两个设备网卡启动时，wan口的icmp6包
win11的
![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20230720033505.png)

lxc的
![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20230720033559.png)

不知道什么时候好的，把NDP proxy slave关掉lxc突然就直接能访问外网了

### 解决

> **注意**，该方法依赖 `owipcalc` 包来计算子网地址： `opkg install owipcalc` 。  
我们可以手动在 WAN 口获得 IPv6 地址后添加一条路由表，让整个子网重定向到 LAN 口，这个操作可以通过 OpenWrt 的 hotplug 机制来进行，保存以下脚本放在 `/etc/hotplug.d/iface/80-reset-route6` 并重启 WAN 接口即可
