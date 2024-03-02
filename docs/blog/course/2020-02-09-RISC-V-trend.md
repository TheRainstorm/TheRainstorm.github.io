---
title: RISC-V trend
date: 2020-01-07 22:24:46
tags:
- risc-v
categories:
- 课程笔记
description: 计算机组成原理的期末作业，在 RISC-V 精简指令集、异构计算等领域中选择一个并查阅相关资料写一篇报告。
---

# RISC-V 报告

author: 计科卓越班 袁福焱 20174260

## 0. 导言

RISC-V 是 21 世纪诞生的一种完全开放的计算机精简指令集，可应用于小到嵌入式系统大到高性能处理器等广泛领域。RISC-V 充分汲取了许多指令集的实践经验，具有非常多的优点。并且它完全开放，采用 BSD 开源协议——全世界任何公司、大学、个人都可以自由免费地使用 RISC-V 指令集构建自己的系统。

本报告第一部分讲述 RISC-V 的几个主要特点与优势，第二部分介绍 RISC-V 的目前已构建建的生态系统。最后一部分，谈论 RISC-V 在推动开源硬件中起到的作用。

## 1. RISC-V 的特点

### 1.1 指令集模块化

以往的指令集为了实现兼容，往往采用增量扩展的方法。即新的处理器不仅要实现新的扩展，还必需要实现过去所有的扩展。如典型的 x86 架构，其中许多指令早已失效，但为了兼容性却必须实现，这导致硬件实现变得越来越复杂。RISC-V 按照功能将指令集分为很多个模块。其中 I 模块为基础整型指令集，这是 RISC-V 要求必须实现的指令集，并且永远不会发生改变。只要实现了该指令集便可以运行完整的基于 RISC-V 的软件。这样，RISC-V 在扩展时便不再会像 x86 那样背上沉重的历史包裹。编译器也可以在保证兼容的基础上，根据已实现的扩展，选择性地生成更高效的代码。

### 1.2 回避以往的设计缺陷

目前主流的指令集有 x86, ARM, MIPS 等。其中 x86 为复杂指令集 (RISC)，于 1978 年诞生。而 ARM, MIPS 为精简指令集 (RISC)，都是 1986 年诞生的。从计算机体系结构的发展上来看，RISC 由于简洁性，能够更加充分地利用现代微体系结构中的流水线、分支预测、cache 等技术，因此比 CISC 更加高效。因此，诞生于 21 世纪 (2004) 的 RISC-V，必然也是精简指令集。并且，由于有了前面指令的经验，RISC-V 吸收了以往指令集的优点，并回避了以往指令集的一些缺陷。优点如，RISC-V 有 32 个通用寄存器，有专门的 0 寄存器。使用专门的移位指令来处理移位操作。使用 load/store 指令访问内存。跳转指令不使用条件码。缺陷则如，RISC-V 废弃了 MIPS 中的分支延迟槽 (有利于架构和实现的分离)，立即数只进行有符号扩展，算数运算不抛出异常 (通过软件判断)，更规整的指令格式（源及目的字段位置固定），整数乘除法可选 (简化了基础实现)。

### 1.3 完全开放

RISC-V 采用 BSD 开源协议，任何人都可以自由免费地使用 RISC-V。其他指令集如 x86 是完全闭源的，只有 intel 和 AMD 等少数公司能够基于 x86 架构生产产品。而 ARM 和 MIPS 都采用授权的方式，通过卖授权的方式盈利，其中 ARM 的授权费则十分昂贵。RISC-V 如今由 RISC-V 基金会维护，任何公司只要愿意每年支付一笔会员费即可成为会员，会员可以参与到 RISC-V 之后标准的制定中。RISC-V 也因此真正成为一个开放的指令集，不会因为任何一个公司的起伏而受到影响。

## 2. RISC-V 的生态

以下内容引用自[开放指令集与开源芯片进展报告-v1p1](http://crva.io/documents/OpenISA-OpenSourceChip-Report.pdf)

> 2011 年，加州大学伯克利分校发布了开放指令集 RISC-V，并很快建立起一个开源软硬件生态系统。截止 2019 年 1 月，已有包括 Google、NVidia 等在内的 200 多个公司和高校在资助和参与 RISC-V 项目。其中，部分企业已经开始将 RISC-V 集成到产品中。例如全球第一大硬盘厂商西部数据（Western Digital）最近宣布将把每年各类存储产品中嵌入的 10 亿个处理器核换成 RISC-V；Google 利用 RISC-V 来实现主板控制模块；NVidia 也将在 GPU 上引入 RISC-V 等。此外，国内阿里巴巴、华为、联想等公司都在逐步研究各自的 RISC-V 实现；上海市将 RISC-V 列为重点扶持项目；印度政府也正在大力资助基于 RISC-V 的处理器项目，使 RISC-V 成为了印度的事实国家指令集。

由此可见，RISC-V 国内外的兴起使得目前 RISC-V 的生态已经比较完善了。

## 3. 之于构建开放硬件生态的意义

2019 年度国际计算机体系结构旗舰会议 ISCA 于 6 月在美国亚利桑那州凤凰城召开，会议的主题即是“面向下一代计算的敏捷开放硬件（Agile and Open Hardware for Next-Generation Computing）”。由此可见开放硬件，敏捷开发已成为未来的趋势。而 RISC-V 则刚好成为这趋势中不可或缺的一环。

目前开源硬件开发中面临着 4 个关键问题 (Yungang Bao, Chinese Academy of Sciences, The Four Steps to An Open-Source Chip Design Ecosystem)：

1. 开放的指令集 ISA/开源 IPs/开源 Socs
2. 硬件描述语言 Lanuages/开源的 EDA 工具
3. 验证和仿真 Vertification/Simulation
4. OS/Complier

RISC-V 便处于第一环中，

虽然目前每个环节都还未完全解决，但我们可以相信，在未来，开发硬件可以像开发一个软件一样。充分利用已开源的资源，用户只需要定制 10% 以内的代码，便可以以月为单位开发出客制化的硬件系统。

## 4. 参考资料

[大道至简——RISC-V 架构之魂（上）](https://mp.weixin.qq.com/s/deNZzdSfxbdUoO58ok53tw)

[大道至简——RISC-V 架构之魂（中）](https://mp.weixin.qq.com/s/rB9ln7-cDb0VjtikD6KWzw)

[大道至简——RISC-V 架构之魂（下）](https://mp.weixin.qq.com/s/sIkKnJt6rQLxM5GM60OnLA)

[开放指令集与开源芯片进展报告-v1p1（2019-02-22 更新）](http://crva.io/documents/OpenISA-OpenSourceChip-Report.pdf)

[远景研讨会纪要–面向下一代计算的开源芯片与敏捷开发](http://crva.io/documents/SIGARCH-Visioning-Workshop-Summary-Agile-and-Open-Hardware-for-Next-Generation-Computing.pdf)
