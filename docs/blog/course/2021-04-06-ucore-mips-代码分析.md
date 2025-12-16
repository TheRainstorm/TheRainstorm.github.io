---
title: ucore-mips 代码分析
date: 2021-04-06 22:51:13
tags:
  - ucore
  - mips
categories:
  - 课程笔记
description: 分析了 ucore mips 版代码，主要包括 Makefile、启动过程、物理内存管理、虚拟内存管理、进程创建（内核和用户）。不过没有分析文件系统
---

[TOC]

### 1. Makefile

1. `boot/loader.bin`基本就是一个读取 elf 的函数，我们上板使用 pmon 加载 ucore，因此用不到。
2. `obj/ucore-kernel-initrd`是一个 elf 文件，特殊之处在于，它的 data 段包含`user/_archive`目录下的文件（包含一个 test.txt）和`$(USER_APP_BINS)`（如 sh, ls 等用户程序）的内容。**将内核和文件系统打包到了一起**。

### 2. kernel_entry

kern/init/entry.S

1. 设置了$gp

   定义在链接脚本里，可以通过`readelf obj/ucore-kernel-initrd -a|grep _gp`来查看其值。参考值（修改了代码编译出的值可能不一样）`0x800c7f40`

2. 设置了$sp，启动时用的栈，栈大小为`KSTACKSIZE`，8KB

   参考值：`bootstacktop(0x80068730)`，`bootstack(0x80066730)`

3. 设置了 Ebase 为`__exception_vector`。参考值：`0x8002b000`。__exception_vector 包含了各异常向量地址的入口。

### 3. kern_init

kern/int/init.c

#### 杂项

##### tlb_invalidate_all

定义于 kern/include/thumips_tlb.h 和 kern/mm/thumips_tlb.c

tlb_invalidata_all 循环调用 write_one_tlb 清空 tlb 表项
**默认 tlb 有 128 项**，虽然不会导致错误，但是可以优化

##### pic_init

定义于 kern/driver/picirq.c
pic_init -> write_c0_status
将 Statu 中的 IM 域全置 0，关闭所有中断。
之后可以通过 pic_enable(int irq) 或 pic_disable(int irq) 开关中断

##### cons_init & clock_init

一个初始化串口，一个初始化时钟中断。

相关宏定义于/kern/include/thumips.h

```c
#define COM1_IRQ        3
#define TIMER0_IRQ       7
```

clock 需要用到`cp0_count`和`cp0_compare`
设置 clock 中断后，每`clock.c::TIMER0_INTERVAL`=1000000 后会产生一个时钟中断

##### check_initrd

检查内核是否有 initrd，通过判断是否_initrd_begin == _initrd_end)

#### kprintf

内核第一次输出信息

```c
const char *message = "(THU.CST) os is loading ...\n\n";
kprintf(message);
```

kprintf 函数最后调用串口的 cons_putc 输出字符。串口输出字符采用忙等待方式。

```c
kern/lib/stdio.c::kprintf -> kern/lib/stdio.c::vkprintf -> kern/lib/printfmt.c::vprintfmt(cputch, ...)

kern/lib/stdio.c::cputch -> kern/driver/console.c::cons_putc
```

```c
#!kern/driver/console.c

static void
serial_putc_sub(int c) {
    while (!(inb(COM1 + COM_LSR) & COM_LSR_TXRDY)) {
    }
    outb(COM1 + COM_TX, c);
}
```

作为对比，用户程序 cprintf

```c
user/lib/stdio.c::cprintf -> user/lib/stdio.c::vcprintf -> user/lib/stdio.c::vprintfmt(cputch, ...)
user/lib/stdio.c::cputch -> user/lib/syscall.c::sys_putc -> syscall(SYS_putc, )
系统调用，进入内核
异常处理程序调用kern/syscall/syscall.c::sys_putc -> kern/lib/stdio.c::kputchar -> cons_putc
```

**用户程序输出每一个字符都会触发一次系统调用**

#### pmm_init

##### page 结构体

```c
struct Page {
    atomic_t ref;                   // page frame's reference counter
    uint32_t flags;                 // array of flags that describe the status of the page frame
    unsigned int property;          // used in buddy system, stores the order (the X in 2^X) of the continuous memory block
    int zone_num;                   // used in buddy system, the No. of zone which the page belongs to
    list_entry_t page_link;         // free list link
//    swap_entry_t index;             // stores a swapped-out page identifier
    list_entry_t swap_link;         // swap hash link
};
```

ucore 将物理内存划分成一个一个的页，并使用 Page 结构体数组来管理。一个 Page 项对应一个物理页。

参考 pmm.c::page_init 代码

```c
kprintf("memory map:\n");
kprintf("    [");
printhex(KERNBASE);
kprintf(", ");
printhex(KERNTOP);
kprintf("]\n\n");

maxpa = KERNTOP;
npage = KMEMSIZE >> PGSHIFT;

// end address of kernel
extern char end[];
// put page structure table at the end of kernel
pages = (struct Page *)ROUNDUP_2N((void *)end, PGSHIFT); 
```

`KMEMSIZE`代表内核管理的物理内存的大小，npage 计算出来为物理页的个数。

end 在链接脚本中定义，为 ucore-kernel-initrd 的结尾。即 ucore 在内核的结尾分配了（直接写）Page 数组的空间，pages 为数组的起始地址。

此时 page 项可以和物理页一一对应起来了

```c
static inline ppn_t
page2ppn(struct Page *page) {
    return page - pages;
}

static inline uintptr_t
page2pa(struct Page *page) {
    return KERNBASE + (page2ppn(page) << PGSHIFT);
}

static inline struct Page *
pa2page(uintptr_t pa) {
    if (PPN(pa) >= npage) {
        panic("pa2page called with invalid pa");
    }
    return &pages[PPN(pa)];
}

static inline void *
page2kva(struct Page *page) {
    return KADDR(page2pa(page));
}
```

这里强调一下`page2kva`中`KADDR`的作用，事实上如果看其定义的话，KADDR(pa) 的值和 pa 是一样的，如下

```c
/* *
 * PADDR - takes a kernel virtual address (an address that points above KERNBASE),
 * where the machine's maximum 256MB of physical memory is mapped and returns the
 * corresponding physical address.  It panics if you pass it a non-kernel virtual address.
 * */
#define PADDR(kva) ({                                                   \
            uintptr_t __m_kva = (uintptr_t)(kva);                       \
            if (__m_kva < KERNBASE) {                                   \
                panic("PADDR called with invalid kva %08lx", __m_kva);  \
            }                                                           \
            __m_kva ;                                         \
        })

/* *
 * KADDR - takes a physical address and returns the corresponding kernel virtual
 * address. It panics if you pass an invalid physical address.
 * */
#define KADDR(pa) ({                                                    \
            uintptr_t __m_pa = (pa);                                    \
            size_t __m_ppn = PPN(__m_pa);                               \
            if (__m_ppn >= npage) {                                     \
                panic("KADDR called with invalid pa %08lx", __m_pa);    \
            }                                                           \
            (void *) (__m_pa);                               \
        })
```

