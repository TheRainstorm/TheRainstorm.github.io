---
title: MTU 的那些坑
date: 2024-03-15 12:55:15
tags:
  - MTU
  - PMTUD
  - MSS
  - fragment
  - GRE
categories:
  - 博客 & 网络
---
## 背景

背景：软件不支持手动 ip，导致需要二层隧道连接两个路由器。

!!! note "通过 mDNS proxy 实现本地发现"

    之前还研究过这类软件一般是怎么发现server的。发现确实有一些方法可以实现跨网络的发现。比如常见的“发现”协议（不知道术语是什么）有mDNS和upnp。是通过ipv4 multicast实现的，所以只要能proxy多播包，就可以实现在两个网络互相发现。

## 二层隧道方案


![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/gre-tap.drawio.png)


- 两个路由器间通过 WAN 口 IPv4 建立 GRE Tap 隧道
- op1 上将直接将 tap 接口桥接到到原有 br-lan 上
- op2 保留了原本自己的 lan，然后创建了一个新的 br-lan2，连接了 gre tap 接口和 eth2 接口。
!!! note "op2 是 PVE Host 上一个容器"

    op2是PVE上的一个LXC容器，分配了eth0, eth1, eth2分别对应wan, lan1, lan2

- op2 侧将一个无线路由器连接到 PVE host（软路由）网口 enp5s0，该网口位于 PVE vmbr2 下，而 op2 eth2 也连接到了 vmbr2。

因此通过切换无线路由器连接到不同网口，可以控制无线路由器位于 lan1 还是 lan2。

!!! note "VLAN 切换 SSID 方案"

    刚开始想了一个更复杂不用改动AP网线的方案。将AP通过一根线和软路由连接，然后创建2个vlan。AP上，创建两个不同SSID绑定到不同VLAN接口上。这样就可以通过更改连接的WiFi来切换lan1和lan2了。不过PVE上vlan貌似配置有点复杂，可能需要创建一个vlan awareness的vmbr1，然后op2连接到vmbr1的eth1和eth2指定不同vlan id。大概就是以上方案，但是我没想清楚vmbr1下untagged的接口怎么办。vmbr1设置了awareness后还能连接untagged的端口吗？因为不太了解PVE VLAN bridge的更详细内容，加上路由器就在手边，换条线也很快，因此就没有使用该方案。

## 遇到的问题

实现上述方案后，确实让一开始的 VR 串流软件可以工作了，但是确遇到了一些意外的问题。

我发现我的手机平板都无法使用 moonlight 串流我位于 op1 下的台式机了。

- moonlight 显示在线，但是一连接就报错。报错让检查 UDP 端口 478000 是否开放。
- 不过我的笔记本同样连接的 WiFi，但是确能够正常串流。虽然隔一段时间就会断开（后面发现这个好像是学校网络的问题，也让我困惑了好久）

以前也遇到这样能 ping 通，但是一发送数据就出问题的现象，问题都是哪里的接口 MTU 设置不正确导致的。因此这次也是往 MTU 这方面排查问题。加上之前遇到的 MSS 问题，于是这次相当于把我知道的都结合起来，看能否解决这个问题。

<!-- more -->

## 基础知识

### IP 分片

MTU，链路层的概念，表示能承载的网络层及以上的包的大小。正常以太网帧的 payload 部分范围应该在 46B - 1500B 之间，也就是 MTU 最大为 1500。
![image.png](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20240315234352.png)

当我们使用 GRE，Wireguard 等隧道时，实际的 MTU 需要减去额外 Header 的开销，因此就会小于 1500。比如 wg ipv4 = 1440, wg ipv6 = 1420。

当上层协议包大小超过链路层 MTU 时，我们需要一种机制将包拆分，然后合并（重组）。这个功能是在 IP 层实现的。IPv4 Header 中有 Flag 和 Fragment offset，用于实现分片与合并。

![image.png](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20240315235458.png)

!!! note "Don't fragment 标志"

    ipv4头中Flags可以设置DF flag，表示禁止分片。这样当需要分片时，router节点应该返回ICMP Fragmentation Needed (Type 3, Code 4)。ipv6由于已经禁止了router分片，因此header中没有也不需要该标志。

!!! note "ipv4 和 ipv6 分片的区别"

    ipv4中间路由器可以对包进行分片，**最后所有的分片包在目的节点合并**
    而ipv6禁止了路由器对包进行分片，分片必须在源和目的节点上进行。因此通信节点间必须先进行PMTUD（路径MTU发现），否则遇到MTU不够时，中间节点会返回ICMPv6 Packet Too Big (Type 2)。
