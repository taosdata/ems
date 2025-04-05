简体中文 | [English](README.md)

# EMS Test Guide for User Repo Runner
在【[ EMS TEST ]( ./README-CN.md )】中我们将 self-hosted-runner 部署在 taosdata 组织下，本文将指导用户如何在个人仓库下创建 runner 并执行这个测试

# 目录
- [EMS Test Guide for User Repo Runner](#ems-test-guide-for-user-repo-runner)
- [目录](#目录)
  - [1. 获取 workflow](#1-获取-workflow)
    - [1.1 Fork Repo](#11-fork-repo)
    - [1.2 在个人仓库中克隆代码](#12-在个人仓库中克隆代码)
  - [2.设置以下 secrets](#2设置以下-secrets)
  - [3.准备 runners](#3准备-runners)
  - [4.修改 workflow](#4修改-workflow)
  - [5.运行 workflow](#5运行-workflow)


## 1. 获取 workflow
这里提供两种方式来获取 Workflow
### 1.1 Fork Repo
登录个人 Github 账号进入 [taosdata/ems](https://github.com/taosdata/ems) 仓库，然后 Fork 到个人账号下。
### 1.2 在个人仓库中克隆代码
```bash
# 1.Clone ems repo
git clone https://github.com/taosdata/ems.git
# 2.You need create a new repo in your github
# ...
# 3.Remote add and push
cd ems
git remote add your-ems git@github.com:jiajayden/your-ems.git
git push your-ems main
```

## 2.设置以下 secrets
| Secret Name   | Description                      |
|---------------|----------------------------------|
| VM_PASSWD     | 个人runner的统一登录密码            |
| RUNNER_PAT    | 个人账号的 persional access token  |
| PUB_DL_URL    | 下载公共依赖的地址，联系我们获取       |
| ASSETS_DL_URL | 下载企业版TDengine的地址，联系我们获取 |

## 3.准备 runners
```markdown
设置好对应的标签，因为这个测试要将所需 runner 提前组成一整套环境，为了避免网络延迟时标签重复带来的重复引用，每个 runner 需要有独特的标签；
```

## 4.修改 workflow
- workflow 中的 env 字段分别修改 MQTT_LABEL、EDGE_LABEL、CENTER_LABEL、CLIENT_LABEL 的信息；
- 修改自定义action引用了 get-runners 和 dynamic-labels 的 scope 和 target 参数，这两个参数是 runner api 的组成部分；
- 修改所有的 runs-on 字段，如果是组织内的 runner 且设置了 group，runs-on 字段需要增加 group 选项，如果是个人仓库的 runner，那么删除 group 字段即可

## 5.运行 workflow
```markdown
进入 action 页面并运行 workflow
```