而之所以需要进行一次转换，主要是保持逻辑上的一致性。因为 CPU 直接发出的地址都是虚拟地址，会经过 MMU 进行虚拟地址转换（一般基于 TLB，而 TLB 基于操作系统管理的页表）。整个转换过程是硬件自动完成的，因此软件基本不用和物理地址打交道（操作系统中涉及到和硬件软硬件协同的部分会涉及到物理地址，如页表中存储的地址是物理地址，当 MIPS 中 tlb refill 异常时，便会读取页表项加载到 TLB 表项中）

因而我们在代码中访问数据时都要使用虚拟地址。

因为这里的整个内核虚拟空间（`[KERNBASE, KERNBASE+KMEMSIZE]=[0x8000_0000, 0x8200_0000)`）都位于 MIPS 中的 kseg0 段，而该段采用固定地址映射的方式，而不使用 TLB，因此内核访问整个内核虚拟地址空间丝毫不用担心。

###### 这里应该有一个错误

按照定义来说，page2pa 就应该是 (page2ppn(page) << PGSHIFT)，加了 KERNBASE 后反而是虚拟地址了。

不过因为 KADDR 也错了，因此当我们分配了一个空闲物理页 page 后，要获得其虚拟地址

`KADDR(page2pa(page))`反而没错了

##### 空闲页

空闲地址开始于 Page 数组之后。init_memmap 会调用 pmm_manager 的 init_memmap 函数，用于记录哪些页是空闲的。

```c
uintptr_t freemem = PADDR((uintptr_t)pages + sizeof(struct Page) * npage);
PRINT_HEX("freemem start at: ", freemem);

uint32_t mbegin = ROUNDUP_2N(freemem, PGSHIFT);
uint32_t mend = ROUNDDOWN_2N(KERNTOP, PGSHIFT);
assert( mbegin < mend );
init_memmap(pa2page(mbegin), (mend - mbegin) >> PGSHIFT );
PRINT_HEX("free pages: ", (mend-mbegin)>>PGSHIFT);
PRINT_HEX("## ", sizeof(struct Page));
```

##### pmm_manager

物理内存管理其实就是要实现**物理空闲页**的分配和回收，ucore 定义了 pmm_manager 的结构体，可以认为 C 中实现的类。

关键的两个函数：

```c
struct Page *(*alloc_pages)(size_t n);
void (*free_pages)(struct Page *base, size_t n);
```

alloc_pages 从空闲页中分配了一段连续的空闲页

而 free_pages 则将指定的一段连续的页重新回收为空闲页

ucore 代码实现了伙伴分配系统 (buddy system)，可以参考其具体实现

##### 页表相关函数

ucore 实现了二级页表

关键函数

```c
pte_t *get_pte(pde_t *pgdir, uintptr_t la, bool create);
struct Page *get_page(pde_t *pgdir, uintptr_t la, pte_t **ptep_store); //根据 pte 的值获得对应的 page
void page_remove(pde_t *pgdir, uintptr_t la);
int page_insert(pde_t *pgdir, struct Page *page, uintptr_t la, uint32_t perm);
struct Page * pgdir_alloc_page(pde_t *pgdir, uintptr_t la, uint32_t perm);
```

###### get_pte

```c
pte_t *get_pte(pde_t * pgdir, uintptr_t la, bool create)
```

函数作用：给定页目录表的虚拟地址，查找虚拟地址 la 对应的页表项 pte。（只要 la 在一个页内，返回的 pte 是相同的）
 注：获得的是 pte 项的**虚拟地址**
过程：

1. 先计算页目录表中对应 pde 表项的虚拟地址

   ```c
   pdep = pgdir + PDX(la)
   ```

2. 如果 pde 项有效，即`((*pdep)&PTE_P) == 0`。直接访问 pde 获得 la 对应二级页表的物理地址。

   ```c
   PDE_ADDR(*pdep)
   ```

3. 计算二级页表中对应页表项 pte 的**物理**地址

   ```c
   (pte_t*)(    PDE_ADDR(*pdep)   ) + PTX(la)
   ```

4. 转换成虚拟地址

   ```c
   (pte_t*)KADDR(   (uintptr_t)(  (pte_t*)(PDE_ADDR(*pdep))+PTX(la)  )  )
   ```

5. 如果 02 中无效，则需要根据 create 决定是否创建二级页表。（下面代码只考虑了创建情形，并为了突出重点，删减了许多有用的代码）

   ```c
   struct Page* new_pte = alloc_page();
   
   uintptr_t pa = (uintptr_t)page2kva(new_pte);
   *pdep = PADDR(pa);
   ```

   最后一行，页表中存储的是物理地址。然而根据之前的分析，我们知道上面代码中的 PADDR(pa) 实际上是虚拟地址。然而我们发现在这样设置之后，下次调用 get_pte 时，获得的 pte 的地址确实是虚拟地址（KADDR 不产生作用）。

###### page_insert

```c
int page_insert(pde_t *pgdir, struct Page *page, uintptr_t la, uint32_t perm)
```

作用：将虚拟地址 la 映射到 page 对应的物理页上

步骤：

1. 根据虚拟地址 la 查找到二级页表项 ptep

2. 如果原本 ptep 已经映射到另一个物理页上了，则删除该映射（有可能导致回收物理页）

3. 设置 ptep 映射到新物理页

   ```
   *ptep = page2pa(page) | PTE_P | perm;
   ```

   由以上代码，可以看到二级页表项中存储的地址其实是虚拟地址。

###### page_remove

```c
void page_remove(pde_t *pgdir, uintptr_t la) {
```

作用：解除 pgdir 中虚拟地址 la 的映射

步骤：

1. 获得 pte

   ```c
   pte_t *ptep = get_pte(pgdir, la, 0);
   ```

2. 如果`ptep != NULL`且`*ptep & PTE_P`，

   ```c
   struct Page *page = pte2page(*ptep);
   page_ref_dec(page);
   // and free it when reach 0
   if(page_ref(page) == 0){
       free_page(page);
   }
   ```

3. 清除映射

   ```c
   *ptep = 0;
   ```

###### pgdir_alloc_page

```c
struct Page * pgdir_alloc_page(pde_t *pgdir, uintptr_t la, uint32_t perm)
```

作用：该函数分配一个物理页，并将 la 对应的虚拟页，映射到该物理页

##### check

###### check_pgdir

