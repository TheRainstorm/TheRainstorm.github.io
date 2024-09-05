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

- Pico 视频多人观影
  - 播放内容
    - Pico 视频内的资源
    - 各类支持 tv 投屏的应用。特别的，支持网盘（因此可以投用户下载的资源）
  - 优点
    - ~~有简易的 avatar~~（2024/06 Pico 更新 Avatar SDK v2.0.0 后，社区可以上传自定义的模型，数量非常丰富。比如全员使用假面骑士形象看特摄）
    - 支持若干场景切换：电影院、沙滩等
    - 投屏支持 4K，**清晰度比较高**
    - **头戴端应用，不需要 PC**
    - 支持 3d 视频
  - 缺点
    - 只能 DLNA 投屏少数白名单网站：B 站、爱奇艺（目前不支持，之后会支持），百度、~~阿里（别用了，会被永久封号）~~、夸克网盘等。**并且官方没有将其公布在网上**。
    - 有内容审查（虽然也算不上缺点，但确实自由度没有那么高）
    - **需要网盘会员才有好体验**：网盘投屏方式不充对应软件会员，基本只能 720p 投屏
    - **不支持字幕**，视频必须提前将字幕烧录到画面中
    - 没测：不知道是否支持音轨切换

- VRChat
  - 播放内容
    - 视频直链（类似于`http://something.com/video.mp4`）
    - 各种流媒体网站（如`https://youtube.com/watch?v=VIDEOID`，原理是使用 yt-dlp 工具解析出视频直链）：包含 B 站、youtube、twitch直播等
  - 优点
    - 不只是看电影；无数的 avatar 和 无数的 world（场景）可以选择，在场景中可以有丰富的交互
    - 直链意味着可以自己使用服务器 host 想要分享的视频
    - **没有审查**。默认有白名单机制，非[白名单的域名](https://creators.vrchat.com/worlds/udon/video-players/www-whitelist/)默认不会播放，但是用户可以手动关闭白名单
  - 缺点
    - 观感不太清晰
      - VRChat 本身渲染分辨率的缘故，需要很高端的显卡才能提高分辨率
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

- 一类是应用厂商提供串流服务器的。bigscreen 就属于这种，它的最大优势是用户可以分享自己的屏幕。过程其实是房主将自己的画面推流到 bigscreen 服务器，其它用户再从 bigscreen 获得画面。这本质上是一种**直播**。
- 另一类就是像 Pico 视频和 VRChat 这种不提供串流服务器的。它们本身不需要服务器存储视频，用户都是通过视频链接访问**已有的视频网站**，因此成本更低些。

理论上最方便最强大的肯定是 bigscreen 这种，但是由于串流服务器存储和带宽的高昂成本，免费用户必然会受到许多限制。因此我觉得更实际的还是后者。其实对于观看大部分正规正版资源，pico 视频已经没什么问题（要么观看 Pico 视频自带的资源，要么使用其它软件投屏）。然而因为国内的审查政策，导致很多即使正规的内容国内平台不一定引进，引进了也可能删减。因此 VRChat 更加开放这一点还是不可缺少的。

视频链接又可以分为两类

- 一类是**视频直链**，也就是链接直接指向 .mp4 或者 .webm视频文件。而要取得这样的链接有许多方法
  - 自己购买服务器存放视频，并创建 HTTP 服务器提供访问（比如使用 nginx）
  - 使用 youtube，bilibili 等流媒体平台的链接。这些链接虽然不指向视频文件，但是 VRC 播放器内部会使用 yt-dlp 工具解析出其中的视频直链。
  - 使用云盘存储视频，并获得直链。虽然云盘通常不提供视频直链，甚至会打击获取直链的插件（比如百度网盘）。但是还是有一些云服务商提供了直链的功能，比如 googledrive
  - 使用一些视频托管网站比如 Vimeo（VRC 官方支持的网站）。用户上传视频到网站，网站提供视频链接。同样，免费用户一般有存储空间限制。
- 另一类是**直播链接**。直播链接通常采用 HLS 协议，链接指向一个 m3u8 文件，文件存储了切片后的视频直链（通常封装成 ts 格式）。VRC 播放器（如 USharpVideo）都支持 m3u8 链接的播放，需要在界面选择为 **Streaming**。
  - 直播链接和视频直链的区别在于，视频直链的文件内容是固定的，而直播链接中 m3u8 内容是动态生成的。
  - 以 B 站直播为例，直播者通过 OBS 等软件将画面编码后，通过 RTMP 协议**推流**到 B 站的服务器（ `rtmp://dl.live-send.acg.tv/live-dl`），B 站可以对视频进行存储（也就是直播回放功能），同时提供 HLS 访问。观看者使用浏览器通过 HLS 协议从 B 站服务器获取直播内容。

以下是它们优缺点的介绍

视频直链

- 优点
  - 简单直接
  - 自己 host 简单，只需要搭建一个 HTTP 服务器即可
- 缺点
  - 为了获得最好的兼容性，对视频格式有许多要求。封装格式建议使用 mp4，编码格式建议使用 h264。字幕建议直接烧录到画面中。
  - 无法随时调节视频码率。由于播放器是直接请求视频文件，因此对网络带宽有很高要求。对于下载的码率很高的电影文件，直接播放基本上是不可能的。这也是为什么如今各种云盘为了提供在线播放功能，**会对用户上传的视频进行转码**，保存 480p, 720p, 1080p 等不同分辨率清晰度的版本。而直播不同，直播源可以随时调节码率

直播链接

- 优点
  - 兼容性最好，由于直接串流电脑画面，因此使用电脑上的播放器基本可以播放任意视频文件，字幕切换、多音轨都不是问题。
  - 按需调节码率
- 缺点
  - VRC 中无法随时调节播放进度，需要电脑上操作
  - 画质不如原始视频文件。直播其实是在对画面进行实时编码，通常使用核显或者独显加速。而压制组压制的视频资源是使用 CPU 花费大量时间压出来的，会对各种参数进行调节，二者质量上肯定是后者更高。而且直播通常采用 CBR（固定码率） 或者 VBR（可变码率）编码方式。优化的是码率，而不是画质，因此画质也是不如使用 CRF（Constant Rate Factor）压出来的高码率视频。
    - 但是其实只要抛弃画质有损失这样的想法，直播编码出来的画面是足够观看电影的。

## 方案介绍

最后经过研究，围绕 VRChat 确实有许多方案。最简单的，使用 twitch 直播电脑画面，当然同样会遇到码率限制等问题。所以最好的还是利用自己的上传带宽，因此可以**在家宽上搭建一个 HLS 的服务器**。绑定域名，提供给外网访问。可以使用 **OBS** 将电脑屏幕、视频播放器等画面推流到自己的 HLS 服务器上。

- 优点
  - 能够播放自己下载的内容，不需要经过网盘
  - 基本不会存在视频兼容性问题，因为推流的是电脑画面
- 缺点
  - **国内可能有法律问题**？相当于在家宽上搭建直播服务器
  - **上传带宽受限**（国内家宽目前上行普遍只有20-40Mbps 水平），按照 2.5Mbps 的码率，最多只能 10 人同时观看。想要 8Mbps 码率，就只能 4 人观看了。
  - 没有 cdn 优化，不一定每个地方都有很好的播放体验

<!-- more -->

## OBS + HLS 服务器 + VRC 方案

!!! note "方案变化"

      其实我原本想的是使用 ffmpeg 将视频转码后推送到 HLS 服务器。并且在克服一大堆问题如音频格式、字幕问题后终于实现了可用的 ffmpeg 命令行参数。然后在写这篇博客时突然在 github 上找到了一个 2019 年的仓库介绍使用 VRC 基于 HLS 来观看视频的方案。方案里用的 OBS 进行推流，我才意识到 OBS “火箭”都造好了，我为啥要用 ffmpeg 在这造自行车呢:)

