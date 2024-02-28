---
title: 为设备分配静态 v6 基于 ndppd
date: 2024-02-27 23:28:52
tags:
  - ipv6
  - ndppd
categories:
  - 折腾
---
## 背景

学校提供了 ipv6，我的许多服务都可以使用 v6 访问。但是学校提供的 PD 可能会变，虽然使用 ddns 可以将 v6 地址映射到固定的域名，但是 ddns 有延迟性。因此最好的解决办法仍然是给机器设置静态 ip。

*p.s. 短期重启网卡 PD 不会变，但是如果长期离线再上线就可能变，类似于 dhcp。*

宿舍的 v6 wan 口无法设置静态 ip，因为学校路由器要求设备必须发了 RS 才会路由该包。

信智楼则可以静态设置。当访问外网时，学校路由器不会检查源地址，会直接路由出去。等接收到回包时，学校路由器看到目的地址为设置的静态地址，会在广播域上发送 NS，我自己路由的 wan 口接收到 NS 后响应 NA（v6 版的 ARP 过程）。学校路由器便知道了我路由器 wan 口的 mac 地址，于是将包发送给我的路由器 wan 口。

虽然信智楼可以静态设置 v6，但是仅限于 wan 口。lan 下面的设备如果手动设置了静态 v6，是无法正常上网的。重复上过程会发现学校仍然会正常把包路由出去，但是收到回包后，会像之前一样发送 NS。而我们路由器的 wan 口接收到 NS 后，根本不会响应 NA（因为不是自己的 v6 地址）。LAN 和 WAN 又不是一个广播域，因此收不到 NS。从而导致学校路由器并不会把回包交给我们。

但其实上面的需求是可以实现的，我们需要一个叫做 NDP proxy 的软件。

<!-- more -->

## 配置

### ndppd 配置

NDP(neighbor discovery protocol) 是 ipv6 中的一套协议，负责 ipv6 的：地址自动配置、邻居检测、ARP、地址冲突检测等。

背景中行不通的**原因在于 WAN 不会响应非自己 ip 的 NS 报文**。对于接口上有的 ip 地址，内核会帮我们响应 NS。对于其它的 ip，则需要第三方软件来设置响应。我们需要用到的便是一个叫 ndppd(ndp proxy daemon) 的软件。

该软件在 openwrt 上也有，直接安装即可

```bash
opkg install ndppd
```

软件的配置如下很简单

```yaml
proxy br-wan {
   # router yes
   timeout 500
   ttl 30000

   rule 2001:da8:d800:336::beef:aa00/120 {
   static
   }
}
```

配置选项说明：

- `proxy <interface>`设置一个监听器。监听指定接口上的 NS，并匹配 rule 决定是否响应。可以设置多个 proxy。
- rule 可以配置几种响应模式
  - `static`：只要匹配到地址，就响应
  - `iface <interface>`：会将 NS 在指定的接口上转发，收到 NA 时才响应。相当于确保指定接口下面该地址设备是存在的才响应
  - `auto`：类似于 iface，但是 ndppd 自动根据`/proc/net/ipv6_route`决定接口
- `router`：NA 中是否包含 route flag。表明本设备是台路由器

这里我们手动保留了 120 位的一段 v6 地址，剩余 8 位可以分配给 255 个设备。使用 static 即可。

启动运行 ndppd

```bash
service ndppd enable
service ndppd start
```

### 配置路由

ndppd 相当于让 wan 口伪装有保留的一段 v6 地址。上级路由器将包发来后，需要 forward 给真正的设备。

执行以下命令添加路由：

```bash
ip -6 ro add 2001:da8:d800:336::beef:aaaa via fe80::6818:12ff:fec3:7f7f dev br-lan
```

其中 via 后的地址是对应设备的 v6 本地链路地址。这种写法把设备当作一个路由器，路由器将目的地址的包发送给对面设备。

另一种写法也是可行的。这种写法表示目的地址位于 br-lan 接口所在广播域。路由器可以把包直接发送给对应设备（中途还涉及 ARP 过程）。

```bash
ip -6 ro add 2001:da8:d800:336::beef:aaaa dev br-lan
```

!!! note "onlink 选项"

    如果上述命令失败，可以添加onlink选项。上述命令会检查目的地址是否位于br-lan的子网，而onlink用于避免该检查。


路由表对比

```bash
2001:da8:d800:336::beef:aaaa via fe80::b8c5:64ff:fe4b:4327 dev br-lan proto static metric 1024 pref medium
2001:da8:d800:336::beef:aaab dev br-lan metric 1024 onlink pref medium
```

### 效果

阿里 ecs 上 mtr 效果
![image.png](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20240228001726.png)

tcpdump 抓到的 NS，NA

```bash
2024-02-27 15:22:27.295778 IP6 2001:da8:d800:336::279 > ff02::1:ffef:aaaa: ICMP6, neighbor solicitation, who has 2001:da8:d800:336::beef:aaaa, length 32
2024-02-27 15:22:27.295880 IP6 2001:da8:d800:336::1c > 2001:da8:d800:336::279: ICMP6, neighbor advertisement, tgt is 2001:da8:d800:336::beef:aaaa, length 32
2024-02-27 15:22:27.300040 IP6 fe80::3ecd:57ff:fe33:bb01 > ff02::1:ffef:aaaa: ICMP6, neighbor solicitation, who has 2001:da8:d800:336::beef:aaaa, length 32
2024-02-27 15:22:27.300045 IP6 fe80::3ecd:57ff:fe33:bb01 > ff02::1:ffef:aaaa: ICMP6, neighbor solicitation, who has 2001:da8:d800:336::beef:aaaa, length 32
2024-02-27 15:22:27.300120 IP6 fe80::216:3eff:fee2:4e72 > fe80::3ecd:57ff:fe33:bb01: ICMP6, neighbor advertisement, tgt is 2001:da8:d800:336::beef:aaaa, length 32
2024-02-27 15:22:27.300153 IP6 fe80::216:3eff:fee2:4e72 > fe80::3ecd:57ff:fe33:bb01: ICMP6, neighbor advertisement, tgt is 2001:da8:d800:336::beef:aaaa, length 32
```

## 遇到的问题

### ndppd 不响应 NS

`tcpdump -ni eth0`抓到了指定 ip 的 NS，但是 ndppd 就是不响应。

*p.s. 1）刚开始以为是 ndppd 没有运行，因为 service 显示 ndppd 是 stopped 的，但其实 ps 是能看到 ndppd 进程的。2）即使命令行手动运行 ndppd`ndppd -c /etc/ndppd.conf -v`，开启 verbose 模式，仍然是没有任何输出*

问题在于`eth0`是连接在`br-wan`上的。这涉及到 bridge 的原理，包从 eth0 接口进来后，在进入网络栈之前就会进入 bridge 的网络栈处理。对于 eth0 来说，是没有包进入网络栈的。

因此需要把 ndppd 的配置改为 br-wan。

### 需要 restart ndppd

ndppd 不生效，restart 后才生效
需要研究。

## 参考资料

- [ndppd/README at 0.2.5 · DanielAdolfsson/ndppd (github.com)](https://github.com/DanielAdolfsson/ndppd/blob/0.2.5/README)
