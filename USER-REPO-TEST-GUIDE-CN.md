简体中文 | [English](USER-REPO-TEST-GUIDE.md)

# EMS Test Guide for User Repo Runner
在【[ EMS TEST ]( ./README-CN.md )】中我们将 `self-hosted-runners` 部署在 `taosdata` 组织下，本文将指导用户如何在个人仓库下创建 runner 并执行这个测试。

# 目录
- [EMS Test Guide for User Repo Runner](#ems-test-guide-for-user-repo-runner)
- [目录](#目录)
  - [1. 获取 Workflow](#1-获取-workflow)
  - [2.设置 Secrets](#2设置-secrets)
  - [3.准备 Runners](#3准备-runners)
    - [3.1 创建 self-hosted-runners](#31-创建-self-hosted-runners)
    - [3.2 标签管理](#32-标签管理)
  - [4.修改 Workflow](#4修改-workflow)
  - [5.运行 Workflow](#5运行-workflow)


## 1. 获取 Workflow

这里提供两种方式来获取 Workflow

| 方式              |  操作步骤/命令示例                                              |
|------------------|--------------------------------------------------------------|
|   **Fork 仓库**   | 登录 `GitHub` 账号                                               |
|                  | 访问 [taosdata/ems](https://github.com/taosdata/ems)          |
|                  | 点击右上角 `Fork` 按钮                                          |
| **克隆代码到本地** | # 先创建个人新仓库并配置 ssh key（需在 GitHub 网页端操作）           |
|                  | `git clone https://github.com/taosdata/ems.git`               |
|                  | `cd ems`                                                        |
|                  | `git remote add your-repo-name git@github.com:github-account-name/your-repo-name.git` |
|                  | `git push your-repo-name main`                                        |


## 2.设置 Secrets

Github 网页端进入对应仓库后，点击 `Settints` -> `Secrets and variables` -> `Actions` -> `New repository secret` 新建 `secrets`

| Secret Name   | Description                      |
|---------------|----------------------------------|
| VM_PASSWD     | 个人 runner 的统一登录密码            |
| RUNNER_PAT    | 个人账号的 persional access token, 需要勾选 repo、workflow、admin:org 权限  |
| PUB_DL_URL    | 测试工具下载地址，联系我们获取       |
| ASSETS_DL_URL | 企业版 TDengine 下载地址，联系我们获取 |

## 3.准备 Runners

### 3.1 创建 self-hosted-runners

self-hosted runners 部署教程可参考 [adding-self-hosted-runners](https://docs.github.com/en/actions/hosting-your-own-runners/managing-self-hosted-runners/adding-self-hosted-runners)


### 3.2 标签管理

> **NOTE:**
> 因为这个测试要将所需 runner 提前组成一整套环境，为了避免网络延迟时相同标签带来的重复引用，每个 runner 的标签组合需要具有唯一性，建议以资源+主机名的组合来设置标签，这样既可以单独使用资源标签随机匹配 runner，也可以使用主机名精确匹配 runner


以下是本测试的一组标签的示例：

|  角色      | 标签名                                | Description                                                      |
|-----------|--------------------------------------|------------------------------------------------------------------|
| MQTT 节点  | 8C16G, u2-191<br>8C16G, u2-192       | MQTT 节点标签，本测试有 2 个，数量需要和边缘节点对应                     |
| 边缘节点    | 20C16G, u2-193<br>20C16G, u2-194     | 边缘节点标签，本测试有 2 个，数量需要和 MQTT 节点对应                    |
| 中心节点    | 20C16G, exclusive, u2-195<br>20C16G, exclusive, u2-196<br>20C16G, exclusive, u2-197  |中心节点标签，本测试有 3 个，exclusive标签表示这台虚拟机独占了一台物理机    |
| 客户端节点  | 24C64G, u2-190                      |客户端节点标签，本测试只设置了 1 个                                    |


## 4.修改 Workflow

> **NOTE:**
> - 如果您的 self-hosted-runners 位于组织下，可使用 【[ .github/workflow/ems-test.yml ](.github/workflows/ems-test.yml)】
>
> - 如果您的 self-hosted-runners 位于个人账号下，需要删除 workflow 中 runner 的 group 信息，可使用 【[ .github/workflow/ems-test-for-user-repo.yml.demo ](.github/workflows/ems-test-for-user-repo.yml.demo)】


以下信息需要您手动修改:


|  ENV          | Description                                                      |
|---------------|------------------------------------------------------------------|
| MQTT_LABEL    | MQTT 节点需要匹配的 `runner` 标签                                     |
| EDGE_LABEL    | 边缘节点需要匹配的 `runner` 标签                                       |
| CENTER_LABEL  | 中心节点需要匹配的 `runner` 标签                                       |
| CLIENT_LABEL  | 客户端节点需要匹配的 `runner` 标签                                     |
| SCOPE         | 仓库是位于组织下还是个人账号下，仅支持设置为 `org` 或者 `repo`             |
| TARGET        | 仓库名，如果仓库在个人账号下，需要命名为 `github_account_name/repo_name` |

## 5.运行 Workflow

进入 `Actions` 页面运行 Workflow