1. 将虚拟地址 0x0 映射到一个物理页 (随便分配一个 page, p1) 上。
2. 将虚拟地址 0x1000(PAGESIZE) 映射到一个物理页 (随便分配一个 page, p2)。
3. 将 0x1000 重新映射到 p1.
   ......
   主要是检查了 page_insert, page_remove 等函数的正确性。

###### check_boot_pgdir（tlb refill 处理)

1. 分配一个物理页，并写入初始值

   ```c
   struct Page *p;
   p = alloc_page();
   *(int*)(page2kva(p) + 0x100) = 0x1234;
   ```

2. 将两个虚拟页映射到该物理页上

   ```c
   assert(page_insert(boot_pgdir, p, 0x100, PTE_W) == 0);
   assert(page_ref(p) == 1);
   assert(page_insert(boot_pgdir, p, 0x100 + PGSIZE, PTE_W) == 0);
   assert(page_ref(p) == 2);
   ```

3. 直接使用虚拟地址访问该物理页，引发 tlb refill 异常

   ```c
   assert(*(int*)0x100 == 0x1234);
   ```

4. 进入对应异常处理程序

   ```c
   static void handle_tlbmiss(struct trapframe* tf, int write)
   {
     int in_kernel = trap_in_kernel(tf);
     assert(current_pgdir != NULL);
     uint32_t badaddr = tf->tf_vaddr;
     int ret = 0;
     pte_t *pte = get_pte(current_pgdir, tf->tf_vaddr, 0);
     if(pte==NULL || ptep_invalid(pte)){   //PTE miss, pgfault
         kprintf("## pagefault in kernel, badaddr: 0x%x\n", badaddr);
       //tlb will not be refill in do_pgfault,
       //so a vmm pgfault will trigger 2 exception
       //permission check in tlb miss
       ret = pgfault_handler(tf, badaddr, get_error_code(write, pte));
     }else{ //tlb miss only, reload it
       /* refill two slot */
       /* check permission */
       if(in_kernel){
         kprintf("## tlb refill in kernel, badaddr: 0x%x\n", badaddr);
         tlb_refill(badaddr, pte); 
         return;
       }else{
         if(!ptep_u_read(pte)){
           ret = -1;
           goto exit;
         }
         if(write && !ptep_u_write(pte)){
           ret = -2;
           goto exit;
         }
       //kprintf("## refill U %d %08x\n", write, badaddr);
         tlb_refill(badaddr, pte);
         return ;
       }
     }
   
   exit:
     if(ret){
       print_trapframe(tf);
       if(in_kernel){
         panic("unhandled pgfault");
       }else{
         do_exit(-E_KILLED);
       }
     }
     return ;
   }
   ```

   1. 首先判断是否在内核中发生了异常，这里通过 Status.KSU 位来判断，2'b00 表示 kernel mode，2'b10 表示 user mode。

       ```c
       bool
       trap_in_kernel(struct trapframe *tf) {
         return !(tf->tf_status & KSU_USER);
       }
       ```

   2. 然后获得 pte

       ```c
       pte_t *pte = get_pte(current_pgdir, tf->tf_vaddr, 0);
       ```

   3. 之后进入 tlb_refill 函数，tlb_refill 执行 tlbwr，从 pte 读取映射的物理页号写入到 tlb 项中。（一次映射两页）

       ```c
       tlb_replace_random(0, badaddr & THUMIPS_TLB_ENTRYH_VPN2_MASK, 
             pte2tlblow(*pte), pte2tlblow(*(pte+1)));
       ```

终端输出

```
## tlb refill in kernel, badaddr: 0x100
check_boot_pgdir() succeeded!
```

##### kmalloc

pmm_init 中还调用了 kmalloc_init。

kmalloc 中主要实现了以下关键函数

```c
void *kmalloc(size_t n);
void kfree(void *objp);
```

可以看到 kmalloc 函数的参数为字节数，返回值为分配的物理内存的虚拟起始地址。

kmalloc 利用到了 slab 机制

>slab 是 Linux 操作系统的一种内存分配机制。其工作是针对一些经常分配并释放的对象，如进程描述符等，这些对象的大小一般比较小，如果直接采用伙伴系统来进行分配和释放，不仅会造成大量的内存碎片，而且处理速度也太慢。而 slab 分配器是基于对象进行管理的，相同类型的对象归为一类 (如进程描述符就是一类)，每当要申请这样一个对象，slab 分配器就从一个 slab 列表中分配一个这样大小的单元出去，而当要释放时，将其重新保存在该列表中，而不是直接返回给伙伴系统，从而避免这些内碎片。

#### vmm_init

通过内存地址虚拟化，可以使得软件在没有访问某虚拟内存地址时不分配具体的物理理内存，而只有在实际访问某虚拟内存地址时，操作系统再动态地分配物理内存，建立虚拟内存到物理理内存的页映射关系，这种技术称为按需分页（demand paging）。把不不经常访问的数据所占的内存空间临时写到硬盘上，这样可以腾出更更多的空闲内存空间
给经常访问的数据；当 CPU 访问到不不经常访问的数据时，再把这些数据从硬盘读入到内存中。这种技术称为页换入换出 (page in/out)

##### vma_struct

vma 用于描述进程对虚拟内存的需求

```c
struct vma_struct {
    struct mm_struct *vm_mm; // the set of vma using the same PDT 
    uintptr_t vm_start;      // start addr of vma 
    uintptr_t vm_end;        // end addr of vma
    uint32_t vm_flags;       // flags of vma
    list_entry_t list_link;  // linear list link which sorted by start addr of vma
};
```

vma 指示了一段连续的虚拟内存空间，不同 vma 通过 list_link 相连，共同表示一个进程的虚拟内存空间。

##### mm_struct

```c
struct mm_struct {
    list_entry_t mmap_list;        // linear list link which sorted by start addr of vma
    struct vma_struct *mmap_cache; // current accessed vma, used for speed purpose
    pde_t *pgdir;                  // the PDT of these vma
    int map_count;                 // the count of these vma
 void *sm_priv;       // the private data for swap manager
 atomic_t mm_count;
 semaphore_t mm_sem;
 int locked_by;
};
```

mm_struct 用于管理一系列使用同一个页目录表的 vma 的集合。

进程控制块中包含一个 mm_struct 的指针，用于管理该进程的虚拟内存空间

###### 关键函数

```c
struct vma_struct *find_vma(struct mm_struct *mm, uintptr_t addr);
struct vma_struct *vma_create(uintptr_t vm_start, uintptr_t vm_end, uint32_t vm_flags);
void insert_vma_struct(struct mm_struct *mm, struct vma_struct *vma);
```

##### check_pgfault（pagefault 的处理）

