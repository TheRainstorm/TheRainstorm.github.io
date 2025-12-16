---
title: hexo 迁移到 mkdoc
date: 2024-01-07 21:47:39
tags:
  - hexo
  - mkdocs
  - cloudfare
  - obsidian
  - markdownlint-cli
categories:
  - 折腾记录
---
我比较喜欢 hexo 的 tags 字云的效果，不过由于以下原因，我打算迁移到新的静态博客框架 mkdocs material theme

- hexo nodejs 的依赖实在是太麻烦了
- hexo 展示的信息量太少了（也可能是我使用的模板的问题）
  - 我感觉这一点上 mkdoc 效果就很好，在大显示器上能够显示更多信息，查阅博客的效率更高

TODO

- [ ] 集成评论区：[Adding a comment system - Material for MkDocs (squidfunk.github.io)](https://squidfunk.github.io/mkdocs-material/setup/adding-a-comment-system/)
- [ ] 看板娘

参考方案

- [杰哥的{运维，编程，调板子}小笔记 (jia.je)](https://jia.je/)
- [jiegec/blog-source: The source of my blog. (github.com)](https://github.com/jiegec/blog-source/tree/master)
- [ヾ (^▽^*))) 欢迎回来~ (shaojiemike.top)](https://shaojiemike.top/)

*p.s. 由于我使用的 markdown 编辑器的原因，才发现标准 MD 中 list 前面需要有一个空行。也就是迄今写的博客均踩了这个坑。。。而 mkdocs 不支持这个非标准行为，以后慢慢更正吧*

<!-- more -->
## mkdocs 教程

### install & run

安装 mkdocs 非常简单

```
pip install mkdocs-material
```

运行本地服务器

```
mkdocs serve -a 0.0.0.0:8000
```

生成静态页面，默认输出到`site/`目录

```
mkdocs build
```

### 配置

只有一个配置文件 mkdocs.yml

```
mkdocs new .
```

```
.
├─ docs/
│  └─ index.md
└─ mkdocs.yml
```

## mkdocs blog 支持

[Setting up a blog - Material for MkDocs (squidfunk.github.io)](https://squidfunk.github.io/mkdocs-material/setup/setting-up-a-blog/)

### tags 索引页面

category 和 archive 页面是自动生成的，tags 页面需要手动配置
> mkdocs automatically generating [archive](https://squidfunk.github.io/mkdocs-material/plugins/blog/#archive) and [category](https://squidfunk.github.io/mkdocs-material/plugins/blog/#categories) indexes, [post slugs](https://squidfunk.github.io/mkdocs-material/plugins/blog/#config.post_url_format), configurable [pagination](https://squidfunk.github.io/mkdocs-material/plugins/blog/#pagination) and more.

想要创建一个页面包含所有 tag 索引，需要创建`docs/tags.md`，内容如下

```
# 标签

[TAGS]
```

mkdocs 启用 tags plugin

```yml
plugins:
  - tags:
      # enabled: !ENV [DEPLOY, false]
      enabled: true
      tags_file: tags.md
```

### 其它

#### excerpt

使用`<!-- more -->`分隔博客
*p.s 中间必须保留空格，使用`<!--more-->`无法生效*

#### authors

create the `.authors.yml` file in your blog directory

```yml
authors:
  squidfunk:
    name: Martin Donath
    description: Creator
    avatar: https://github.com/squidfunk.png
```

然后就可以在文档的元数据中添加 author 列表

#### linking

> While [post URLs](https://squidfunk.github.io/mkdocs-material/plugins/blog/#config.post_url_format) are dynamically computed, the [built-in blog plugin](https://squidfunk.github.io/mkdocs-material/plugins/blog/) ensures that all links from and to posts and a post's assets are correct.

文档中链接到另一个文档

```
[Hello World!](blog/posts/hello-world.md)
```

链接到一个页面，只需要指向该页面的索引 md 文件

```
[Blog](../index.md)
```

#### readtime

显示文章的预计阅读时间。自动启用，如果嫌估计的不准确，可以手动设置

```
---
date: 2023-01-31
readtime: 15
---
```

### 问题

#### 没有 category 页面

build 后才会生成，直接 serve 是看不到的

### 有用的 Plugin

#### meta

可以为一个目录的所有文件设置基础 meta 信息，在分门别类存储博客时比较有用。但是目前是需要付费才能使用
**Sponsors only** – this plugin is currently reserved to [our awesome sponsors](https://squidfunk.github.io/mkdocs-material/insiders/).

[Built-in meta plugin - Material for MkDocs (squidfunk.github.io)](https://squidfunk.github.io/mkdocs-material/plugins/meta/)
The meta plugin solves the problem of setting metadata (front matter) for all pages in a folder, i.e., a subsection of your project, which is particularly useful to ensure that a certain subset of pages features specific tags, uses a custom template, or is attributed to an author.

## 静态网站部署

### cloudfare page

参考资料：

- mkdocs+cf page 资料：[Deploy MkDocs with Material or Material Insiders theme to Cloudflare Pages - Starfall Projects](https://www.starfallprojects.co.uk/projects/deploy-host-docs/deploy-mkdocs-material-cloudflare/#site-setup)
- cf page 文档：[Get started guide · Cloudflare Pages docs](https://developers.cloudflare.com/pages/get-started/guide/)
- cloudflare build platform 介绍：[Modernizing the toolbox for Cloudflare Pages builds](https://blog.cloudflare.com/moderizing-cloudflare-pages-builds-toolbox/)

cf page 优势

- cf page 支持很多 preset（各种静态网站框架），mkdocs 是其中之一，因此配置非常简单。
  - gh page 只支持 Jekyll，其它需要自定义 workflow 来生成 html 页面
- 支持设置 **Production branch** 和 **Preview branch**，监听不同 git 分支
- 支持选择不同的 build platform，目前有 ubuntu22.04 和 ubuntu20.04

*注意：需要配置`requirements.txt`文件告诉 cf 安装依赖，否则 cf build 时会报错`mkdocs not found`*

```
mkdocs-material
mkdocs-material-extensions
mkdocs-git-revision-date-localized-plugin
mkdocs-wavedrom-plugin
mkdocs-rss-plugin
```

配置 custom domain 时直接添加域名即可

### github page

由于原本已经创建过 github page 了，本以为无法再创建新的 github page，然后发现 github 支持多种 page！

- user, organization page 是账户性质的 page，对应`<username>.github.io`或`<organization>.github.io`的仓库
- project page 则没有限制，可以创建任意多个，通过`http(s)://<username>.github.io/<repository>`访问。
  - private 仓库创建 public page 需要 github pro 以上

参考文档

- 关于 gh page 类型，限制：[About GitHub Pages - GitHub Docs](https://docs.github.com/en/pages/getting-started-with-github-pages/about-github-pages#types-of-github-pages-sites)
- 配置 publishing source：[Configuring a publishing source for your GitHub Pages site - GitHub Docs](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- mkdocs 关于 deploy 文档（github 和 gitlab）：[Publishing your site - Material for MkDocs (squidfunk.github.io)](https://squidfunk.github.io/mkdocs-material/publishing-your-site/?h=deploy)

#### 配置 publishing source

有两种配置 page source 方法

- deploy from a branch：通常对应一个 gh-page 分支，只包含静态 html 文件
  - 可以是本地使用类似`hexo deploy`, `mkdocs gh-deploy`命令生成，然后 push 到 github 分支
  - 也可以是自定义 gh workflow，生成然后 push 到 gh-page 分支。Most external CI workflows "deploy" to GitHub Pages by committing the build output to the `gh-pages` branch of the repository, and typically include a `.nojekyll` file.
- github action
  - 也是先通过 action 生成静态网站文件，最后通过 [`actions/upload-pages-artifact`](https://github.com/actions/upload-pages-artifact) 和 [`actions/deploy-pages`](https://github.com/actions/deploy-pages)发布到 gh page。

mkdocs 官方提供的方式是方式 1，使用它的 workflow 脚本，会自动生成静态网站文件并 push 到 gh-page 分支。
*p.s 需要修改其中 pip install 命令，补充完依赖*

#### 配置 custom domain

> Under "Custom domain", type your custom domain, then click **Save**. If you are publishing your site from a branch, this will create a commit that adds a `CNAME` file directly to the root of your source branch. If you are publishing your site with a custom GitHub Actions workflow, no `CNAME` file is created.

配置 custom domain

- 域名解析服务提供商：添加一条 CNAME record，指向 user.github.io
- github
  - 对于 source 为 deploy from a branch，在`/`路径添加 CNAME 文件，包含 CNAME 名（通过 setting 中设置，也会自动创建该 CNAME 文件）
  - 对于 source 为 github action，通过 setting 设置即可，不会创建 CNAME 文件
如果已经创建过 user 或 organization site，则创建 project site 时会自动使用之前的域名

## markdown 格式修复

原本写的 markdown 文件有一些格式不太规范（常见错误[^1]），切换成 mkdocs 后，有许多报错信息。以下列出其中一些问题，并且提供一个自动修复脚本[fix_markdown.py](../../code/fix_markdown.py)，避免一些枯燥的手动修改。

[^1]: [A few common Markdown mistakes (github.com)](https://gist.github.com/DavidAnson/006a6c2a2d9d7b21b025)

### metadata

markdown 开头部分可以定义一些元数据，如作者，日期等，这部分叫做 frontmatter。通常采用 yaml 格式。

日期只能使用`YY-mm-dd`或者`YY-mm-dd HH:MM:SS`，像`2023-04-20 16:22`这样的格式是无法识别的

```
ERROR   -  Error reading metadata 'date' of post 'blog/posts/2023-04-20-具体数学.md' in 'docs':
           Expected type: <class 'datetime.date'> or <class 'datetime.datetime'> but received: <class 'str'>
```

脚本支持修复该问题。

我使用 obsidian 的 Template 功能来自动生成 metadata，其默认生成的时间格式是不带秒的时间格式，因而导致了以上问题。

可以自定义其模板时间格式：[Templates - Obsidian Help](https://help.obsidian.md/Plugins/Templates)
修正后模板如下：

```
---
title: {{title}}
date: {{date}} {{time:HH:mm:ss}}
tags:
- linux
categories:
- 折腾
---

<!-- more -->
```

### 图片链接

原本使用了两种格式`/images/xxx/xxx.png`, `images/xxx/xxx.png`的图片链接，导致报错

```
Doc file 'blog/posts/2023-04-20-具体数学.md' contains a relative link 'images/具体数学/image-20220607171500766.png', but the target
           'blog/posts/images/具体数学/image-20220607171500766.png' is not found among documentation files
```

mkdocs 所有链接均使用相对路径，改为相对于 md 文件的路径即可。
*p.s 这里不得不提下 obsidian 的方便之处了。obsidian 采用了尽可能匹配的原则，因此只要文件名相同，无论位于哪个目录下，均能正确匹配*

使用正则修改关键代码如下

```python
RE = fr'!\[(.*?)\]\(/{old_prefix}(.*?)\)'   # old_prefix = images/
m1 = re.findall(RE, content)
if m1:
  content = re.sub(RE, f'![\g<1>]({new_prefix}\g<2>)', content)
```

### 内部链接

[Setting up a blog - Material for MkDocs (squidfunk.github.io)](https://squidfunk.github.io/mkdocs-material/setup/setting-up-a-blog/?h=relative+link#linking-from-and-to-posts)

mkdocs 使用相对路径，指向引用的 md 文件，并且也支持使用`#`定位到特定 section。原本 hexo 的链接格式则复杂多了。
由于数目不多，手动修改即可。

```
[openwrt配置#ipv6](2022-02-13-openwrt配置.md#ipv6)
```

*p.s obsidan 同样支持定位到另一个 markdown 文档，并且不用太在意路径*

### 数学公式

[Math - Material for MkDocs (squidfunk.github.io)](https://squidfunk.github.io/mkdocs-material/reference/math/)
有 MathJax 和 KaTex 两个选择

- **Speed**: KaTeX is generally faster than MathJax. If your site requires rendering large quantities of complex equations quickly, KaTeX may be the better choice.
- **Syntax Support**: MathJax supports a wider array of LaTeX commands and can process a variety of mathematical markup languages (like AsciiMath and MathML). If you need advanced LaTeX features, MathJax may be more suitable.

但是使用两种方案，据无法正确显示我的[具体数学](2023-04-20-具体数学.md)那篇文章的所有数学公式，并且 MathJax 正确识别的更少。因此最后选用了 KaTeX

### 列表前空行

markdown 标准语法中，block 元素前后都需要空行。但是 obsidan 支持不加空行， github 也支持 list 前面不加空行。

别人关于是否需要支持这个常见“错误”的讨论
[Blank lines before lists, revisited - Spec - CommonMark Discussion](https://talk.commonmark.org/t/blank-lines-before-lists-revisited/1990/35)

修复办法

- cd 到包含 md 的目录
- 运行 markdownlint-cli2
  - 其中 `**` 匹配任意符号，`*` 匹配除 `/` 外符号。因此 `**/*.md` 表示当前目录及子目录下所有 md 文件。
  - `#node_modules` 作为第二个参数同样是用于匹配文件。不过 `#` 用于取消（negate）匹配。因此该参数作用是排除 node_modules 目录，避免索引太多文件。
  - `--fix` 参数用于修改源文件

```shell
docker run -v $PWD:/workdir davidanson/markdownlint-cli2:v0.13.0 "**/*.md" "#node_modules" --fix
```

## mkdocs 扩展格式

mkdocs 将 markdown 许多扩展语法都作为插件开启，比如 footnotes。

### 箴言 Admonition

[Admonitions - Material for MkDocs (squidfunk.github.io)](https://squidfunk.github.io/mkdocs-material/reference/admonitions/)

- 默认标题为 note
- `!!! note ""` 不使用标题

=== "箴言"

    !!! note "Phasellus posuere in sem ut cursus"
    
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla et euismod
        nulla. Curabitur feugiat, tortor non consequat finibus, justo purus auctor
        massa, nec semper lorem quam in massa.

=== "Source"

    ```
    !!! note "Phasellus posuere in sem ut cursus"
    
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla et euismod
        nulla. Curabitur feugiat, tortor non consequat finibus, justo purus auctor
        massa, nec semper lorem quam in massa.
    ```

- 使用 `???` 表示可折叠的块
- `???+` 默认展开

=== "Collapsible blocks"

    ???+ note
    
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla et euismod
        nulla. Curabitur feugiat, tortor non consequat finibus, justo purus auctor
        massa, nec semper lorem quam in massa.

=== "Source"

    ```
    ???+ note
    
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla et euismod
        nulla. Curabitur feugiat, tortor non consequat finibus, justo purus auctor
        massa, nec semper lorem quam in massa.
    ```

其它类型见 <https://squidfunk.github.io/mkdocs-material/reference/admonitions/#supported-types>

### footnotes

[Footnotes - Material for MkDocs (squidfunk.github.io)](https://squidfunk.github.io/mkdocs-material/reference/footnotes/)

```markdown
Lorem ipsum[^1] dolor sit amet, consectetur adipiscing elit.[^2]

[^1]: Lorem ipsum dolor sit amet, consectetur adipiscing elit.

[^2]:
    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla et euismod
    nulla. Curabitur feugiat, tortor non consequat finibus, justo purus auctor
    massa, nec semper lorem quam in massa.
```

Lorem ipsum[^1] dolor sit amet, consectetur adipiscing elit.[^2]


[^2]:
    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla et euismod
    nulla. Curabitur feugiat, tortor non consequat finibus, justo purus auctor
    massa, nec semper lorem quam in massa.

### highlighting

对文本进行多种突出：高亮、下划线、删除线。

[Formatting - Material for MkDocs (squidfunk.github.io)](https://squidfunk.github.io/mkdocs-material/reference/formatting/)

#### Highlighting text

=== "Highlighting text"

    - ==This was marked (highlight)==
    - This was inserted (underline)
    - ~~This was deleted (strikethrough)~~

=== "Source"

    ```markdown
    - ==This was marked (highlight)==
    - ^^This was inserted (underline)^^
    - ~~This was deleted (strikethrough)~~
    ```

#### Sub- and superscripts

=== "Sub- and superscripts"

    - H~2~O
    - A^T^A

=== "Source"

    ```
    - H~2~O
    - A^T^A
    ```

### Content tabs

创建 Tab 切换显示的内容。

[Content tabs - Material for MkDocs (squidfunk.github.io)](https://squidfunk.github.io/mkdocs-material/reference/content-tabs/)

=== "C"

    ``` c
    #include <stdio.h>

    int main(void) {
      printf("Hello world!\n");
      return 0;
    }
    ```

=== "C++"

    ``` c++
    #include <iostream>

    int main(void) {
      std::cout << "Hello world!" << std::endl;
      return 0;
    }
    ```

=== "Source"

    ```
    === "C"
    
        ``` c
        #include <stdio.h>
    
        int main(void) {
          printf("Hello world!\n");
          return 0;
        }
        ```
    
    === "C++"
    
        ``` c++
        #include <iostream>
    
        int main(void) {
          std::cout << "Hello world!" << std::endl;
          return 0;
        }
        ```
    ```

### diagrams

[Diagrams - Material for MkDocs (squidfunk.github.io)](https://squidfunk.github.io/mkdocs-material/reference/diagrams/)

> Material for MkDocs integrates with [Mermaid.js](https://mermaid.js.org/), a very popular and flexible solution for drawing diagrams.

**obsidian 同样支持显示该格式。**

=== "diagrams"

    ``` mermaid
    graph LR
      A[Start] --> B{Error?};
      B -->|Yes| C[Hmm...];
      C --> D[Debug];
      D --> B;
      B ---->|No| E[Yay!];
    ```

=== "Source"

    ```text
    graph LR
      A[Start] --> B{Error?};
      B -->|Yes| C[Hmm...];
      C --> D[Debug];
      D --> B;
      B ---->|No| E[Yay!];
    ```

其它格式参见：[State diagrams | Mermaid](https://mermaid.js.org/syntax/stateDiagram.html)

### 其它

math: [Math - Material for MkDocs (squidfunk.github.io)](https://squidfunk.github.io/mkdocs-material/reference/math/)
task list: [Lists - Material for MkDocs (squidfunk.github.io)](https://squidfunk.github.io/mkdocs-material/reference/lists/)
