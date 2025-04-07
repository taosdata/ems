
English | [简体中文](USER-REPO-TEST-GUIDE-CN.md)

# EMS Test Guide for User Repo Runner
This document guides users to create self-hosted runners in personal repositories and execute tests, based on the [EMS TEST](./README-CN.md) deployment under the `taosdata` organization.

# Table of Contents
- [EMS Test Guide for User Repo Runner](#ems-test-guide-for-user-repo-runner)
- [Table of Contents](#table-of-contents)
  - [1. Obtaining Workflow](#1-obtaining-workflow)
  - [2. Setting Secrets](#2-setting-secrets)
  - [3. Preparing Runners](#3-preparing-runners)
    - [3.1 Creating Self-hosted Runners](#31-creating-self-hosted-runners)
    - [3.2 Label Management](#32-label-management)
  - [4. Modifying Workflow](#4-modifying-workflow)
  - [5. Executing Workflow](#5-executing-workflow)

## 1. Obtaining Workflow

Two methods to obtain workflow:

| Method              | Steps/Command Examples                                      |
|---------------------|------------------------------------------------------------|
| **Fork Repository** | 1. Log in to GitHub account                                |
|                     | 2. Visit [taosdata/ems](https://github.com/taosdata/ems)   |
|                     | 3. Click `Fork` button                                     |
| **Local Clone**     | # First create personal repo & configure SSH key          |
|                     | git clone https://github.com/taosdata/ems.git              |
|                     | cd ems                                                     |
|                     | git remote add your-repo-name git@github.com:your-account/your-repo.git |
|                     | git push your-repo-name main                               |

## 2. Setting Secrets
Configure via GitHub: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

| Secret Name   | Description                                  |
|---------------|----------------------------------------------|
| VM_PASSWD     | Unified login password for personal runners  |
| RUNNER_PAT    | Personal access token                        |
| PUB_DL_URL    | Test tool download URL (Contact us)          |
| ASSETS_DL_URL | Enterprise TDengine download URL (Contact us)|

## 3. Preparing Runners

### 3.1 Creating Self-hosted Runners
Refer to official guide: [adding-self-hosted-runners](https://docs.github.com/en/actions/hosting-your-own-runners/managing-self-hosted-runners/adding-self-hosted-runners)

### 3.2 Label Management

> **NOTE:**
> To prevent duplicate references from identical labels under network latency, each runner's label combinations must be unique. We recommend using <b>resource+hostname</b> format, allowing both resource-based random matching and hostname-specific precision matching.

Label configuration example:

| Role          | Labels                                  | Description                                                                 |
|---------------|-----------------------------------------|-----------------------------------------------------------------------------|
| MQTT Node     | 8C16G, u2-191<br>8C16G, u2-192          | 2 MQTT nodes required, quantity must match edge nodes                      |
| Edge Node     | 20C16G, u2-193<br>20C16G, u2-194        | 2 edge nodes required, quantity must match MQTT nodes                      |
| Center Node   | 20C16G, exclusive, u2-195<br>20C16G, exclusive, u2-196<br>20C16G, exclusive, u2-197 | 3 center nodes, `exclusive` indicates dedicated physical machine |
| Client Node   | 24C64G, u2-190                          | 1 client node configured                                                 |

## 4. Modifying Workflow

> **NOTE:**
> - For organization-hosted runners: Use【[ .github/workflow/ems-test.yml ](.github/workflows/ems-test.yml)】
>
> - For personal account runners: Use 【[ .github/workflow/ems-test-for-user-repo.yml.demo ](.github/workflows/ems-test-for-user-repo.yml.demo)】 (remove group info)

Required modifications:

| ENV           | Description                                                       |
|---------------|-------------------------------------------------------------------|
| MQTT_LABEL    | Target label for MQTT nodes                                       |
| EDGE_LABEL    | Target label for edge nodes                                       |
| CENTER_LABEL  | Target label for center nodes                                     |
| CLIENT_LABEL  | Target label for client nodes                                     |
| SCOPE         | Repository scope: `org` (organization) or `repo` (personal)       |
| TARGET        | Repository name format: `github_account_name/repo_name` for personal |

## 5. Executing Workflow
Navigate to `Actions` page to run the workflow.