1. 创建 mm_struct

    ```c
    check_mm_struct = mm_create();
    ```

    这里的`check_mm_struct`为全局变量

2. 分配[0, PTSIZE]的虚拟内存

    ```c
    struct vma_struct *vma = vma_create(0, PTSIZE, VM_WRITE); //如果该成 VM_READ，之后在 do_pgfault 便会通不过权限检查。
    insert_vma_struct(mm, vma);
    ```

3. 访问 0x100

    ```c
      uintptr_t addr = 0x100;
      assert(find_vma(mm, addr) == vma);

      int i, sum = 0;
      for (i = 0; i < 100; i ++) {
        *(char *)(addr + i) = i;    //page fault
        sum += i;
      }
      for (i = 0; i < 100; i ++) {
        sum -= *(char *)(addr + i);
      }
      assert(sum == 0);
    ```

4. 触发 tlb refill 异常。（实际为 pagefault，此时页表中没有该映射，因此 tlb 中也没有该项）

    参考之前 tlb refill 异常处理的代码，进入 pgfault_handler

    1. 首先通过判断 check_mm_struct 非空，知道是在执行 check_pgfault 函数，将 mm 设置为 check_mm_struct
    2. 在 do_pgfault 中首先调用 find_vma 函数，确定该虚拟地址是有效的
    3. 然后检查该地址访问权限是否正确（如果将
    4. 都通过了后，调用 pgdir_alloc_page，直接分配一个物理页，并在 mm->pgdir 中插入映射关系。
    5. 异常处理完成并返回

5. 再次触发 tlb refill 异常。（现在页表中存在了该映射，因此进入 tlb_refill 函数）

终端输出

```
## pagefault in kernel, badaddr: 0x100
## tlb refill in kernel, badaddr: 0x100
check_pgfault() succeeded!
```

代码

```c
static inline int get_error_code(int write, pte_t *pte)
{
  int r = 0;
  if(pte!=NULL && ptep_present(pte)) //因为 pagefault 的条件 (pte==NULL || ptep_invalid(pte))，这里根本不可能为真
    r |= 0x01;
  if(write)
    r |= 0x02;
  return r;
}
```

```c
static int
pgfault_handler(struct trapframe *tf, uint32_t addr, uint32_t error_code) {
  extern struct mm_struct *check_mm_struct;
  struct mm_struct *mm;
  if (check_mm_struct != NULL) {
    assert(current == NULL);
    mm = check_mm_struct;
  }
  else {
    if (current == NULL) {
      print_trapframe(tf);
      //print_pgfault(tf);
      panic("unhandled page fault.\n");
    }
    mm = current->mm;
  }
  return do_pgfault(mm, error_code, addr);
}
```

```c
#! vmm.c

//page fault number
volatile unsigned int pgfault_num=0;
// do_pgfault - interrupt handler to process the page fault execption
int
do_pgfault(struct mm_struct *mm, uint32_t error_code, uintptr_t addr) {
  int ret = -E_INVAL;
  struct vma_struct *vma = find_vma(mm, addr);
  //kprintf("## %08x %08x\n", error_code, addr);

  pgfault_num++;
  if (vma == NULL || vma->vm_start > addr) {
    kprintf("not valid addr %x, and  can not find it in vma\n", addr);
    goto failed;
  }

  switch (error_code & 3) {
    default:
      /* default is 3: write, present */
    case 2: /* write, not present */
      if (!(vma->vm_flags & VM_WRITE)) {
        kprintf("write, not present in do_pgfault failed\n");
        goto failed;
      }
      break;
    case 1: /* read, present */
      kprintf("read, present in do_pgfault failed\n");
      goto failed;
    case 0: /* read, not present */
      if (!(vma->vm_flags & (VM_READ | VM_EXEC))) {
        kprintf("read, not present in do_pgfault failed\n");
        goto failed;
      }
  }

  uint32_t perm = PTE_U;
  if (vma->vm_flags & VM_WRITE) {
    perm |= PTE_W;
  }
  addr = ROUNDDOWN_2N(addr, PGSHIFT);
    
  ret = -E_NO_MEM;

  // try to find a pte, if pte's PT(Page Table) isn't existed, then create a PT.
  pte_t *ptep=NULL;
  if ((ptep = get_pte(mm->pgdir, addr, 1)) == NULL) {
    goto failed;
  }

  if (*ptep == 0) { // if the phy addr isn't exist, then alloc a page & map the phy addr with logical addr
    if (pgdir_alloc_page(mm->pgdir, addr, perm) == NULL) {
      goto failed;
    }
  }
  else { // if this pte is a swap entry, then load data from disk to a page with phy addr, 
    // map the phy addr with logical addr, trig swap manager to record the access situation of this page
    if(swap_init_ok) {
      panic("No swap!! never reach!!"); 
    }
    else {
      kprintf("no swap_init_ok but ptep is %x, failed\n",*ptep);
      goto failed;
    }
  }
  /* refill TLB for mips, no second exception */
  //tlb_refill(addr, ptep);
  ret = 0;
failed:
  return ret;
}
```

#### 函数调用

1. 使用 jal 调用函数，使用 jr ra 返回。使用 a0-a3 传递参数，使用 v0-v1 传递返回值。对于更多的参数，使用栈传递。

2. 为了防止寄存器的值被覆盖。需要在存储寄存器的值，可以由 caller 或者 callee 来完成。但是只有一方完成时，因为 caller 不知道 callee 会用哪些寄存器，或者 callee 不知道 caller 需要用哪些寄存器。因此就会导致存储不必要的寄存器。MIPS 采用了一种折衷的策略，将寄存器分为 caller-save（如 t0-t7, a0-a3, v0-v1）和 callee-save（如 s0-s7, ra）

3. fp 寄存器（也是 s8）用于指向栈帧的第一个元素。因为 x86 中提供了 push 和 pop 指令，sp 的位置是变化的，要引用不同变量的值是用 fp 更方便。而 MIPS 中则是在函数的开头手动将 sp 设置，sp 之后的值不会变化，因此 fp 貌似作用不大。

4. gp 寄存器，用于程序访问全局变量（比如函数的地址）。

   > ps. 使用 mipsel-linux-gnu-gcc -S 编译一个简单的函数调用测试代码。不知为什么和上面讲的 caller-save，callee-save 对不上。比如函数开头`addiu $sp,$sp,-40`，但结果却根本没用上这么大的空间。然后，为什么还会出现`sw $a0,40($fp)`，即将参数`a0`写入父函数栈帧的情况。（这个然后 fp 和 sp 始终相等，不知道为什么要去存储 fp

#### sched_init & proc_init

##### proc_struct(进程控制块)

