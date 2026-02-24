---
title: ssh 代理的妙用
date: 2026-01-11 01:12:20
tags:
  - ssh
  - socks
  - gost
  - proxy
categories:
  - 软件工具
---
起因是需要让阿里云 ecs 访问 github，在使用 ssh -R 完成需求后，仔细研究了 ssh -L/-R 的区别。在搞明白后，觉得它们是如此的对称，设计的太好了。后面又发现了gost 这个代理领域的”瑞士军刀“，将它和 ssh 正反代理结合，真的是可以玩出花了。

<!-- more -->

## ssh 正向和反向代理总结


本质就是 ssh 在两台机器间建立了一个安全隧道（secure channel），ssh `-L/-R` 使用 ssh 隧道，**实现在本地的和远程之间的 socket 转发**。

```shell
 -L/R [bind_address:]port  :  host:hostport
       socket1                 socket2
```

- socket 支持 TCP （ip 和 端口） 和 Unix socket
- -L（-R） 实现本地（远程）监听一个 socket，远程（本地）对指定的 host:hostport 建立一个 TCP 连接，ssh 在这两个 socket 之间转发数据


### 正向代理

```shell
 -L [bind_address:]port:host:hostport
 -L [bind_address:]port:remote_socket
 -L local_socket:host:hostport
 -L local_socket:remote_socket
```

- `[bind_address:]port` 表示本地监听的 socket，发送给这个 socket 的数据，会被转发到远程的 socket `host:hostport`（由远程机器连接创建）
- 本地监听的 socket
    - 不指定 bind_address 时，一般是绑定到 localhost（`GatewayPorts` 默认 `no`，绑定到 local），只有本机可以访问。
    - 设置为`空`或者 `*` 时，绑定到所有地址（v4：`0.0.0.0` , v6：`[::]`）
    - By default, the local port is bound in accordance with the GatewayPorts setting.  However, an explicit bind_address may be used to bind the connection to a specific address.  The bind_address of `localhost` indicates that the listening port be bound for local use only, while an empty address or `*` indicates that the port should be available from all interfaces.

### 反向代理

```shell
-R [bind_address:]port:host:hostport
-R [bind_address:]port:local_socket
-R remote_socket:host:hostport
-R remote_socket:local_socket
-R [bind_address:]port
```

- `[bind_address:]port` 和 `host:hostport` 表示的远程和本地刚好对调了一下，`[bind_address:]port` 此时表示远程机器上监听的端口。
- 默认绑定到 loopback 接口（127.0.0.1）。想要绑定到任意接口只有远程 sshd `GatewayPorts` 启用才行（启用时默认绑定到 0.0.0.0）。

### Bonus：SOCKS 代理任意流量

ssh -L 可以实现让远程代理特定 ip 和 端口流量，有没有办法代理任意地址流量呢。

ssh 支持 -D 选项

```shell
-D [bind_address:]port
```

- 简单来说就是在本地监听 `[bind_address:]port`，启动一个 socks 代理服务。
- socks 代理任意流量的原理：1）socks 客户端请求 socks 服务器，告诉需要连接目的地址。2）socks 服务器和目的地址建立连接，之后在两个 socket 之间转发 TCP 流量。
- 支持 SOCKS4/SOCKS5 协议
  - SOCKS5 支持代理 UDP：1）客户端首先通过 **TCP** 连接到 SOCKS5 服务器，发送一个 `UDP ASSOCIATE` 请求。服务器会告诉客户端：“我已经准备好了“。2）客户端将原始的 UDP 数据包封装（加上 SOCKS5 特有的报头），然后通过 **UDP** 协议发送到服务器指定的端口。服务器收到后，剥离报头，再将原始 UDP 数据转发给最终的目标。
- Specifies a local “dynamic” application-level port forwarding.  This works by allocating a socket to listen to port on the local side, optionally bound to the specified bind_address.  Whenever a connection is made to this port, the connection is forwarded over the secure channel, and the application protocol is then used to determine where to connect to from the remote machine.

ssh -R 也有一个**动态远程端口转发**的功能，和 -D 的区别是 -R 是在**远程**监听 socks 服务，将流量通过本地转发。**可以一条命令实现让远程服务器通过本地机器代理上网**，对于远程服务器没法访问外网（比如国内 ecs 没法访问 github）很方便。

```shell
# in local machine
ssh -R 11223 server

# in server
export all_proxy=socks5h://127.0.0.1:11223
# sock5h 表示通过代理进行 dns 解析

curl -L -O
# wget 不支持 socks 代理
```

