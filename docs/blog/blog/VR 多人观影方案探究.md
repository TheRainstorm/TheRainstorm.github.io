---
title: VR 多人观影
date: 2024-05-25 18:49:05
tags:
  - vr
  - vrchat
  - hls
categories:
  - 博客
---
VR 比较常见的一个功能便是拿来看看视频，巨大的屏幕以及可以切换的各种拟真场景，都可以带来非常高的沉浸感。而多人观影，则使得这个功能更近一步。在多人观影应用中，玩家可以创建虚拟房间，别人可以加入这个房间观看同一部电影。在虚拟场景中，玩家可以看到对面的虚拟形象做出的各种动作，也可以听到对面带有方位感的立体的声音，让人感觉对方仿佛就在眼前一样。

对我来说，VR 多人观影的最大优点可能是可以突破时间空间的限制，加强人与人之间的连接。毕竟现实中想要和好友特别是异地的好友一起看电影实在太难了，而在 VR 中却可以轻易做到。
我相信，这种加强人与人的链接，必然是 VR 未来发展的很重要的一个方向。（比如在 VRChat 中，玩家能做到的不仅是一起观影，还能一起玩游戏、一起逛图甚至一起陪伴睡觉。确实能瞥见一点元宇宙的影子）

回到正题，由于目前 VR 还处于一个开拓区，许多应用都没有完全明确的形态。针对 VR 多人观影，并没有非常成熟的应用，不同软件侧重的功能不同。以下是我对试过的一些方案的总结
## 现有方案总结

- pico 视频多人观影
  - 播放内容
    - pico 视频内的资源
    - 各类支持 tv 投屏的应用。特别的，支持网盘（因此可以投用户下载的资源）
  - 优点
    - 有简易的 avatar
    - 支持若干场景切换：电影院、沙滩等
    - 投屏支持 4K，**清晰度比较高**
    - 没测：不知道是否支持字幕、音轨切换
    - **头戴端应用，不需要 PC**
    - 支持 3d 视频
  - 缺点
    - 只能 DLNA 投屏少数白名单网站：B 站、爱奇艺（目前不支持，之后会支持），百度、阿里、夸克网盘等。**并且官方没有将其公布在网上**。
    - 有内容审查（虽然也算不上缺点，但确实自由度没有那么高）
    - **需要网盘会员才有好体验**：网盘投屏方式不充对应软件会员，基本只能 720p 投屏