```c
struct proc_struct {
    enum proc_state state;                      // Process state
    int pid;                                    // Process ID
    int runs;                                   // the running times of Proces
    uintptr_t kstack;                           // Process kernel stack
    volatile bool need_resched;                 // bool value: need to be rescheduled to release CPU?
    struct proc_struct *parent;                 // the parent process
    struct mm_struct *mm;                       // Process's memory management field
    struct context context;                     // Switch here to run process
    struct trapframe *tf;                       // Trap frame for current interrupt
    uintptr_t cr3;                              // CR3 register: the base addr of Page Directroy Table(PDT)
    uint32_t flags;                             // Process flag
    char name[PROC_NAME_LEN + 1];               // Process name
    list_entry_t list_link;                     // Process link list 
    list_entry_t hash_link;                     // Process hash list
    int exit_code;                              // exit code (be sent to parent proc)
    uint32_t wait_state;                        // waiting state
    struct proc_struct *cptr, *yptr, *optr;     // relations between processes
    struct run_queue *rq;                       // running queue contains Process
    list_entry_t run_link;                      // the entry linked in run queue
    int time_slice;                             // time slice for occupying the CPU
    struct fs_struct *fs_struct;                // the file related info(pwd, files_count, files_array, fs_semaphore) of process
};
```

###### tf

```c
struct trapframe {
 uint32_t tf_vaddr; /* coprocessor 0 vaddr register */
 uint32_t tf_status; /* coprocessor 0 status register */
 uint32_t tf_cause; /* coprocessor 0 cause register */
 uint32_t tf_lo;
 uint32_t tf_hi;
 uint32_t tf_ra; /* Saved register 31 */
  struct pushregs tf_regs;
 uint32_t tf_epc; /* coprocessor 0 epc register */
};
```

tf 记录了

1. 进程的上下文：32 个通用寄存器的值
2. epc, status, cause 等 CP0 寄存器

进入异常后，要将 sp 切换到内核栈。对于内核进程来说，就是当前的 sp，而对于用户进程来说，需要从进程控制块中读取 kstack 的地址。

uCore 内核允许嵌套中断。因此为了了保证嵌套中断发⽣生时 tf 总是能够指向当前的 trapframe，uCore 在内核栈上维护了了 tf 的链。

> 发生中断（异常）时，trap.c::mips_trap 会改变当前进程 current->tf 的值
>
> `current->tf = *tf*;`
>
> 要实现嵌套中断，需要在改变 current->tf 前使用一个 trapframe *otf（局部变量，存储在内核栈中）存下来。之后再将 current->tf 恢复为 otf。
>
> 这里提一下，如果一个用户进程发生了异常，在异常处理程序中又发生了一次异常，那么第二次异常时，已经处于了内核模式（在压入 tf 后，调用 mips_trap 之前）。在 ramExcHandle_general 中就不会计算新的 sp
>
> ```assembly
> mfc0 k0, CP0_STATUS /* Get status register */
> andi k0, k0, KSU_USER/* Check the we-were-in-user-mode bit */
> beq k0, $0, 1f  /* If clear, from kernel, already have stack */
> ```
>
>

###### kstack

内核栈用于存储中断帧 tf 以及作为进程在内核中执行使用的 sp

对于内核线程，该栈就是运行时的程序使⽤用的栈。而对于普通进程，uCore 在创建进程时分配了了 2 个连续的物理理⻚页作为内核栈的空间。

内核栈位于内核地址空间，并且是不不共享的（每个线程都拥有⾃自⼰己的内核栈），因此不不受到 mm 的管理理，当进程退出的时候，内核能够根据 kstack 的值快速定位栈的位置并进⾏行行回收。

###### mm

内存管理理的信息，包括内存映射列列表、⻚页表指针等。mm 成员变量量在 lab3 中⽤用于虚存管理理。但在实际 OS 中，内核线程常驻内存，不不需要考虑 swap page 问题，在 lab3 中涉及到了了⽤用户进程，才考虑进程⽤用户内存空间的 swap page 问题，mm 才会发挥作⽤用。

> 还没看到用户进程的 swap page 代码

##### 创建内核线程

###### idle

proc_init 函数启动了创建内核线程的步骤。首先当前的执行上下文（从 kern_init 启动至今）就可以看成是 uCore 内核中的一个内线程的上下文。为此，uCore 调用 alloc_proc 函数给当前执行的上下文分配一个进程控制块并在 proc_init 中对它进行相应初始化，将其打造成第 0 个内核线程 --idleproc。

```c
   //alloc_proc
   proc->mm = NULL;    //不需要，所有内核进程公用一个页表
   proc->cr3 = boot_cr3;  //在 pmm_init 中分配为 PADDR(boot_pgdir)
   
   //proc_init
   idleproc->pid = 0;
   idleproc->state = PROC_RUNNABLE;
   idleproc->kstack = (uintptr_t)bootstack; //在 entry.S 中设置的
   idleproc->need_resched = 1; //表明在 kern_init 后会切换
```

###### init(kernel_thread & do_fork)

idle 内核线程主要工作是完成内核中各个子系统的初始化，idle 会调用 kernel_thread 函数创建内核线程 init。

kernel_thread 简单来说为新进程分配了 PCB 空间，和 kstack 空间。

```c
  //proc_init
 int pid = kernel_thread(init_main, NULL, 0);
    if (pid <= 0) {
        panic("create init_main failed.\n");
    }
    initproc = find_proc(pid);
    set_proc_name(initproc, "init");
```

过程：

1. kernel_thread 创建内核线程的中断帧，重点在于将 epc 设置为了 kernel_thread_entry，以及设置 a0 和 a1 为 arg 和 fn。**还有一点值得注意，status 的 KSU 为内核模式**。

   当从 eret 返回后（forkrets -> exception_return），CPU 便会进入 kernel_thread_entry，并以 tf 中指定的寄存器值执行。

   kernel_thread 函数采用了局部变量 tf 来放置中断帧，并把中断帧的指针传递给 do_fork 函数。

   kernel_thread 调用 do_fork 的 stack 参数为 0。在 do_fork->copy_thread 以此来判断是创建内核线程

2. do_fork 作用是以当前进程为父进程，创建一个子进程，可以根据 clone_flags 决定是否共享 mm。具体主要做了以下一些事情：

   1. 调用 alloc_proc 为子进程分配 PCB 空间

   2. 调用 setup_kstack(proc)**分配了内核栈空间**（注意这里的 kstack 为空闲页的起始地址，而非栈顶）

   3. 调用 copy_mm，根据 clone_flags 来确定是复制还是共享 mm。（只对用户进程有效，内核线程 mm 都为 NULL）

   4. 调用 copy_thread：将 tf 拷贝到 kstack 的栈顶，**设置 tf 中的 sp 为 proc->tf - 32**（这里的减 32 应该和之前提到的 MIPS 函数调用规则有关，不管怎样，sp 是位于 kstack 中的）

      **将 context 中的 ra 设置为 forkret**

   5. 将子进程插入 hash_list 和 proc_list

   6. 调用 wakeup_proc 将进程加入调度队列