### PMTUD

PMTUD，即 Path MTU Dsicovery，用于发现通信路径上的最大 MTU，用来避免分片。

PMTUD 常见的是基于 ICMP 的方法：

- 对于 IPv4，可以设置 DF 标志，如果收到 Fragmentation Needed，就减小 MTU（ICMP 数据中包含下一条需要的 MTU）
- 对于 IPv6，没有不分片标志。设置初始 MTU 为网卡 MTU，如果中间设备返回 ICMPv6 type 2 消息，就减少 MTU。

我们可以使用 ping 来测试
```
$ ping www.baidu.com -l 1372 -f
正在 Ping www.a.shifen.com [182.61.200.6] 具有 1372 字节的数据:
来自 182.61.200.6 的回复: 字节=1372 时间=33ms TTL=46

$ ping www.baidu.com -l 1373 -f
正在 Ping www.a.shifen.com [182.61.200.6] 具有 1373 字节的数据:
需要拆分数据包但是设置 DF。
```

可以看到，我到百度的 PTMU 为 1372（因为实际中经过了一个 1400 的 wg 隧道）
- 其中 `-l` 指定 icmp data 部分，因此实际 ip 包大小为：20 + 8 + 1372 = 1400
- `-f`禁用分片

下图是使用 wireshark 抓到的 ICMP 包截图。类型为 destination unreachable，code 表明这是由于需要分片导致的。ICMP 还包含了下一条的 MTU 是 1400。并且将原本的 ip 包放在了结尾，可以看到原本的 IP 头，和 icmp 头。
![image.png](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20240316192524.png)

### PMTUD 失败与 MSS clamping

实际路由器由于安全考虑，会禁止转发 ICMP 消息，因此会导致 PMTUD 失效。这样对于 ipv6，可能会产生黑洞连接现象：TCP 三次握手成功（数据小于 MTU），但是发送数据没有响应（超过路径 MTU，包被丢弃）。

因此有些路由器提供了 MSS clamping 功能。路由器会对转发的 TCP 包的 MSS 进行设置，该操作基于 iptable 实现。可以设置静态的数值，也可以设置成根据出口网卡 MTU 自动设置。