- vrchat
  - 播放内容
    - 视频直链（类似于`http://something.com/video.mp4`）
    - 各种流媒体网站（如`https://youtube.com/watch?v=VIDEOID`，原理是使用 yt-dlp 工具解析出视频直链）：包含 B 站、youtube、twitch直播等
  - 优点
    - 不只是看电影；无数的 avatar 和 无数的 world（场景）可以选择，在场景中可以有丰富的交互
    - 直链意味着可以自己使用服务器 host 想要分享的视频
    - **没有审查**。默认有白名单机制，非[白名单的域名](https://creators.vrchat.com/worlds/udon/video-players/www-whitelist/)默认不会播放，但是用户可以手动关闭白名单
  - 缺点
    - 观感不太清晰
      - vrchat 本身渲染分辨率的缘故，需要很高端的显卡才能提高分辨率
      - ~~播放器貌似本身也限制分辨率，只有 480p, 720p, 1080p 可选~~（感觉可能只是一个外观按钮，毕竟自己服务器 streaming 的内容，码率等都是服务端控制的，播放器端不应该会再转码一次）
    - 播放器不完善
      - 不支持外挂字幕，只支持将字幕烧录到视频中。（有项目支持了，但是我没成功）
      - 不支持切换音轨
      - *p.s. VLC 播放器使用同样的 url 是均支持的*，说明问题是可以解决的，所以未来可期
    - 目前没有 3d 的播放器，只能分享 2d 视频

- bigscreen：一个专门用于多人观影的软件[Steam 上的 Bigscreen Beta (steampowered.com)](https://store.steampowered.com/app/457550/Bigscreen_Beta/)
  - 播放内容
    - 电脑屏幕
    - 电脑本地视频
    - youtube，twitch 等内容
  - 优点
    - 播放内容很开放，**很容易播放自己下载的内容**。甚至分享电脑屏幕
    - 场景很丰富：有付费场景和免费场景（其中一个教室场景观感很不错）
    - 支持 3d 视频
  - 缺点
    - 清晰度还是低了点，最高码率为 5m

其实从原理上，上面应用可以分为两类。

- 一类是应用厂商提供串流服务器的。bigscreen 就属于这种，它的最大优势是用户可以分享自己的屏幕。过程其实是房主将自己的画面推流到 bigscreen 服务器，其它用户再从 bigscreen 获得画面。这本质上是一种直播。
- 另一类就是像 pico 视频和 vrchat 这种不提供串流服务器的。它们本身不需要服务器存储视频，用户都是通过视频链接访问已有的视频网站，因此成本更低些。

理论上最方便最强大的肯定是 bigscreen 这种，但是由于串流服务器存储和带宽的高昂成本，免费用户必然会受到许多限制。

因此我觉得更实际的还是后面这种。其实对于观看大部分正规正版资源，pico 视频已经没什么问题。然而因为国内的审查政策，导致很多即使正规的内容国内平台不一定引进，引进了也可能删减。因此 vrchat 更加开放这一点还是不可缺少的。

## 方案介绍

最后经过研究，围绕 vrchat 确实有许多方案。最简单的，使用 twitch 直播电脑画面，当然同样会遇到码率限制等问题。所以最好的还是利用自己的上传带宽，因此可以**在家宽上搭建一个 HLS 的服务器**。绑定域名，提供给外网访问。可以使用 OBS 推流将电脑屏幕、视频播放器等画面推流到自己的 HLS 服务器上。

- 优点
  - 能够播放自己下载的内容，不需要经过网盘
  - 基本不会存在视频兼容性问题，因为推流的是电脑画面
- 缺点
  - **国内可能有法律问题**？相当于在家宽上搭建直播服务器
  - **上传带宽受限**（国内家宽目前上行普遍只有20-30M 水平），按照 2.5M 的码率，最多只能 10 人同时观看。想要 8M 码率，就只能 4 人观看了。
  - 没有 cdn 优化，不一定每个地方都有很好的播放体验

<!-- more -->

## OBS + HLS 服务器 + VRC 方案

!!! note "方案变化"

      其实我原本想的是使用 ffmpeg 将视频转码后推送到 HLS 服务器。并且在克服一大堆问题如音频格式、字幕问题后终于实现了可用的 ffmpeg 命令行参数。然后在写这篇博客时突然在 github 上找到了一个 2019 年的仓库介绍使用 VRC 基于 HLS 来观看视频的方案。方案里用的 OBS 进行推流，我才意识到 OBS “火箭”都造好了，我为啥要用 ffmpeg 在这造自行车呢:)

由于 VRC_HLS 解释的很详细了，因此这里就不再详细解释了。

### vrc 地图

推荐来自[The Best Ways To Watch Movies in VR (with friends) for Free! – VR Wave (vr-wave.store)](https://www.vr-wave.store/blogs/virtual-reality-prescription-lenses/how-to-watch-movies-in-vr-with-friends-draft)
#### Movie & Chill

![Movie & Chill](https://cdn.shopify.com/s/files/1/0415/3324/3552/files/vlcsnap-2022-11-17-15h48m36s604_1024x1024.png?v=1668728955)
#### Yet Another Movie Theater: Renewed

![](https://cdn.shopify.com/s/files/1/0415/3324/3552/files/vlcsnap-2022-11-17-15h50m56s869_1024x1024.png?v=1668729113)
#### Sovren’s Chill Home


![Sovren’s Chill Home](https://cdn.shopify.com/s/files/1/0415/3324/3552/files/vlcsnap-2022-11-17-15h54m40s931_1024x1024.png?v=1668729292)

#### Campsite Movie Night

![Campsite Movie Night](https://cdn.shopify.com/s/files/1/0415/3324/3552/files/vlcsnap-2022-11-17-15h56m08s989_1024x1024.png?v=1668729380)
## 参考资料

- Fluid，可以在各个地方打开浏览器，也支持多人模式: [Fluid](https://fluid.so/)
- 推荐了各种 VR 观影方案，以及 VRC 地图：[The Best Ways To Watch Movies in VR (with friends) for Free! – VR Wave (vr-wave.store)](https://www.vr-wave.store/blogs/virtual-reality-prescription-lenses/how-to-watch-movies-in-vr-with-friends-draft)
  - 其它方案
    - Horizon Words
    - Watch Party - Meta Horizon Home
- VRC + HLS 教程：[mekanoe/VRC_HLS: Solution & guide for streaming anything into VRChat. (github.com)](https://github.com/mekanoe/VRC_HLS)