```c
int
kernel_thread(int (*fn)(void *), void *arg, uint32_t clone_flags) {
    struct trapframe tf;
    memset(&tf, 0, sizeof(struct trapframe));
    tf.tf_regs.reg_r[MIPS_REG_A0] = (uint32_t)arg;
    tf.tf_regs.reg_r[MIPS_REG_A1] = (uint32_t)fn;
    tf.tf_regs.reg_r[MIPS_REG_V0] = 0;
    //TODO
    tf.tf_status = read_c0_status();
    tf.tf_status &= ~ST0_KSU;
    tf.tf_status |= ST0_IE;
    tf.tf_status |= ST0_EXL;
    tf.tf_regs.reg_r[MIPS_REG_GP] = __read_reg($28);
    tf.tf_epc = (uint32_t)kernel_thread_entry;
    return do_fork(clone_flags | CLONE_VM, 0, &tf);
}

//kern/proc/entry.S
kernel_thread_entry:        # void kernel_thread(void)
  addiu $sp, $sp, -16
  jal $a1
  nop
  move $a0, $v0
  la  $t0, do_exit
  jal $t0 
  nop
  /* never here */
    
//called by do_fork
static void
copy_thread(struct proc_struct *proc, uintptr_t esp, struct trapframe *tf) {
    proc->tf = (struct trapframe *)(proc->kstack + KSTACKSIZE) - 1;
    *(proc->tf) = *tf;
    proc->tf->tf_regs.reg_r[MIPS_REG_V0] = 0;
    if(esp == 0) //a kernel thread
      esp = (uintptr_t)proc->tf - 32;
    proc->tf->tf_regs.reg_r[MIPS_REG_SP] = esp;
    proc->context.sf_ra = (uintptr_t)forkret;
    proc->context.sf_sp = (uintptr_t)(proc->tf) - 32;
}

// do_fork - parent process for a new child process
//    1. call alloc_proc to allocate a proc_struct
//    2. call setup_kstack to allocate a kernel stack for child process
//    3. call copy_mm to dup OR share mm according clone_flag
//    4. call copy_thread to setup tf & context in proc_struct
//    5. insert proc_struct into hash_list && proc_list
//    6. call wakup_proc to make the new child process RUNNABLE 
//    7. set the 
int
do_fork(uint32_t clone_flags, uintptr_t stack, struct trapframe *tf) {
 int ret = -E_NO_FREE_PROC;
 struct proc_struct *proc;
 if (nr_process >= MAX_PROCESS) {
     goto fork_out;
 }
 ret = -E_NO_MEM;
 //LAB4:EXERCISE2 2009010989
 if ((proc = alloc_proc()) == NULL) {
     goto fork_out;
 }

 proc->parent = current;

 if(setup_kstack(proc)){
     goto bad_fork_cleanup_proc;
 }
 //LAB8:EXERCISE2 2009010989 HINT:how to copy the fs in parent's proc_struct?
 if (copy_fs(clone_flags, proc) != 0) {
     goto bad_fork_cleanup_kstack;
 }
 if (copy_mm(clone_flags, proc)){
     goto bad_fork_cleanup_fs;
 }

 copy_thread(proc, (uint32_t)stack, tf);

 proc->pid = get_pid();
 hash_proc(proc);


 //list_add(&proc_list, &(proc->list_link));
 set_links(proc);

 wakeup_proc(proc);

 ret = proc->pid;

fork_out:
 return ret;

bad_fork_cleanup_fs:
 put_fs(proc);
bad_fork_cleanup_kstack:
 put_kstack(proc);
bad_fork_cleanup_proc:
 kfree(proc);
 goto fork_out;
}
```

###### user_main

在 init_main 中，创建了 user_main 线程。

```c
// init_main - the second kernel thread used to create user_main kernel threads
static int
init_main(void *arg) {
 ...
    int pid = kernel_thread(user_main, NULL, 0);
    if (pid <= 0) {
        panic("create user_main failed.\n");
    }

    while (do_wait(0, NULL) == 0) {
        schedule();
    }

    fs_cleanup();
    kprintf("all user-mode processes have quit.\n");
    ...
}
```

kernel_thread 之前已经分析过了，我们来看 user_main 做了什么

```c
// user_main - kernel thread used to exec a user program
static int
user_main(void *arg) {
    kprintf("in user main, pid: %d\n", current->pid);
    KERNEL_EXECVE(sh);
    panic("user_main execve failed.\n");
}
```

user_main 调用了`KERNEL_EXECVE`来加载执行一个用户程序。`KERNEL_EXECVE`被展开为对 kernel_execve 的调用。

```c
// kernel_execve - do SYS_exec syscall to exec a user program called by user_main kernel_thread
static int
kernel_execve(const char *name, const char **argv) {
    int argc = 0, ret;
    while (argv[argc] != NULL) {
        argc ++;
    }
    //panic("unimpl");
    asm volatile(
      "la $v0, %1;\n" /* syscall no. */
      "move $a0, %2;\n"
      "move $a1, %3;\n"
      "move $a2, %4;\n"
      "move $a3, %5;\n"
      "syscall;\n"
      "nop;\n"
      "move %0, $v0;\n"
      : "=r"(ret)
      : "i"(SYSCALL_BASE+SYS_exec), "r"(name), "r"(argc), "r"(argv), "r"(argc) 
      : "a0", "a1", "a2", "a3", "v0"
    );
    return ret;
}
```

而 kernel_execve 则是进行了一次系统调用。

kernel_execve -> SYSCALL -> sys_exec -> do_execve

1. 因为 kernel_execve 就是在内核线程，所以之后进行系统调用，仍然是使用一样的内核栈。

