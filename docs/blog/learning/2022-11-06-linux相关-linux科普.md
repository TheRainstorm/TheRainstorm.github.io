---
title: linux 相关-linux 科普
date: 2022-11-06 18:14:50
tags:
  - tty
categories:
  - 学习笔记
---
linux 相关
<!-- more -->
# linux 科普

## tty, pts

- tty 表示终端 (terminal or console) 的统称。tty(tele typerwriter) 电传打字机为早期电脑的输入输出设备，后面被显示器和键盘取代。
  - ctrl alt + F1-F6 对应 6 个终端
  - ctrl alt + F7 对应图形化界面
- pts(pseudo terminal slave) 表示伪终端。是一个程序（终端仿真器 teminal emulators）

```bash
who #查看当前所有登录用户及终端
➜  ~ who
yfy      :1           2022-10-24 14:26 (:1)
yfy      pts/1        2022-10-16 15:36 (tmux(1158265).%0)
yfy      pts/2        2022-10-24 14:43 (192.168.1.180)
yfy      pts/3        2022-10-23 18:57 (tmux(1158265).%5)
yfy      pts/4        2022-10-16 15:37 (tmux(1158265).%2)
yfy      pts/6        2022-10-16 15:38 (tmux(1158265).%3)
yfy      pts/7        2022-10-16 15:38 (tmux(1158265).%4)
yfy      pts/12       2022-10-24 00:36 (tmux(1158265).%0)
who -m # 查看当前用户

echo "hello" > /dev/pty/x   #直接给对应终端发送消息
```
