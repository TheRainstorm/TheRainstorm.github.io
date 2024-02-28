---
title: HPL complie
date: 2020-02-16 00:07:30
tags:
  - hpl
mathjax: true
description: 关于编译 BLAS/CBLAS，编译 HPL 以及 HPL 的优化。
categories:
  - 学习
---

# 运行 HPL

## 编译 BLAS/CBLAS

BLAS 为 fortran 接口的库，CBLAS 为 C 语言接口的库

```bash
 tar zxf blas-3.8.0.tgz 
 tar zxf cblas.tgz
 cd BLAS-3.8.0
 make #生成blas_LINUX.a
 cp blas_LINUX.a ../CBLAS
 cd ../CBLAS
 vi Makefile.in
 #修改
 # BLLIB = ../blas_LINUX.a
 make #在lib/下生成cblas_LINUX.a
```

## 编译 HPL

```bash
tar zxf hpl-2.3.tar.gz 
cd hpl-2.3
cp setup/Make.Linux_PII_CBLAS ./Make.<arch> #在top-level 文件夹下
vi Make.<arch> #修改
make <arch> #在bin/<arch>/下生成HPL.dat xhpl

```

### Make.<arch>示例

#### OpenMPI+CBLAS

```makefile
ARCH         = <arch>

TOPdir       = /home/mpiuser/hpl-2.3

MPdir        = /path/to/OpenMPI
MPinc        = -I$(MPdir)/include
MPlib        = $(MPdir)/lib/libmpi.so

LAdir        = 
LAinc        = 
LAlib        = path/to/cblas_LINUX.a path/to/blas_LINUX.a #顺序不能改变，cblas依赖blas

HPL_OPTS     = -DHPL_CALL_CBLAS 

CC           = mpicc
LINKER       = mpif77
```

## HPL 优化

### 配置参数

计算次数：

$$
\#Ns \times \#NBs \times \#(Ps, Qs) \times \#PFACTs \times \#NBMINs \times \#BCASTs \times \#DEPTHs
$$

```
HPLinpack benchmark input file
Innovative Computing Laboratory, University of Tennessee
HPL.out      output file name (if any)
6            device out (6=stdout,7=stderr,file)
1            # of problems sizes (N)
8192         Ns
1            # of NBs
128          NBs
0            PMAP process mapping (0=Row-,1=Column-major)
3            # of process grids (P x Q)
2 1 4        Ps
2 4 1        Qs
16.0         threshold
3            # of panel fact
0 1 2        PFACTs (0=left, 1=Crout, 2=Right)
2            # of recursive stopping criterium
2 4          NBMINs (>= 1)
2            # of panels in recursion
2            NDIVs
3            # of recursive panel fact.
0 1 2        RFACTs (0=left, 1=Crout, 2=Right)
1            # of broadcast
0            BCASTs (0=1rg,1=1rM,2=2rg,3=2rM,4=Lng,5=LnM)
1            # of lookahead depth
0            DEPTHs (>=0)
2            SWAP (0=bin-exch,1=long,2=mix)
64           swapping threshold
0            L1 in (0=transposed,1=no-transposed) form
0            U  in (0=transposed,1=no-transposed) form
1            Equilibration (0=no,1=yes)
8            memory alignment in double (> 0)
```