2. do_execve 做的事情

   ```c
   int do_execve(const char *name, int argc, const char **argv) 
   ```

   1. 创建局部变量 local_name, kargv（位于上下文的内核栈中），将参数 name, argv 复制过来。

      kernel_execve 调用时传递了"sh"字符串常量的地址。而该"sh"的地址在 gdb 调试时显示为 0x8002_7ff0，而 local_name 的地址则为 0x81fe_bd20（此时 sp 为 0x81fe_bd00，可以知道 local_name 位于当前函数的栈帧中，而"sh"位于别处）

      ```c
      copy_string(mm, local_name, name, sizeof(local_name))
          
      copy_kargv(mm, argc, kargv, argv)
      ```

      copy_string 函数，作用是先检查访问 src 是否合法（通过 mm），然后将 src 复制到 dst 中。这里的 dst 位于内核空间

      ```c
      bool copy_string(struct mm_struct *mm, char *dst, const char *src, size_t maxn) 
      ```

      copy_string 具体代码，if 判断有点复杂，且没有注释，没太看懂。

   2. 读取文件系统，获得文件号，之后传给 load_icode 使用。

      ```c
      fd = sysfile_open(path, O_RDONLY)
      ```

   3. 清空原本的 mm。vma，分配的 Page，页表等等都会被清除。(user 此时是内核进程，因此没有 mm)

      ```c
       if (mm != NULL) {
              lcr3(boot_cr3);
              if (mm_count_dec(mm) == 0) {
                  exit_mmap(mm);
                  put_pgdir(mm);
                  mm_destroy(mm);
              }
              current->mm = NULL;
          }
      ```

   4. 调用 load_icode

      ```c
      load_icode(fd, argc, kargv)
      ```

      调用完 load_icode 后，elf 文件已经被全部加载进内存，并且根据 elf 文件 program header 的内容设置好了 vma，页表等内容。还分配了 USTACK 空间。

3. load_icode 做的事情

   ```c
   // load_icode -  called by sys_exec-->do_execve
   // 1. create a new mm for current process
   // 2. create a new PDT, and mm->pgdir= kernel virtual addr of PDT
   // 3. copy TEXT/DATA/BSS parts in binary to memory space of process
   // 4. call mm_map to setup user stack, and put parameters into user stack
   // 5. setup trapframe for user environment 
   static int
   load_icode(int fd, int argc, char **kargv)
   ```

   1. 创建新的 mm

      ```c
       struct mm_struct *mm;
          if ((mm = mm_create()) == NULL) {
              goto bad_mm;
          }
          if (setup_pgdir(mm) != 0) {
              goto bad_pgdir_cleanup_mm;
          }
      ```

   2. 接下来涉及到对 elf 文件的解析。首先调用 load_icode_read 读取 elf 头 (struct elfhdr32)。然后根据 elfhdr，获得程序头 (struct proghdr) 的文件内偏移 elf->e_phoff、程序头的数量 elf->e_phnum。再通过 for 循环，读取每个程序头 ph。程序头显示了每个段的信息。

      ```c
      for (phnum = 0; phnum < elf->e_phnum; phnum ++) {
          off_t phoff = elf->e_phoff + sizeof(struct proghdr) * phnum;
          if ((ret = load_icode_read(fd, ph, sizeof(struct proghdr), phoff)) != 0) {
              goto bad_cleanup_mmap;
       }
          ...
      ```

      readelf -l  obj/user/sh的信息

      ```
      Elf 文件类型为 EXEC (可执行文件)
      Entry point 0x100033d0
      There are 2 program headers, starting at offset 52
      
      程序头：
        Type           Offset   VirtAddr   PhysAddr   FileSiz MemSiz  Flg Align
        ABIFLAGS       0x0141d0 0x100041d0 0x100041d0 0x00018 0x00018 R   0x8
        LOAD           0x010000 0x10000000 0x10000000 0x05010 0x09010 RWE 0x10000
      
       Section to Segment mapping:
        段节...
         00     .MIPS.abiflags 
         01     .text .MIPS.abiflags .data .bss
      ```

   3. 根据每个 ph 的信息，添加 vma。这里用的是 ph->p_memsz。

      ```c
       vm_flags = 0;
            //ptep_set_u_read(&perm);
          perm |= PTE_U;
          if (ph->p_flags & ELF_PF_X) vm_flags |= VM_EXEC;
          if (ph->p_flags & ELF_PF_W) vm_flags |= VM_WRITE;
          if (ph->p_flags & ELF_PF_R) vm_flags |= VM_READ;
          if (vm_flags & VM_WRITE) perm |= PTE_W; 
      
          if ((ret = mm_map(mm, ph->p_va, ph->p_memsz, vm_flags, NULL)) != 0) {
              goto bad_cleanup_mmap;
          }
      ```

   4. 调用 pgdir_alloc_page 为每个虚拟地址分配物理页，并添加页表映射。调用 load_icode_read 将 elf 文件对应段 (segment) 读取到对应的物理页中。

      ```c
      
          off_t offset = ph->p_offset;
          size_t off, size;
          uintptr_t start = ph->p_va, end, la = ROUNDDOWN_2N(start, PGSHIFT);
      
          end = ph->p_va + ph->p_filesz;
          while (start < end) {
              if ((page = pgdir_alloc_page(mm->pgdir, la, perm)) == NULL) {
                  ret = -E_NO_MEM;
                  goto bad_cleanup_mmap;
              }
              off = start - la, size = PGSIZE - off, la += PGSIZE;
              if (end < la) {
                  size -= la - end;
              }
              if ((ret = load_icode_read(fd, page2kva(page) + off, size, offset)) != 0) {
                  goto bad_cleanup_mmap;
              }
              start += size, offset += size;
          }
      ```

   5. 设置 bss 段（猜测）

      ```c
       end = ph->p_va + ph->p_memsz;
      
          if (start < la) {
              if (start >= end) {
                  continue ;
              }
              off = start + PGSIZE - la, size = PGSIZE - off;
              if (end < la) {
                  size -= la - end;
              }
              memset(page2kva(page) + off, 0, size);
              start += size;
              assert((end < la && start == end) || (end >= la && start == la));
          }
      
          while (start < end) {
              if ((page = pgdir_alloc_page(mm->pgdir, la, perm)) == NULL) {
                  ret = -E_NO_MEM;
                  goto bad_cleanup_mmap;
              }
              off = start - la, size = PGSIZE - off, la += PGSIZE;
              if (end < la) {
                  size -= la - end;
              }
              memset(page2kva(page) + off, 0, size);
              start += size;
          }
      ```

   6. 映射用户栈空间（添加 vma，当发生 pagefault 时，异常处理程序会自动分配物理页）

      ```c
       vm_flags = VM_READ | VM_WRITE | VM_STACK;
          if ((ret = mm_map(mm, USTACKTOP - USTACKSIZE, USTACKSIZE, vm_flags, NULL)) != 0) {
              goto bad_cleanup_mmap;
          }
      ```

   7. 将函数调用参数压入用户栈中

      ```c
         uintptr_t stacktop = USTACKTOP - argc * PGSIZE;
          char **uargv = (char **)(stacktop - argc * sizeof(char *));
          int i;
          for (i = 0; i < argc; i ++) {
              uargv[i] = strcpy((char *)(stacktop + i * PGSIZE), kargv[i]);
          }
      ```

      上一个步骤已经将 USTACKTOP 添加到了 vma 中。因此在第一次访问用户栈时会触发 pagefault（页表中没有映射关系），操作系统会动态分配 Page。第二次访问会再触发一次 tlb refill，tlb 添加映射关系，之后便可以正常访问了。

   8. 设置 tf。

      1. 将 tf->tf_epc 设置为了 elf->e_entry。因此异常返回时便开始执行 elf 程序。

      2. 在 tf->tf_status 中设置了 KSU_USER，因此从 SYSCALL 返回后，CPU 会转变为用户态。

      ```c
       struct trapframe *tf = current->tf;
          memset(tf, 0, sizeof(struct trapframe));
      
          tf->tf_epc = elf->e_entry;
          tf->tf_regs.reg_r[MIPS_REG_SP] = USTACKTOP;
          uint32_t status = read_c0_status();
          status &= ~ST0_KSU;
          status |= KSU_USER;     //变成用户进程
          status |= ST0_EXL;
          tf->tf_status = status;
          tf->tf_regs.reg_r[MIPS_REG_A0] = argc;
          tf->tf_regs.reg_r[MIPS_REG_A1] = (uint32_t)uargv;
      ```