由于 [mekanoe/VRC_HLS: Solution & guide for streaming anything into VRChat. (github.com)](https://github.com/mekanoe/VRC_HLS) 解释的很详细了，因此这里就不再详细解释了。

### h264_nvenc 模式选择

- CBR (Constant Bit Rate)
  - 恒定比特率：在整个视频编码过程中，码率保持恒定。
  - 特点
    - 保持稳定的码率，带宽利用率可预测。
    - 适用于带宽限制严格的环境，如直播。
    - 可能导致在复杂场景中画质下降，因为码率不会动态调整。
  - 使用场景：
    - **直播**：由于直播通常需要稳定的码率来保证流畅传输，CBR 是最佳选择。
- CQP (Constant QP)：恒定量化参数：不控制比特率，而是控制量化参数（QP），以保持恒定的视觉质量。
  - 特点：
    - 质量恒定，码率根据内容复杂度变化。
    - 高质量编码，但无法预测输出文件大小或带宽需求。
    - 不适合实时传输或带宽受限场景。
  - 使用场景：
    - **本地存储**：适用于需要高质量编码的场景，如视频存档或后期处理。
- VBR (Variable Bit Rate)
  - 可变比特率：允许比特率根据视频内容的复杂度动态调整，在简单场景中降低码率，在复杂场景中增加码率。
  - 特点：
    - 质量与文件大小之间的平衡。
    - 提高视频复杂场景的画质，同时在简单场景中节省带宽。
    - 适合带宽相对宽松但希望优化传输质量的场景。
  - 使用场景：
    - 预录视频：适用于希望优化文件大小和画质的视频录制。

### 码率设置

[Choose live encoder settings, bitrates, and resolutions - YouTube Help (google.com)](https://support.google.com/youtube/answer/2853702?hl=en)

![](https://raw.githubusercontent.com/TheRainstorm/.image-bed/main/20240526101525.png)

1080p@60 推荐 12 Mbps

### VRC 地图

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

- VRC player allowlist： [Video Player Allowlist | VRChat Creation](https://creators.vrchat.com/worlds/udon/video-players/www-whitelist/)
- Fluid，可以在各个地方打开浏览器，也支持多人模式: [Fluid](https://fluid.so/)
- 推荐了各种 VR 观影方案，以及 VRC 地图：[The Best Ways To Watch Movies in VR (with friends) for Free! – VR Wave (vr-wave.store)](https://www.vr-wave.store/blogs/virtual-reality-prescription-lenses/how-to-watch-movies-in-vr-with-friends-draft)
  - 其它方案
    - Horizon Words
    - Watch Party - Meta Horizon Home
- VRC + HLS 教程：[mekanoe/VRC_HLS: Solution & guide for streaming anything into VRChat. (github.com)](https://github.com/mekanoe/VRC_HLS)
- streaming 友好 ffmpeg 编码选项
  - faststart：视频可以立即播放，而不是等到文件下载结束。[Fastest way to add -movflags +faststart to an MP4 using FFMPEG, leaving everything else as-is - Stack Overflow](https://stackoverflow.com/questions/50914503/fastest-way-to-add-movflags-faststart-to-an-mp4-using-ffmpeg-leaving-everythi)
  - 其它工具还支持 interlaving audio and video: [Fragmentation, segmentation, splitting and interleaving · gpac/gpac Wiki (github.com)](https://github.com/gpac/gpac/wiki/Fragmentation,-segmentation,-splitting-and-interleaving)
- 支持 3d 视频的播放器？：[ProTV 2.3 for VRChat (Udon Video Player) [Free DL available] (gumroad.com)](https://architechvr.gumroad.com/l/protv)
- [USharpVideo](https://github.com/MerlinVR/USharpVideo)是前端，后端基于 AVPro ?[AVPro Only · MerlinVR/USharpVideo Wiki (github.com)](https://github.com/MerlinVR/USharpVideo/wiki/avpro-only)

```
public VRCUnityVideoPlayer unityVideo;
public VRCAVProVideoPlayer avProVideo;
```
