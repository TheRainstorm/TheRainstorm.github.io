---
title: linux 创建代理
date: 2024-10-03 20:43:19
tags:
  - linux
  - proxy
  - http
  - socks
categories:
  - 博客 & 网络
---

我自己的机器配置了透明代理，因此配置开发环境等非常方便。但是实验室服务器等其它机器则通常没有自由的网络环境。因此如果能够让其它机器通过我内网的一台 linux 机器（通常是 VM）上网就很方便了。

由于并不需要绕过 GFW，传统的代理协议如 HTTP 代理和 Socks 即可，并且许多软件都对这两种协议有支持。比如 linux 命令行下的软件大部分支持通过环境变量启用代理，如 curl, wget, git。浏览器甚至 windows 操作系统自身通常也支持设置系统代理（也是对浏览器生效）。因此本片文章主要总结了搭建这两种**代理服务器**的常见软件。

总结：调研下来，虽然这两种协议历史悠久，有成熟的软件工具。但是目前大部分软件功能都太多了，这导致配置很复杂（比如 squid 9000 行的配置文件）这对简单使用代理功能有点 overkill 了。不过虽然配置复杂，学习后至少能用，因此就先不纠结了。**要我说感觉可以使用 python 简单糊一个单文件脚本，支持 1）密码认证 2）基于 ip 的访问控制 3）并且端口复用，同时支持 http 和 socks。可以放在 TODO list 里。

<!-- more -->
## 基础知识

### HTTP代理

首先复习下 HTTP 代理，这个协议很简单。第一种模式直接转发 HTTP 报文即可。第二种模式仅是使用了 HTTP 方法建立连接，打开 TCP 连接后就和 HTTP 报文没啥关系了，可以代理各种基于 TCP 的协议。（因此不支持 UDP）

两种模式：
- 中间人模式
  - 无法代理HTTPS，因为HTTPS需要证书，而代理服务器无法提供。
- 隧道模式

![](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/f975dcf4258847fc953be37343b14a36~tplv-k3u1fbpfcp-zoom-in-crop-mark:1512:0:0:0.awebp)