##### 调度

执行完 proc_init 后，已经创建好了两个内核线程 idle 和 init，并且当前执行的线程为 proc_init。当 ucore 的所有初始化工作完成后，ucore 执行 kern_init 的最后一个函数 cpu_idle 函数。cpu_idle 会调用 schedule 让出 CPU。

schedule 具体的实现我们可以不关心。我们只需要知道 sched_class_enqueue(proc) 将一个进程放入运行队列 run queue。next = sched_class_pick_next() 从 rq 中找到下一个执行的进程。

当选定需要执行的进程后，proc_run 函数将该进程载入 CPU 执行。

```c
void
cpu_idle(void) {
    while (1) {
        if (current->need_resched) {
            schedule();
        }
    }
}

void
schedule(void) {
    bool intr_flag;
    struct proc_struct *next;
    local_intr_save(intr_flag);
    {
        current->need_resched = 0;
        if (current->state == PROC_RUNNABLE) {
            sched_class_enqueue(current);
        }
        if ((next = sched_class_pick_next()) != NULL) {
            sched_class_dequeue(next);
        }
        if (next == NULL) {
            next = idleproc;
        }
        next->runs ++;
        if (next != current) {
            //kprintf("########################\n");
            //kprintf("c %d TO %d\n", current->pid, next->pid);
            //print_trapframe(next->tf);
            //kprintf("@@@@@@@@@@@@@@@@@@@@@@@@\n");
            proc_run(next);
        }
    }
    local_intr_restore(intr_flag);
}

void
proc_run(struct proc_struct *proc) {
    if (proc != current) {
        bool intr_flag;
        struct proc_struct *prev = current, *next = proc;
        local_intr_save(intr_flag);
        {
          //panic("unimpl");
            current = proc;
            //load_sp(next->kstack + KSTACKSIZE);
            lcr3(next->cr3);
            tlb_invalidate_all();       //标注一下这里的 tlb 清空，待优化
            switch_to(&(prev->context), &(next->context));
        }
        local_intr_restore(intr_flag);
    }
}
```

proc_run 会调用 switch_to，switch_to 会：

1. 将当前的 context 存储在 prev->context 中。（注意，context 只包含 s0-s8, sp, gp, ra）
2. 恢复 next->context
3. 执行`j ra`

###### init 进程执行过程

通过 kernel_thread(init_main, NULL, 0) 创建 init 进程后

1. cpu_idle 中（idle 进程中），执行 schedule()，此时只有 idle 和 init 两个进程，因此调度到 init 进程执行 proc_run。

2. 执行 switch_to，kernel_thread 设置了 context 中的 sp, ra。执行 jr ra 后，跳转到 forkret

   ```c
   // forkret -- the first kernel entry point of a new thread/process
   // NOTE: the addr of forkret is setted in copy_thread function
   //       after switch_to, the current proc will execute here.
   static void
   forkret(void) {
       forkrets(current->tf);
   }
   
   forkrets:
     addiu sp, a0, -16
     b exception_return
     nop
   ```

3. forkrets->exception_return 从中断返回，弹出中断帧 tf。CPU 便会进入 kernel_thread_entry，并以 tf 中指定的寄存器值执行

4. kernel_thread_entry 跳转执行$a1 即 init_main

   ```assembly
   //kern/proc/entry.S
   kernel_thread_entry:        # void kernel_thread(void)
     addiu $sp, $sp, -16
     jal $a1
     nop
     move $a0, $v0
     la  $t0, do_exit
     jal $t0 
     nop
     /* never here */
   ```

###### user_main 的执行过程

1. 在 init_main 中，创建了 user_main 线程。然后 init_main 执行 do_wait

   ```c
   // init_main - the second kernel thread used to create user_main kernel threads
   static int
   init_main(void *arg) {
    ...
       int pid = kernel_thread(user_main, NULL, 0);
       if (pid <= 0) {
           panic("create user_main failed.\n");
       }
   
       while (do_wait(0, NULL) == 0) {
           schedule();
       }
   
       fs_cleanup();
       kprintf("all user-mode processes have quit.\n");
       ...
   }
   ```

2. do_wait 的作用是等待指定的或者任意一个（传入的 pid 为 0）子线程进入 ZOMBIE 状态，释放子进程的内核栈空间和 PCB 空间。否则，自己进入睡眠状态 SLEEPING，然后调用 schedule()。

   ```c
   // do_wait - wait one OR any children with PROC_ZOMBIE state, and free memory space of kernel stack
   //         - proc struct of this child.
   // NOTE: only after do_wait function, all resources of the child proces are free.
   int
   do_wait(int pid, int *code_store)
   ```

3. schedule 调用到 user_main 线程。和 init 一样，执行到 user_main 函数。

4. user_main 函数调用了 kernel_execv 函数，实质为一次 SYS_exec 系统调用。

5. 最后重新分配内核和用户空间，加载了 sh 用户程序。user_main 线程从内核线程变为用户线程。

6. 用户进程链接脚本 user.ld 指定了 ENTRY(_start)。\_start 在 user/libs/initcode.S 中定义。

   ```assembly
   _start:
       nop
       la $gp, _gp
       addiu $sp, $sp, -16
       jal umain
       nop
   ```

   umain 在 user/libs/umain.c 中定义

   ```c
   void
   umain(int argc, char *argv[]) {
       int fd;
       if ((fd = initfd(0, "stdin:", O_RDONLY)) < 0) {
           warn("open <stdin> failed: %e.\n", fd);
       }
       if ((fd = initfd(1, "stdout:", O_WRONLY)) < 0) {
           warn("open <stdout> failed: %e.\n", fd);
       }
       int ret = main(argc, argv);
       exit(ret);
   }
   ```

#### ide_init & fs_init