| 参数          | 命令示例                       | 代理类型       | 监听位置       | 流量出口 (IP变成谁)       |
| :---------- | :------------------------- | :--------- | :--------- | :----------------- |
| **-D**      | `ssh -D 1080 B`            | 动态本地转发     | 本地 (A)     | 远程 (B)             |
| **-R** (完整) | `ssh -R 8080:1.2.3.4:80 B` | 静态远程转发     | 远程 (B)     | 本地 (A) -> 固定目标     |
| **-R** (简写) | `ssh -R 1080 B`            | **动态远程转发** | **远程 (B)** | **本地 (A) -> 任意目标** |

### 优化选项

- **-N (No Command)**：告诉 SSH 只建立连接，不执行远程命令（即不打开 Shell 终端）。
  - 你只想用它做隧道，不需要终端交互，设置此项可以防止误操作。
- **-f (Background)**：让 SSH 在后台运行。
  - 输入密码连接成功后，SSH 会立即进入后台，释放当前终端窗口。通常与 -N 配合使用。
- **-q (Quiet)**：静默模式。
  - 减少不必要的输出日志。
- **-C (Compression)**：开启压缩。
    - **开启**：如果你在低速网络（如跨国 VPS、手机热点）上运行。
    - **关闭**：如果你在局域网内，或者传输的是已经压缩过的文件（如 JPG, ZIP, 视频），开启压缩反而会增加 CPU 负载并降低速度。
- **-o ServerAliveInterval=30**：客户端每隔 30 秒向服务器发送一个“心跳”包。
- **-o ServerAliveCountMax=3**：如果连续 3 次心跳包没有回应，则强制断开连接并退出。
- **-o ExitOnForwardFailure=yes**：如果端口转发绑定失败（例如端口已被占用），直接退出程序。
  - 原因：默认情况下，如果转发失败，SSH 仍会保持连接，这会导致你以为代理通了其实没通。

Tips 临时使用，通常开启 `-N -C` 即可

## ssh 使用示例收集

### 正向代理

#### 访问远程 localhost 服务

一些服务为了安全，会监听 localhost，只有本机可以访问。通过正向代理，可以让本地访问一些远程的 localhost 服务。

*Tips：除此之外，如果服务只有某一个网段的机器可以访问。也可以连接该网段内任意一台机器，通过 ssh 正向代理实现本地访问。*

```shell
# A
ssh -L 1234:localhost:80 B
curl http://localhost:1234  # 此时 A 访问本地的 1234，实际访问的是 B 的 80

# 非标准端口完整写法
ssh -L 1234:localhost:80 -p 2222 root@B
```

#### jump——ssh 跳板机

jump 本质就是通过中间节点代理 target ssh 端口。

- 连续 jump

```shell
ssh -J A,B C  # 通过 A -> B 再连接 C，A,B 逗号分隔
```

- 正向代理 + jump

```shell
ssh -J A -L 1234:localhost:80 B
```
### 反向代理

#### 内网服务器使用本地上网

实验室可能有一些内网机器，笔记本可以连接，而且笔记本自身可以访问外网。此时可以让服务器通过本地访问外网。（对于科学上网场景同样有用，让服务器通过本地机器科学上网）

```shell
# local
ssh -R 11223 server

# server
export all_proxy=socks5h://127.0.0.1:11223
```

- 缺点是 ssh 只支持 socks 代理，curl 可以使用，wget 无法使用
- 可以通过后面的 gost 实现本地监听 http 代理
- 或者像 cfw 这样的代理软件，自身就会在本地监听 http/socks 代理服务，此时通过 ssh -R 将远程转发到本地代理端口

#### 借用 VPS 公网 v4 暴露本地服务

```shell
### openwrt 路由器上
# 将 ecs 2203 端口转发到本地 ssh
ssh -fNR :2203:localhost:22 root@ecs -p 22

### 公网访问 openwrt
ssh root@ecs -p 2203
```

还需要设置 ssh 选项 keepalive，避免连接关闭。

bonus: openwrt ssh（dropbear）连接服务器时免密配置
```shell
mkdir ~/.ssh
ln -s /etc/dropbear/dropbear_ed25519_host_key ~/.ssh/id_dropbear # dropbear 默认 -i ~/.ssh/id_dropbear
```

#### 代理公司内网

在外需要访问公司内网使用，可以使用内网任意一台机器执行一条命令实现一个简易的代理服务器

```shell
ssh -R 11223 ecs
```