![](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/c514cc172f6c41e08f94e0a977dbf525~tplv-k3u1fbpfcp-zoom-in-crop-mark:1512:0:0:0.awebp)
[HTTP 代理原理及实现 - 掘金 (juejin.cn)](https://juejin.cn/post/6998351770871152653)

### Socks 代理

支持 UDP（主要区别是阶段三是直接转发 UDP packet，还是建立 TCP 连接后 relay 数据）  ，并且协商阶段可以支持多种认证方法。

[理解socks5协议的工作过程和协议细节 | Bigbyto (wiyi.org)](https://wiyi.org/socks5-protocol-in-deep.html)

![socks5 协议过程](https://wiyi.org/assets/images/socks5/client-socks5_f.jpg)

### client 软件设置代理

通过查看 curl 和 wget 软件的 man 手册，我们可以发现这些工具有一节 ENVIRONMENT 介绍支持的代理环境变量。通常支持以下环境变量。

- `http_proxy`, `https_proxy`
  - If set, the http_proxy and https_proxy variables should contain the URLs of the proxies for HTTP and HTTPS connections respectively.
- `ftp_proxy`
  - This variable should contain the URL of the proxy for FTP connections.  It is quite common that http_proxy and ftp_proxy are set to the same URL.
- `all_proxy`
  - Sets the proxy server to use if no protocol-specific proxy is set.
- `no_proxy`
  - This variable should contain a comma-separated list of domain extensions proxy should not be used for.  For instance, if the value of no_proxy is .mit.edu, proxy will not be used to retrieve documents from MIT.

可以发现

- 可以针对不同协议设置不同代理。**仅设置 http_proxy 的话，不会对 https 网站生效**
- **建议使用小写**。The environment variables can be specified in l**ower case or upper case**. The lower case version has precedence. http_proxy is an exception as it is only available in lower case.
- socks 协议家族
  - `socks4://, socks4a://, socks5:// or socks5h:// `
  - `socks5h` 表示域名在代理服务器上解析
    - Since clients are allowed to use either resolved addresses or domain names, a convention from [cURL](https://en.wikipedia.org/wiki/CURL "CURL") exists to label the domain name variant of SOCKS5 "socks5h", and the other simply "socks5". A similar convention exists between SOCKS4a and SOCKS4.[[18]](https://en.wikipedia.org/wiki/SOCKS#cite_note-18)
- 对于需要 authentication 的代理服务器，通常格式如下 [git/Documentation/config/http.txt at 0ca365c2ed48084974c7081bdfe3189094a2b993 · git/git (github.com)](https://github.com/git/git/blob/0ca365c2ed48084974c7081bdfe3189094a2b993/Documentation/config/http.txt#L8-L9)
  - `[protocol://][user[:password]@]proxyhost[:port][/path]`

## HTTP 代理服务器

### privoxy

[Privoxy - Community Help Wiki (ubuntu.com)](https://help.ubuntu.com/community/Privoxy)

- 唯一一个只需要改下端口号就可以使用的

```
sudo apt install privoxy
vim /etc/privoxy/config

sudo systemctl start privoxy
```
#### 我的访问控制

由于这个 HTTP 代理是公开的。目前我不希望有人通过这个代理入侵我的内网。因此添加了如下规则。（在结尾处，能够覆盖前面的规则）
注意 privoxy 的匹配是基于字符串的，因此**不支持 CIDR 地址**。

```
{ +block{My network can only be access by VPN} }
192.168.*.*
10.*.*.*
```
#### 访问控制文档

privoxy 使用 action 来进行访问控制

> The actions files are used to define what _actions_ Privoxy takes for which URLs, and thus determines how ad images, cookies and various other aspects of HTTP content and transactions are handled, and on which sites (or even parts thereof).

通过自定义配置 user.action 来覆盖默认配置 default.action（定义了许多预定义规则如拦截广告、拦截弹窗、Cookie 处理）
> The over-riding principle when applying actions, is that the last action that matches a given URL wins. The broadest, most general rules go first (defined in default.action), followed by any exceptions (typically also in default.action), which are then followed lastly by any local preferences (typically in _user_.action). Generally, user.action has the last word.


**action 文件由一系列 section 组成，包含了 action 和要匹配的 pattern**

- Actions files are divided into sections.
- They have a **heading line** (often split up to multiple lines for readability) which consist of **a list of actions**, separated by whitespace and enclosed in curly braces.
- Below that, there is a list of URL and tag **patterns**, each on a separate line.

```
{ +handle-as-image  +block{Banner ads.} }
# Block these as if they were images. Send no block page.
banners.example.com
media.example.com/.*banners
.example.com/images/ads/
```

##### **pattern 格式**

- Generally, an URL pattern has the form `<host><port>/<path>`
- The host part uses a simple globbing type matching technique, while the path part uses more flexible ["Regular Expressions"](https://en.wikipedia.org/wiki/Regular_expressions) (POSIX 1003.2).
- ipv6 地址需要使用 `<>` 包起来

例子
```shell
# host pattern  (glob synatax)

ad*.example.com
.?pix.com
www[1-9a-ez].example.c*

# path pattern (regular expression)
.example.com/.*/index.html$
.example.com/(.*/)?index\.html$  # Will match any page in the domain of "example.com" that is named "index.html"

.example.com/(.*/)(ads|banners?|junk)
#This regular expression will match any path of "example.com" that contains any of the words "ads", "banner", "banners" (because of the "?") or "junk".
```

!!!? note bouns

    request pattern：还可以根据 HTTP header 来匹配。以 `TAG:` 为开头
    
>     Request tag patterns are used to change the applying actions based on the request's tags. Tags can be created based on HTTP headers with either the [client-header-tagger](https://www.privoxy.org/user-manual/actions-file.html#CLIENT-HEADER-TAGGER) or the [server-header-tagger](https://www.privoxy.org/user-manual/actions-file.html#SERVER-HEADER-TAGGER) action.

##### **Action**

默认是关闭的，除非在 action 文件中显示地打开（*So in this case Privoxy would just be a normal, non-blocking, non-filtering proxy.*）。使用 `+` 开启，`-` 关闭。

action 可能是带有参数的。多值的参数多次匹配可以累加

```
+name{param}   # enable action and add param to the list of parameters
-name{param}   # remove the parameter param from the list of parameters
             # If it was the last one left, disable the action.
-name          # disable this action completely and remove all parameters from the list
```

action list：有数不过来的 action，参考[manual](https://www.privoxy.org/user-manual/actions-file.html#:~:text=8.5.-,Actions,-All%20actions%20are)。我们主要关注 block 即可。
代理也是一种中间人攻击，可以做到好多有趣的事（由于 HTTP 协议基础部分还是简单的，所以还是好理解的）

- add-header
- **block**: Block ads or other unwanted content
  - A block reason that should be given to the user.
```
{+block{No nasty stuff for you.}}
# Block and replace with "blocked" page
.nasty-stuff.example.com

{+block{Doubleclick banners.} +handle-as-image}
# Block and replace with image
.ad.doubleclick.net
.ads.r.us/banners/

{+block{Layered ads.} +handle-as-empty-document}
# Block and then ignore
adserver.example.net/.*\.js$
```
- change-x-forwarded-for: Improve privacy by not forwarding the source of the request in the HTTP headers.
  - "block" to delete the header.
  - "add" to create the header (or append the client's IP address to an already existing one).
- **filter**: 修改 html, js 内容
  - All instances of text-based type, most notably HTML and JavaScript, to which this action applies, can be filtered on-the-fly through the specified regular expression based substitutions. (Note: as of version 3.0.3 plain text documents are exempted from filtering, because web servers often use the text/plain MIME type for all files whose type they don't know.)
- limit-connect
- **redirect**: Redirect requests to other sites.
```
# Replace example.com's style sheet with another one
  { +redirect{http://localhost/css-replacements/example.com.css} }
  example.com/stylesheet\.css

  # Create a short, easy to remember nickname for a favorite site
  # (relies on the browser to accept and forward invalid URLs to Privoxy)
  { +redirect{https://www.privoxy.org/user-manual/actions-file.html} }
  a

  # Always use the expanded view for Undeadly.org articles
  # (Note the $ at the end of the URL pattern to make sure
  # the request for the rewritten URL isn't redirected as well)
  {+redirect{s@$@&mode=expanded@}}
  undeadly.org/cgi\?action=article&sid=\d*$

  # Redirect Google search requests to MSN
  {+redirect{s@^http://[^/]*/search\?q=([^&]*).*@http://search.msn.com/results.aspx?q=$1@}}
  .google.com/search

  # Redirect MSN search requests to Yahoo
  {+redirect{s@^http://[^/]*/results\.aspx\?q=([^&]*).*@http://search.yahoo.com/search?p=$1@}}
  search.msn.com//results\.aspx\?q=

  # Redirect http://example.com/&bla=fasel&toChange=foo (and any other value but "bar")
  # to       http://example.com/&bla=fasel&toChange=bar
  #
  # The URL pattern makes sure that the following request isn't redirected again.
  {+redirect{s@toChange=[^&]+@toChange=bar@}}
  example.com/.*toChange=(?!bar)

  # Add a shortcut to look up illumos bugs
  {+redirect{s@^http://i([0-9]+)/.*@https://www.illumos.org/issues/$1@}}
  # Redirected URL = http://i4974/
  # Redirect Destination = https://www.illumos.org/issues/4974
  i[0-9][0-9][0-9][0-9]*/

  # Redirect requests for the old Tor Hidden Service of the Privoxy website to the new one
  {+redirect{s@^http://jvauzb4sb3bwlsnc.onion/@http://l3tczdiiwoo63iwxty4lhs6p7eaxop5micbn7vbliydgv63x5zrrrfyd.onion/@}}
  jvauzb4sb3bwlsnc.onion/

  # Redirect remote requests for this manual
  # to the local version delivered by Privoxy
  {+redirect{s@^http://www@http://config@}}
  www.privoxy.org/user-manual/
```

### squid (失败)

!!! warning

    *p.s 没有搞定，就是代理不成功，不试了。*

[How to install a Squid server | Ubuntu](https://ubuntu.com/server/docs/how-to-install-a-squid-server)

- sudo systemctl restart squid.service 不知为何容易**卡半天**
- 配置 9000 行
  - **不过我们基本只需要关注两个配置**
    - http_port
    - http_access

配置文件需要讲究顺序，我们在 `http_access deny all` 前面添加额外的规则，在配置文件结尾加没有用
```
acl ustc_net src 222.195.72.0/24
acl ustc_net2 src 202.38.72.0/24

http_access allow ustc_net ustc_net2
```
#### 报错

不知为何，在 ryzen 上通过 localhost 设置可以访问，在其它机器上都不行。

curl 报错
```
* Uses proxy env variable https_proxy == 'http://114.214.236.72:11223'
* Trying 114.214.236.72:11223...
* TCP_NODELAY set 
* Connected to 114.214.236.72 (114.214.236.72) port 11223 (#0)
* allocate connect buffer!
* Establish HTTP proxy tunnel to www.youtube.com:443
> CONNECT www.youtube.com:443 HTTP/1.1
> Host: www.youtube.com:443 
> User-Agent: curl/7.68.0 
> Proxy-Connection: Keep-Alive
> 
< HTTP/1.1 403 Forbidden
< Server: squid/5.9 
< Mime-Version: 1.0 
< Date: Wed, 02 Oct 2024 06:52:32 GMT 
< Content-Type: text/html;charset=utf-8 
< Content-Length: 3496
< X-Squid-Error: ERR_ACCESS_DENIED 0
< Vary: Accept-Language 
< Content-Language: en
< X-Cache: MISS from ryzen
< X-Cache-Lookup: NONE from ryzen:11223 
< Via: 1.1 ryzen (squid/5.9)
< Connection: keep-alive
< 
* Received HTTP code 403 from proxy after CONNECT 
* CONNECT phase completed!
* Closing connection 0
curl: (56) Received HTTP code 403 from proxy after CONNECT 
```

squid 日志
```
1727852473.521    312 127.0.0.1 TCP_TUNNEL/200 534253 CONNECT www.youtube.com:443 - HIER_DIRECT/198.18.0.148 -
1727852480.354    488 127.0.0.1 TCP_TUNNEL/200 533027 CONNECT www.youtube.com:443 - HIER_DIRECT/198.18.0.148 -
1727852491.756   4547 127.0.0.1 TCP_TUNNEL/200 545250 CONNECT www.youtube.com:443 - HIER_DIRECT/198.18.0.148 -
1727852507.818    405 127.0.0.1 TCP_TUNNEL/200 531655 CONNECT www.youtube.com:443 - HIER_DIRECT/198.18.0.148 -
1727852631.171      0 192.168.35.254 TCP_DENIED/403 3856 CONNECT www.youtube.com:443 - HIER_NONE/- text/html
1727852697.691      0 192.168.35.254 NONE_NONE/000 0 - error:transaction-end-before-headers - HIER_NONE/- -
1727853038.964      0 192.168.35.254 TCP_DENIED/403 3856 CONNECT www.youtube.com:443 - HIER_NONE/- text/html
```

## Socks5

### dante

- 优点
  - 支持用户名密码验证
  - 支持访问控制：**通过 rule 控制哪些客户端可以连接 server，以及客户端可以 request 哪些地址**
  - 文档、配置文件注释清晰易读
- 缺点
  - 不支持 ipv6
  - 配置增加了很多东西，所以配置相对复杂

[How To Setup SOCKS5 Proxy Server using Dante on Ubuntu 16.04 (github.com)](https://gist.github.com/4faramita/431f92a0fca1b8f0239ac4947ea2122b)

安装

```
dante-server
```

#### 配置

- set socksmethod to 'none' instead of 'username' if you want to disable auth.

```
internal: 0.0.0.0 port = 11223
external: 192.168.35.2

#clientmethod: none
socksmethod: none
user.privileged: root
user.unprivileged: nobody

user.libwrap: nobody
client pass {
    from: 0.0.0.0/0 to: 0.0.0.0/0
    log: error connect disconnect
}
socks pass {
    from: 0.0.0.0/0 to: 0.0.0.0/0
    log: error connect disconnect
}
```


```
# The config file is divided into three parts;
#    1) server settings
#    2) rules
#    3) routes
```

server setting 部分可以配置：

- 监听地址，出口地址
- 验证方法

- clientmethod:
  - The  default  value  for this keyword is all methods that may be necessary for the later socks-based authentication methods, as specified as values to the global socksmethod keyword.  **Normally you should not need to set this keyword, as Dante will set it to the correct value by it self.**
- socksmethod
  - Supported values are bsdauth, gssapi, none, pam.any, pam.address, pam.username, rfc931, and username

设置 socksmethod 为 username 后，直接访问会报错。需要设置为 `socks5://user:password@proxyhost:port`

```
curl: (7) No authentication method was acceptable. (It is quite likely that the SOCKS5 server wanted a username/password, since none was supplied to the server on this connection.)
```


rule 部分用于实现访问控制，决定哪些 client 可以连接 socks，也决定 client 能够访问哪些内容。

```
# 允许所有 client，后面的 to 并不是目标地址，而是 danted 接收到包的接口地址
client pass {
    from: 0.0.0.0/0 to: 0.0.0.0/0
    log: error connect disconnect
}

# the people at the 172.16.0.0/12 are bad, no one should talk to them.
# log the connect request and also provide an example on how to
# interact with libwrap.
#socks block {
#        from: 0.0.0.0/0 to: 172.16.0.0/12
#        libwrap: spawn finger @%a
#        log: connect error
#}
```

man 中貌似没有关于 route 的介绍，但是实际上很简单，可以用于实现某些地址使用另一个 socks server 再次转发
```
# route all http connects via an upstream socks server, aka "server-chaining".
#route {
# from: 10.0.0.0/8 to: 0.0.0.0/0 port = http via: socks.example.net port = socks
#}
```

#### man 手册

`man 5 danted.conf`
##### authentication methods

- none
  - This method requires no form of authentication.
- **username**
  - This method requires the client to provide a username and password.  This information must match the username and password given in the system password file.
- gssapi
  - This method requires the setup of a Kerberos environment and can provide strong encryption and authentication, depending on the gssapi settings you choose.
- rfc931
  - This method requires the host the socks client runs on to provide a rfc931 ("ident") username for the client.  This username match a username given in the system password file.
- **pam.address**
  - IP-based (rhosts) PAM authentication.
- pam.any
  - Will try to match against any type of PAM authentication, depending on the information that is currently available.  Normally of limited use, and you should instead set the pam-based method(s) you actually want.
- **pam.username**
  - Username/password-based  PAM authentication.  Similar to the method username, but the information is passed to the PAM subsystem for authentication, rather than Dante using the system password file directly.  When using PAM, be wary of memory leakages and other bugs in the external PAM library Dante will have to use on your platform.
- bsdauth
  - This method requires the available client data to be verified by the BSD Authentication system.  Similar to the method username, but passed to the BSD authentication system instead.
##### rule

有点像防火墙规则，决定哪些 client 可以连接 socks，也决定 client 能够访问哪些内容。

**两种规则**

- **client rule**: are used to see if the client is allowed to connect to the Dante server
  - These rules will start with `client pass` for a rule that allows the client, or `client block` for a rule that blocks the client
  - It is recommended that the client-rules do not use hostnames but only IP-addresses, both for security and **performance** reasons.  These rules **operate at the TCP level**.
- socks-rules: prefixed with socks and operate at the socks protocol level
  - These rules will start with `socks pass` for a rule that allows the client, or `socks block` for a rule that blocks the client.
  - 性能变得不那么重要，但是仍然推荐使用

rule 由 `client pass/block` 或者 `socks pass/block` 开始，内容主要是匹配的 condition 相关的关键词（不过也有 log 这种 action 做一些额外操作）

示例
```
client pass {
    from: 0.0.0.0/0 to: 0.0.0.0/0
    log: error connect disconnect
}
```

- condition
  - clientcompatibility, clientmethod, command, **from**, group, socksmethod, protocol, proxyprotocol, **to**, user
  - **port**: Parameter to from, to and via.  Accepts the keywords eq/=, neq/!=, ge/>=, le/<=, gt/>, lt/< followed by a number.  A port range can also be given as "port <start #> - <end #>"
- action
  - bandwidth, libwrap, log, session, **redirect**, timeout.connect, timeout.negotiate, timeout.io, timeout.tcp_fin_wait, and udp.portrange.

from, to 含义

- `from` refers to the clients address
  - In the client-rule context, `to` means the address the request is accepted on, i.e., a address the Dante server listens on.
  - In the socks-rule context, `to` means the client's destination address, as expressed in the client's socks request.  I.e., the address the Dante server should connect to (for TCP sessions) or send packets to (for UDP session) on behalf of the client.
- **first match is best match** basis.

##### 其它功能

- SESSION
  - The session keyword can be used any any rule to limit the number of active sessions and the rate at which they are established.
- TRAFFIC MONITORING
  - The Dante server can be configured to monitor the traffic passing through it, and trigger alarms based on the observed network traffic
### ss-local + ss-server

自己最熟悉的工具，因此配置起来很容易。

把 local 和 server 分别部署在 GFW 的两侧是正常用法，部署在同一台机器上则只是利用了 local 的 socks5 代理功能。

- 优点
  - 每个配置选项都知道含义
- 缺点
  - local 侧不支持用户密码验证，也不支持访问控制
  - systemd service 默认只有 ss-server 的，没有 ss-local 的

```
sudo vim /etc/shadowsocks-libev/server.json
{
    "server":["127.0.0.1"],
    "mode":"tcp_and_udp",
    "server_port": 1080,
    "local_ipv4_address": "192.168.35.2",
    "nameserver": "192.168.35.1",
    "timeout":86400,
    "method":"aes-256-cfb",
    "password": "abcd4567",
    "fast_open": true
}

# local
sudo vim /etc/shadowsocks-libev/local.json
{
    "server":"127.0.0.1",
    "server_port":1080,
    "local_address": "0.0.0.0",
    "local_port":11223,
    "password":"abcd4567",
    "timeout":300,
    "method":"aes-256-cfb",
    "fast_open": false
}

```

```
/usr/bin/ss-server -c /etc/shadowsocks-libev/server.json
/usr/bin/ss-local -c /etc/shadowsocks-libev/local.json
```