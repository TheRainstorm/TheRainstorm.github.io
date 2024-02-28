---
title: 安装使用 OpenCV(windows)
date: 2020-02-29 12:00:00
tags:
  - opencv
description: 关于 OpenCV 的安装 (预编译版，从源码安装)，使用 (VisualStudio 和 CMake)。
categories:
  - 学习
---

# 安装使用 OpenCV(windows)

## Install

### 安装预编译版

在[opencv.org](https://opencv.org/releases.html)上提供了源代码以及各个操作系统的预编译版。windows 预编译版为一个 installer 程序，运行后会将各种文件 extract 到安装目录。安装完成后，`/path/to/opencv/`包含两个目录——build, source。source 为源代码目录 (和直接下载源代码解压一模一样)，build 下包含了许多其它文件。其中：

- **include/**为调用 OpenCV 时需要包含的头文件 (源代码目录下也有)

- **x64/vcxx/**下包含 bin/和 lib/，为预编译的库。vcxx 代表使用 MSVC xx 编译的，运行时需要对应的 runtime 库。

  | IDE    | 编译器 |
  | ------ | ------ |
  | VS2017 | VC15   |
  | VS2015 | VC14   |
  | VS2013 | VC12   |
  | VS2012 | VC11   |
  | VS2010 | VC10   |
  | VS2008 | VC9    |
  | VS2005 | VC8    |

- **etc/**文件夹中是 OpenCV 某些算法所依赖的数据集。

- **`OpenCVConfig.cmake`**文件在使用 CMake 编译项目时可使用 find_package 自动搜索头文件、库文件路径

- 其它文件暂时不管

### 从源文件编译 OpenCV

  略

## Usage

### 通过 VisualStudio 编译 OpenCV 程序

1. 菜单栏 project->properities。（或在右侧的 Solution Explorer 下找到一个 project(solution 和 project 的关系)。鼠标右键->Properities）

2. C/C++/AdditionalIncludeDirectories。编译器从该文件夹下查找头文件。

   (*p.s.* `#include "opencv2/opencv.hpp"`和`#include "opencv.hpp"`对应不同的设置)

3. Linker/Input/AdditionalDependencies 添加`opencv_world420.lib`

4. Linker/General/AdditionalLibraryDirectories 添加`opencv_world420.lib`所在目录。（或直接在 3 中输入绝对路径）

5. 设置环境变量，把`opencv_world420.dll`所在目录添加到 Path 变量。(否则运行时报错：无法找到`opencv_world420.dll`)。不添加环境变量的方法是直接把`opencv_world420.dll`拷贝到 exe 所在目录。

   *p.s.* 貌似`opencv_world420.lib`表面上是一个静态链接库，但实际上是一个动态链接库，因而运行时需要`opencv_world420.dll`。而第 3 步如若改成添加`opencv_world420.dll`，则编译失败。

   > LNK1107 could also occur if you attempt to pass a module (.dll or .netmodule extension created with [/clr:noAssembly](https://docs.microsoft.com/en-us/cpp/build/reference/clr-common-language-runtime-compilation?view=vs-2019) or [/NOASSEMBLY](https://docs.microsoft.com/en-us/cpp/build/reference/noassembly-create-a-msil-module?view=vs-2019)) to the linker; pass the .obj file instead. 

### 通过 CMake 编译 OpenCV 程序

参考：[Using OpenCV with gcc and CMake](https://docs.opencv.org/2.4/doc/tutorials/introduction/linux_gcc_cmake/linux_gcc_cmake.html)

通过 CMake 编译 OpenCV 程序有几点好处：

- 在 Windows 和 Linux 之间移植程序不用更改设置。

- 自动搜索 include，lib 路径。(通过`OpenCVConfig.cmake`文件，需添加到 Path 环境变量)
- 写代码的方式比 VisualStudio 点击按钮然后输入方便，配置的文件可以保留下来用于其它项目。

缺点：

- #include 某个文件，VS Code 不会自动提示，不会自动自动补全函数，不会显示函数文档

  （可以先用 CMake 配置好 include, lib 后，生成 sln 并用 VS 打开）

步骤：

1. 添加`opencv/build/`到 Path(`OpenCVConfig.cmake`所在目录)。

2. 编写`CMakeLists.txt`。示例：

   ```
   cmake_minimum_required(VERSION 2.8)
   project( DisplayImage )
   find_package( OpenCV REQUIRED ) //
   add_executable( DisplayImage DisplayImage.cpp )
   target_link_libraries( DisplayImage ${OpenCV_LIBS} ) //
   ```

3. 使用 CMake GUI，点击 configure(可以先 File->Delete Cache，删除掉之前的配置)

   选择 VS 的编译器。

4. 在中间面板修改一些变量的值。（重新 configure）

5. Generate，在 build 目录下生成 VS 的 sln 文件，双击打开。

6. 在 ALL_BUILD 上右键 build。