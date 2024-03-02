---
title: retroarch 配置
date: 2022-09-29 00:56:52
tags:
- retroarch
categories:
- 软件工具
---

[RetroArch Starter Guide – Retro Game Corps](https://retrogamecorps.com/2022/02/28/retroarch-starter-guide/)

retroarch 是一个模拟器前端，不同的模拟器以 core 的形式嵌入 retro。retroarch 相对于单独的模拟器来说好处如下

- 跨平台。retroarch 支持非常多的平台。由于 core 是动态链接库的形式嵌入 retroarch 的，相当于解决了不同 core 的跨平台问题。
- 支持全局的按键映射。不用为每个模拟器设置手柄，快捷键等等配置。
- shader and filters。可以实现一些特别的视觉效果，比如

<!-- more -->

## 参考

[RetroArch 街机模拟教程【亲测有效】 - 简书 (jianshu.com)](https://www.jianshu.com/p/60cc555e9289)
[EmuELEC 中文网 - EmuELEC 使用指南五之街机模拟器使用简介](https://www.emuelec.cn/85.html)
[EmuELEC 中文网 - EmuELEC 使用指南一之新手快速上手指南](https://www.emuelec.cn/35.html)

## 平台列表

```json
name_list = [\
    "(1989) NEC - PC Engine",

    "(1988) Sega - MegaDrive",
    "(1994) Sega - Saturn",
    "(1998) Sega - DreamCast",

    "(1989) Nintendo - GB",
    "(1998) Nintendo - GBC",
    "(2001) Nintendo - GBA",
    "(2004) Nintendo - NDS",
    "(2011) Nintendo - 3DS",

    "(1983) Nintendo - FC",
    "(1990) Nintendo - SFC",
    "(1996) Nintendo - N64",
    #(2001) "Nintendo - NGC",
    "(2006) Nintendo - Wii",
    # "(2012) Nintendo - WiiU",

    "(2004) Sony - PSP",
    # "(2011) Sony - PSV",
    "(1994) Sony - PS1",
    "(2000) Sony - PS2",
    # "(2006) Sony - PS3",
    # "(2013) Sony - PS4",
]
```

世嘉[List of Sega video game consoles - Wikipedia](https://en.wikipedia.org/wiki/List_of_Sega_video_game_consoles)
主机

- MD: Mega Drive, 1988
- SS: Sega Saturn, 1994
- DC: Dreamcast, 1998, 6

索尼[PlayStation - Wikipedia](https://en.wikipedia.org/wiki/PlayStation)
掌机

- PSP: 2004, 7
- PSV: 2011
主机
- PS1: 1994, 5
- PS2: 2000, 6
- PS3: 2006, 7
- PS4: 2013, 8

任天堂[Nintendo video game consoles - Wikipedia](https://en.wikipedia.org/wiki/Nintendo_video_game_consoles)
掌机
GB(1989), GBC(1998), GBA(2001)

NDS/DS(2004)
3DS(2011)

主机
FC/NES:1983
SFC/SNES: 1990
N64: 1996
NGC/game cube: 2001
WII 2006
WIIU 2012
Switch

[TurboGrafx-16 - Wikipedia](https://en.wikipedia.org/wiki/TurboGrafx-16)
  NEC 1989
  Japan in 1987 and in North America in 1989.

街机

- neogeo: snk, 拳皇，合金弹头
- cps1,2,3
- mame

- oldman

  ```
  SFC  201M x
  GBA_499 3.6G
  
  NGC  15G
  Wii  120G
  
  SS  7.9G
  DC  17.3G x
  
  PS1  37.1G
  PS2  302G/20G
  PSP  319G/10.4G
  ```

- retroarch 整合包
  
  ```
  FC  66M 
  SFC  619M
  GB[C] 100M
  GBA  2.26G 
  NDS  3.91G
  3DS  25.6G
  N64  637M
  NGC  4.53G
  Wii  53.4G
  WiiU
  
  MD  417M
  SS  4.73G
  DC  22G
  
  PS1  18.8G
  PS2  59.5G
  PSP  21.5G
  
  PCE* 1.49G
  3DO  3.56G
  Aracade 4.36G
  ```
