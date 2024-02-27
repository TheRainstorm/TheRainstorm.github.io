---
title: 为设备分配静态v6-ndppd
date: 2024-02-27 23:28:52
tags:
  - ipv6
  - ndppd
categories:
  - 折腾
---
## 背景

PD可能会变，ddns有延迟性，最好的是设置静态ip。

*p.s. 短期重启网卡不会变，但是如果长期离线再上线就可能变。类似于dhcp，因此在不能设置上游路由器的情况下无法保证静态*

宿舍的v6 wan口无法设置静态ip，因为学校路由器要求设备必须发了RS才会路由该包。信智楼则可以静态设置，当访问外网时，学校路由器不会检查源地址，会直接路由出去。等接收到回包时，学校路由器看到目的地址为设置的静态地址，会在广播域上发送NS，wan口接收到后响应NA（v6版的ARP过程）。学校路由器知道mac地址后，将包发送给路由器wan口。

虽然信智楼可以静态设置v6，但是仅限于wan口。lan下面的设备如果手动设置了静态v6，是无法正常上网的。重复上过程会发现学校仍然会正常把包路由出去，但是收到回包后，会像之前一样发送NS。而我们路由器的wan口接收到NS后，根本不会响应NA（因为不是自己的v6地址）。LAN和WAN又不是一个广播域，因此收不到NS。从而导致学校路由器并不会把回包交给我们。

但其实上面的需求是可以实现的，我们需要一个叫做NDP proxy的软件。

<!-- more -->

## 配置

### ndppd配置

NDP(neighbor discovery protocol)是ipv6中的一套协议，负责ipv6的：地址自动配置、邻居检测、ARP、地址冲突检测等。

背景中行不通的原因在于WAN不会响应非自己ip的NS报文。对于接口上有的ip地址，内核会帮我们响应NS。对于其它的ip，则需要第三方软件来设置响应。我们需要用到的便是一个ndppd(ndp proxy daemon)的软件。

该软件在openwrt上也有，直接安装即可
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

- `proxy <interface>`设置一个监听器。监听指定接口上的NS，并匹配rule决定是否响应。可以设置多个proxy。
- rule可以配置几种响应模式
  - `static`：只要匹配到地址，就响应
  - `iface <interface>`：会将NS在指定的接口上转发，收到NA时才响应。相当于确保指定接口下面该地址设备是存在的才响应
  - `auto`：类似于iface，但是ndppd自动根据`/proc/net/ipv6_route`决定接口
- `router`：NA中是否包含route flag。表明本设备是台路由器

这里我们手动保留了120位的一段v6地址，剩余8位可以分配给255个设备。使用static即可。

启动运行ndppd
```
service ndppd enable
service ndppd start
```
### 配置路由

ndppd相当于让wan口伪装有保留的一段v6地址。上级路由器将包发来后，需要forward给真正的设备。

执行以下命令添加路由：
```
ip -6 ro add 2001:da8:d800:336::beef:aaaa via fe80::6818:12ff:fec3:7f7f dev br-lan
```

其中via后的地址是对应设备的v6本地链路地址。这种写法把设备当作一个路由器，路由器将目的地址的包发送给对面设备。

感觉另一种写法应该也是有效的（待验证）。这种方法把包从br-lan发出去过程应该还涉及NS，NA过程。
```
ip -6 ro add 2001:da8:d800:336::beef:aaaa dev br-lan on-link
```
### 效果

阿里ecs上mtr效果
![image.png](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20240228001726.png)

tcpdump抓到的NS，NA
```
2024-02-27 15:22:27.295778 IP6 2001:da8:d800:336::279 > ff02::1:ffef:aaaa: ICMP6, neighbor solicitation, who has 2001:da8:d800:336::beef:aaaa, length 32
2024-02-27 15:22:27.295880 IP6 2001:da8:d800:336::1c > 2001:da8:d800:336::279: ICMP6, neighbor advertisement, tgt is 2001:da8:d800:336::beef:aaaa, length 32
2024-02-27 15:22:27.300040 IP6 fe80::3ecd:57ff:fe33:bb01 > ff02::1:ffef:aaaa: ICMP6, neighbor solicitation, who has 2001:da8:d800:336::beef:aaaa, length 32
2024-02-27 15:22:27.300045 IP6 fe80::3ecd:57ff:fe33:bb01 > ff02::1:ffef:aaaa: ICMP6, neighbor solicitation, who has 2001:da8:d800:336::beef:aaaa, length 32
2024-02-27 15:22:27.300120 IP6 fe80::216:3eff:fee2:4e72 > fe80::3ecd:57ff:fe33:bb01: ICMP6, neighbor advertisement, tgt is 2001:da8:d800:336::beef:aaaa, length 32
2024-02-27 15:22:27.300153 IP6 fe80::216:3eff:fee2:4e72 > fe80::3ecd:57ff:fe33:bb01: ICMP6, neighbor advertisement, tgt is 2001:da8:d800:336::beef:aaaa, length 32
```
## 遇到的问题

### ndppd不响应NS

`tcpdump -ni eth0`抓到了指定ip的NS，但是ndppd就是不响应。

*p.s. 1）刚开始以为是ndppd没有运行，因为service显示ndppd是stopped的，但其实ps是能看到ndppd进程的。2）即使命令行手动运行ndppd`ndppd -c /etc/ndppd.conf -v`，开启verbose模式，仍然是没有任何输出*

问题在于`eth0`是连接在`br-wan`上的。这涉及到bridge的原理，包从eth0接口进来后，在进入网络栈之前就会进入bridge的网络栈处理。对于eth0来说，是没有包进入网络栈的。

因此需要把ndppd的配置改为br-wan。

### 需要restart ndppd

ndppd不生效，restart后才生效
需要研究。
## 参考资料

- [ndppd/README at 0.2.5 · DanielAdolfsson/ndppd (github.com)](https://github.com/DanielAdolfsson/ndppd/blob/0.2.5/README)