之后在浏览器上安装 Proxy SwitchOmega 插件，配置 Socks5 代理。

![image.png](https://imagebed.yfycloud.site/2026/02/51d8d485203250398b40d4f0f3b690b7.png)

在需要的网页上使用代理

![image.png](https://imagebed.yfycloud.site/2026/02/8a5af1130232ae091ef8ae376f5eba0c.png)

## gost

[ginuerzh/gost: GO Simple Tunnel - a simple tunnel written in golang](https://github.com/ginuerzh/gost)

优点

- 语法真的异常简洁，轻松实现搭建 socks/http/ss 代理，支持代理链等
- 支持几乎所有平台： linux, windows, freebsd + x86, amd64, arm, mips
- 体积只有 4MB

### 基本命令

**作为 http/Socks 代理**

![image.png](https://imagebed.yfycloud.site/2026/01/89205d48b4932382144ff24bb3ea9a5f.png)

```shell
# 作为标准HTTP/SOCKS5代理（一个端口复用）
gost -L=:8080

# 带密码的 http 代理
gost -L http://user:pass@:8080
```

**多级转发代理(代理链)**

![image.png](https://imagebed.yfycloud.site/2026/01/4d07e8a7f2cb304139ed326f15c239a9.png)

gost 按照 -F 设置的顺序通过代理链将请求最终转发给 a.b.c.d:NNNN 处理，每一个转发代理可以是任意HTTP/HTTPS/HTTP2/SOCKS4/SOCKS5/Shadowsocks 类型代理。

```shell
gost -L=:8080 -F=quic://192.168.1.1:6121 -F=socks5+wss://192.168.1.2:1080 -F=http2://192.168.1.3:443 ... -F=a.b.c.d:NNNN
```

**正向代理/本地端口转发**

```shell
# 将本地TCP端口2222上的数据(通过代理链)转发到192.168.1.1:22上
gost -L=tcp://:2222/192.168.1.1:22 [-F=...]
```

**反向代理/远程端口转发**

```shell
# 将172.24.10.1:2222上的数据(通过代理链)转发到192.168.1.1:22上
gost -L=rtcp://:2222/192.168.1.1:22 [-F=... -F=socks5://172.24.10.1:1080]
```

### 用例

#### VPS 代理本地 ssh

- 本例子没有在 vps 启动 gost，而是复用了 ssh 服务作为底层隧道
- 本例子只是为了说明 gost 语法，实际使用 ssh 的 -R 是最方便的
```shell
# 无公网机器 B
gost -L rtcp://:2204/127.0.0.1:22 -F forward+ssh://user@vps:port?ssh_key=/path/to/id

# 之后通过 vps 公网 ip 访问 B
ssh xx@vps -p 2204
```

- 目前 github 下载的 v2.12 (202410）是 v2 版本（gost v3 许多关键字都变了：[SSH - GOST](https://gost.run/en/tutorials/protocols/ssh/)）
    - gost的SSH支持两种模式
        - Forwarding Mode（`forward+ssh`）：作为转发通道，支持 tcp，用于本地/远程TCP端口转发使用。
        - Tunnel Mode（`ssh`）：作为通道传输其他协议，支持 tcp, udp
    - `ssh_key` 用于权限验证
- 上面使用 vps 本来就有的 ssh 服务，因此**不需要在 vps 上运行 gost 命令**
- gost 优缺点
    - 可能解决了 ssh 需要保活的问题
    - 同样需要设置 `GatewayPorts yes`


#### 内网服务器使用本地上网

解决 ssh 只能监听 socks 代理的问题

```shell
# 在本地启动带密码的 HTTP 代理
./gost -L http://user:pass@:8080

# 将 ECS 的 1080 端口转发到本地的 8080 端口 
ssh -R 1080:localhost:8080 ecs_user@ecs_ip
```

此时可以在服务器上使用 http 代理了

```shell
export all_proxy=http://user:pass@:8080
```

**如果使用单纯使用 gost，不使用 ssh**

```shell
# 启动隧道服务端，监听 8000 端口用于建立隧道连接
./gost -L relay://:8000


# 1. 启动本地 HTTP 代理，带上你的用户名(user)和密码(pass) 
# 2. 通过 rtcp 将 ECS 的 1080 端口映射到本地的 8080 端口 
./gost -L http://user:pass@:8080 -L rtcp://:1080/:8080 -F relay://ECS_IP:8000
```

Tips：**加密隧道**：为了防止流量被识别或拦截，可以将 relay 替换为 relay+tls 或 relay+mwss（带证书加密）