!!! note "MSS 介绍"

  - MSS (maximum segment size) 是 TCP 中的概念，是连接双方能够接收的最大 segment 大小。
  - MSS = MTU - IP header - TCP header。MTU 为 1500 时，MSS 为 1460
  - MSS 会在 TCP 三次握手时进行协商，作为 TCP 头中 option 的内容。[并且只能在 SYNC 被设置时才能包含。](https://en.wikipedia.org/wiki/Transmission_Control_Protocol#:~:text=urgent%20data%20byte.-,Options,-(Variable%200%E2%80%93320)
  ![image.png](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20240316195430.png)

!!! note "MSS clamping 是双向的"

    MTU的影响是单项的，即路由器往一个接口转发时，如果包大于接口MTU，就会进行分片。MSS clamping后，从该接口进入和出去的包都会被修改MSS。这里盗一张图
    ![image.png](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20240316201316.png)

Openwrt 的 MSS 功能放在防火墙 Zone 设置中（毕竟是基于 iptable 的，确实是防火墙功能），默认 WAN zone 的 MSS clamping 是勾选上的。如果有 wireguard 等隧道接口的话，建议也勾上，因此这样可以避免在路由器上分片，提升 TCP 性能。

![image.png](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20240316200359.png)
### 参考资料

- 提到隧道往往需要限制 MSS 来避免分片：[什么是 MSS（最大分段大小）？ | Cloudflare (cloudflare-cn.com)](https://www.cloudflare-cn.com/learning/network-layer/what-is-mss/)
- 提到了 GRE 下 MSS 的计算：[什么是 GRE 隧道？| GRE 协议如何工作 | Cloudflare (cloudflare-cn.com)](https://www.cloudflare-cn.com/learning/network-layer/what-is-gre-tunneling/)
- MTU, MSS, PMTUD 联系：[MTU TCP-MSS 详解 - 知乎 (zhihu.com)](https://zhuanlan.zhihu.com/p/139537936)
- 提到了 1）v4 和 v6 的差异；2）中间路由器禁用 ICMP 导致黑洞连接现象；3）有些路由器提供 MSS 方案解决 PMTUD 失败的问题。[Path MTU Discovery - Wikipedia](https://en.wikipedia.org/wiki/Path_MTU_Discovery)
- 列出了 PMTUD black holes：[Black hole (networking) - Wikipedia](https://en.wikipedia.org/wiki/Black_hole_(networking))
## 定位问题（但无法解除）

### 实验一：设置 bridge MTU 不影响接收只影响发送

kvm-win10 (1500)-> pve vmbr1(1280) -> op1: eth1 (1500)->  br-lan (1280)

虽然 op1 br-lan mtu 已经设置成了 1280，但是实际上由于包是从 eth1 进入的，所以并不会丢掉。

- 中途 vmbr1 没有把包丢掉，我猜测是因为底层的接口实际 MTU 都是 1500 的，因此能够接收就不会丢掉。和 bridge 自身 MTU 没有关系

然后可以发现**op1 response 时根据 br-lan 的 MTU 进行了分片**，这是符合 MTU 一开始的设计的。

```
$ ping 192.168.35.1 -l 1472 -f

正在 Ping 192.168.35.1 具有 1472 字节的数据:
来自 192.168.35.1 的回复: 字节=1472 时间<1ms TTL=64
来自 192.168.35.1 的回复: 字节=1472 时间<1ms TTL=64
```

```
root@op1 ➜  ~ tcpdump -ni eth1 icmp and host 192.168.35.5
tcpdump: verbose output suppressed, use -v[v]... for full protocol decode
listening on eth1, link-type EN10MB (Ethernet), snapshot length 262144 bytes
20:24:59.427833 IP 192.168.35.5 > 192.168.35.1: ICMP echo request, id 1, seq 1386, length 1480
20:24:59.427856 IP 192.168.35.1 > 192.168.35.5: ICMP echo reply, id 1, seq 1386, length 1256
20:24:59.427858 IP 192.168.35.1 > 192.168.35.5: ip-proto-1
```
### 实验二：同一个二层无法发 ICMP 导致黑洞

kvm-win10 (1500)-> pve vmbr1(1280) -> op1: eth1 (1280)->  br-lan (1280)

设置 eth1 mtu 后。完全 ping 不通，op1 上 tcpdump 抓不到任何包，只有 pve vmbr1 上能抓到。
此时即使是允许分片，也是一样的现象。

```
$ ping 192.168.35.1 -l 1472 -f

正在 Ping 192.168.35.1 具有 1472 字节的数据:
请求超时。
```

```
$ ping 192.168.35.1 -l 1472

正在 Ping 192.168.35.1 具有 1472 字节的数据:
请求超时。
```

产生该现象的原因是，op1 eth1 的 mtu 小了，包根本传不到 op1。**因为它们位于同一个二层，没有路由器负责分片**。

而 op1 又**没法返回 ICMP 报错信息**（因为这里 op1 不做为路由器），因此 kvm-win10 仍然继续以该大小包发送。

*下一个实验表明，此时如果收到 ICMP 报错，系统就会调整 PMTU，在发送 icmp request 时就进行分片。*
### 实验三：ICMP 发挥作用

op1 和 op2 通过 wireguard 隧道 wg_s2s 连接，而该隧道我将 MTU 设置成了 1400。当 kvm-win10 ping op2 的 wg 地址时，就会经过该隧道。

大致过程：kvm-win10(1500) -> op1 eth1(1500) -> op1 wg_s2s (1400) (out)

可以发现不允许分片时，无法 ping 通，路由器返回 ICMP 报错。允许分片就可以正常 ping 通了。
```
$ ping 10.0.32.2 -l 1373 -f

正在 Ping 10.0.32.2 具有 1373 字节的数据:
来自 192.168.35.1 的回复: 需要拆分数据包但是设置 DF。
需要拆分数据包但是设置 DF。
需要拆分数据包但是设置 DF。

$ ping 10.0.32.2 -l 1373

正在 Ping 10.0.32.2 具有 1373 字节的数据:
来自 10.0.32.2 的回复: 字节=1373 时间=2ms TTL=63
来自 10.0.32.2 的回复: 字节=1373 时间=2ms TTL=63
```

并且 tcpdump 抓包可以看到第二次 ping 时，kvm-win10 已经提前将包进行分片了。

- 第一条`192.168.35.5 > 10.0.32.2`，length 还是 1281 (1373+8)
- 第二次就已经变成连续两条`192.168.35.5 > 10.0.32.2`了。（长度是 1376 而不是 MTU 对应的 1380，是因为 ipv4 分片需要 8 字节对齐）
```
root@op1 ➜  ~ tcpdump -ni eth1 icmp and host 192.168.35.5
tcpdump: verbose output suppressed, use -v[v]... for full protocol decode
listening on eth1, link-type EN10MB (Ethernet), snapshot length 262144 bytes
20:45:09.452565 IP 192.168.35.5 > 10.0.32.2: ICMP echo request, id 1, seq 1400, length 1381
20:45:09.452590 IP 192.168.35.1 > 192.168.35.5: ICMP 10.0.32.2 unreachable - need to frag (mtu 1400), length 556
20:45:17.217676 IP 192.168.35.5 > 10.0.32.2: ICMP echo request, id 1, seq 1403, length 1376
20:45:17.217681 IP 192.168.35.5 > 10.0.32.2: ip-proto-1
20:45:17.219738 IP 10.0.32.2 > 192.168.35.5: ICMP echo reply, id 1, seq 1403, length 1256
20:45:17.219741 IP 10.0.32.2 > 192.168.35.5: ip-proto-1
```

**而要想提前分片，表明 OS 需要缓存目的地址的 PMTU**，windows 有命令可以查看 PMTU
```
netsh interface ipv4 show destinationcache
```

可以看到目的地址已经被设置成了 1400
```
接口 16: 以太网 2


PMTU 目标地址                                      下一个跃点地址
---- --------------------------------------------- -------------------------
1400 10.0.32.2                                     192.168.35.1
1500 20.42.65.91                                   192.168.35.1
1500 39.91.134.53                                  192.168.35.1
```

之后再发送大于 PMTU 的包时，windows 就会直接提示需要分片，而不会把包发出去，因此收不到来自路由器的 ICMP 报错消息。
```
$ ping 10.0.32.2 -l 1373 -f

正在 Ping 10.0.32.2 具有 1373 字节的数据:
需要拆分数据包但是设置 DF。
需要拆分数据包但是设置 DF。
```

### 实验四：GRE Tap 隧道导致二层 MTU 不一致

由于 GRE Tap 的存在，导致原本全部都是 1500MTU 的二层里，出现了 1284 的隧道通路。因此只要大于该 MTU 的包通过该通路就会被丢弃，并且不会返回 ICMP，从而导致黑洞。

op1 下的 KVM-win10 ping op2 下的笔记本时，只要 icmp data 大于 1256 就会导致该现象。即使允许分片，也 ping 不通。
```
$ ping 192.168.35.180 -l 1256

正在 Ping 192.168.35.180 具有 1256 字节的数据:
来自 192.168.35.180 的回复: 字节=1256 时间=2ms TTL=128
来自 192.168.35.180 的回复: 字节=1256 时间=2ms TTL=128

$ ping 192.168.35.180 -l 1257

正在 Ping 192.168.35.180 具有 1257 字节的数据:
Control-C
```

## 总结与思考

- 原因在于二层 MTU 不一致，导致包经过一个更小的通路时既无法分片，也无法返回 ICMP，从而导致黑洞。
- 对于 TCP 还能通过 MSS clamping 解决，但是对于 UDP 就没有办法了
- 如果二层隧道需要保证 MTU 一致，那用途是否太小？假设隧道 MTU 小于 1500，那么所有 1500 的设备都不能接入这个隧道。感觉只能连入几台可以手动调整 MTU 的设备。

- 疑点：
  - 为什么笔记本可以正确连接，而手机平板不行。wireshark 抓包时，确实笔记本的包更小。
    - OS 不同？windows 可能自己做了 PMTUD
### 可能的解决？

- Android 设置手动设置 MTU
- arp proxy，让两边通信实际并不走 gre 隧道，而是通过 wg 隧道？（感觉可行）
- 有没有 L2 上的 PMTUD？或者不基于 ICMP 不就行了？
- windows 上设置目标的 PMTU？（但是 MTU 单向的，貌似影响不到对面发包。但是也许串流场景对面发不了很大的包？）
## 参考

- windows 查看 PMTU：[Windows MTU active value after pmtu ? - Microsoft Community](https://answers.microsoft.com/en-us/windows/forum/all/windows-mtu-active-value-after-pmtu/ed7c2ce3-adc3-4135-9539-267a8e9fbe56)

