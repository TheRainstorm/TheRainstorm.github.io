---
title: github action 编译 openwrt
date: 2023-01-27 10:53:00
tags:
  - openwrt
  - CI
  - github-action
categories:
  - 折腾
---
<!-- more -->

## 参考

github action 基本教程：[GitHub Actions 入门教程 - 阮一峰的网络日志 (ruanyifeng.com)](https://www.ruanyifeng.com/blog/2019/09/getting-started-with-github-actions.html)
从 workflow 概念到高级用法：[About workflows - GitHub Docs](https://docs.github.com/en/actions/using-workflows/about-workflows)

## workflow 基础

- 可以有多个 workflow：For example, you can have one workflow to build and test pull requests, another workflow to deploy your application every time a release is created, and still another workflow that adds a label every time someone opens a new issue.

### 运行时机（触发一条 workflow）

- Events that occur in your workflow's repository
- Events that occur outside of GitHub and trigger a `repository_dispatch` event on GitHub
- Scheduled times
- Manual

### 例子

```yaml
name: learn-github-actions
run-name: ${{ github.actor }} is learning GitHub Actions
on: [push]
jobs:
  check-bats-version:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '14'
      - run: npm install -g bats
      - run: bats -v
```

### job 依赖 (need)

```yaml
jobs:
  setup:
    runs-on: ubuntu-latest
    steps:
      - run: ./setup_server.sh
  build:
    needs: setup
    runs-on: ubuntu-latest
    steps:
      - run: ./build_server.sh
  test:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: ./test_server.sh
```

### 重复执行 job(matrix)

重复执行 3 次，每次使用不同 nodejs 版本

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node: [12, 14, 16]
    steps:
      - uses: actions/setup-node@v3
        with:
          node-version: ${{ matrix.node }}
```

### steps.run

每个 run 都在单独的进程中

```yaml
- name: Install Dependencies
  run: npm install

# multi-line command
- name: Clean install dependencies and build
  run: |
    npm ci
    npm run build

# working dir
- name: Clean temp directory
  run: rm -rf *
  working-directory: ./temp
```

## storage(cache, )

- 使用 cache 存储不经常改变的内容，如 npm 的依赖
- 使用 artifacts 存储生成的文件以便其它 workflow 访问，如编译的二进制或 log。

cache: [Caching dependencies to speed up workflows - GitHub Docs](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows)
artifacts: [Storing workflow data as artifacts - GitHub Docs](https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts)

> For example, you can create a `key` using an expression that calculates the hash of an npm `package-lock.json` file. So, when the dependencies that make up the `package-lock.json` file change, the cache key changes and a new cache is automatically created.

```yaml
npm-${{ hashFiles('package-lock.json') }}
```

## Context 和默认环境变量

**Default environment variables:** These environment variables exist only on the runner that is executing your job.

**Contexts:** You can use most contexts at any point in your workflow, including when _default variables_ would be unavailable. For example, you can use contexts with expressions to perform initial processing before the job is routed to a runner for execution; this allows you to use a context with the conditional `if` keyword to determine whether a step should run

使用 env 定义的变量既可以在 run 中使用，也可以在 workflow 文件中使用。在 run 中使用可以使用操作系统对应的 shell 的格式读取，也可以使用 context 的格式读取。

### 定义 environment variable

```yaml
name: Greeting on variable day

on:
  workflow_dispatch

env:
  DAY_OF_WEEK: Monday

jobs:
  greeting_job:
    runs-on: ubuntu-latest
    env:
      Greeting: Hello
    steps:
      - name: "Say Hello Mona it's Monday"
        run: echo "$Greeting $First_Name. Today is $DAY_OF_WEEK!"
        env:
          First_Name: Mona
```

### 使用 Context

json 数据结构的对象。包含多种类型 Context：`github, env, jobs, steps, runner, secrets, inputs`

#### github

```json
{
  "token": "***",
  "job": "dump_contexts_to_log",
  "ref": "refs/heads/my_branch",
  "sha": "c27d339ee6075c1f744c5d4b200f7901aad2c369",
  "repository": "octocat/hello-world",
  "repository_owner": "octocat",
  "repositoryUrl": "git://github.com/octocat/hello-world.git",
  "run_id": "1536140711",
  "run_number": "314",
  "retention_days": "90",
  "run_attempt": "1",
  "actor": "octocat",
  "workflow": "Context testing",
  "head_ref": "",
  "base_ref": "",
  "event_name": "push",
  "event": {
    ...
  },
  "server_url": "https://github.com",
  "api_url": "https://api.github.com",
  "graphql_url": "https://api.github.com/graphql",
  "ref_name": "my_branch",
  "ref_protected": false,
  "ref_type": "branch",
  "secret_source": "Actions",
  "workspace": "/home/runner/work/hello-world/hello-world",
  "action": "github_step",
  "event_path": "/home/runner/work/_temp/_github_workflow/event.json",
  "action_repository": "",
  "action_ref": "",
  "path": "/home/runner/work/_temp/_runner_file_commands/add_path_b037e7b5-1c88-48e2-bf78-eaaab5e02602",
  "env": "/home/runner/work/_temp/_runner_file_commands/set_env_b037e7b5-1c88-48e2-bf78-eaaab5e02602"
}
```

#### env

```yaml
name: Hi Mascot
on: push
env:
  mascot: Mona
  super_duper_var: totally_awesome

jobs:
  windows_job:
    runs-on: windows-latest
    steps:
      - run: echo 'Hi ${{ env.mascot }}'  # Hi Mona
      - run: echo 'Hi ${{ env.mascot }}'  # Hi Octocat
        env:
          mascot: Octocat
  linux_job:
    runs-on: ubuntu-latest
    env:
      mascot: Tux
    steps:
      - run: echo 'Hi ${{ env.mascot }}'  # Hi Tux
```

#### steps

通过 id 设置 step 每步名字，之后可以获得每步的 output 等信息
> This example `steps` context shows two previous steps that had an [`id`](https://docs.github.com/en/actions/learn-github-actions/workflow-syntax-for-github-actions#jobsjob_idstepsid) specified. The first step had the `id` named `checkout`, the second `generate_number`. The `generate_number` step had an output named `random_number`.

```json
{
  "checkout": {
    "outputs": {},
    "outcome": "success",
    "conclusion": "success"
  },
  "generate_number": {
    "outputs": {
      "random_number": "1"
    },
    "outcome": "success",
    "conclusion": "success"
  }
}
```

#### runner

```json
{
  "os": "Linux",
  "arch": "X64",
  "name": "GitHub Actions 2",
  "tool_cache": "/opt/hostedtoolcache",
  "temp": "/home/runner/work/_temp"
}
```

secrets

`GITHUB_TOKEN` is a secret that is automatically created for every workflow run, and is always included in the `secrets` context
