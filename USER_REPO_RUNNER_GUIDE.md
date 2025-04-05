English | [简体中文](USER_REPO_RUNNER_GUIDE.md)

# EMS Test Guide for User Repo Runner
In [EMS TEST](./README-CN.md), we deployed the `self-hosted-runners` under the `taosdata` organization. This document guides users on how to create runners in their personal repositories and execute these tests.

# Table of Contents
- [EMS Test Guide for User Repo Runner](#ems-test-guide-for-user-repo-runner)
- [Table of Contents](#table-of-contents)
  - [1. Obtain Workflow](#1-obtain-workflow)
    - [1.1 Fork Repository](#11-fork-repository)
    - [1.2 Clone Code to Personal Repository](#12-clone-code-to-personal-repository)
  - [2. Configure the Following Secrets](#2-configure-the-following-secrets)
  - [3. Prepare Runners](#3-prepare-runners)
  - [4. Modify Workflow](#4-modify-workflow)
  - [5. Execute Workflow](#5-execute-workflow)

## 1. Obtain Workflow
Two methods are provided to obtain the workflow:

### 1.1 Fork Repository
Log in to your personal GitHub account, navigate to the [taosdata/ems](https://github.com/taosdata/ems) repository, and fork it to your personal account.

### 1.2 Clone Code to Personal Repository
```bash
# 1. Clone ems repo
git clone https://github.com/taosdata/ems.git
# 2. Create a new repository in your GitHub account
# ...
# 3. Add remote and push
cd ems
git remote add your-ems git@github.com:jiajayden/your-ems.git
git push your-ems main
```

## 2. Configure the Following Secrets
| Secret Name   | Description                      |
|---------------|----------------------------------|
| VM_PASSWD     | Unified login password for personal runners |
| RUNNER_PAT    | Personal Access Token for your account |
| PUB_DL_URL    | URL for downloading public dependencies (contact us to obtain) |
| ASSETS_DL_URL | URL for downloading TDengine Enterprise Edition (contact us to obtain) |

## 3. Prepare Runners
```markdown
Configure appropriate labels. Since this test requires pre-assembling all necessary runners into a complete environment, each runner needs unique labels to avoid duplicate references caused by network latency.
```

## 4. Modify Workflow
- Update the env fields in the workflow: MQTT_LABEL, EDGE_LABEL, CENTER_LABEL, and CLIENT_LABEL
- Modify the custom actions that reference get-runners and dynamic-labels, specifically the scope and target parameters which are components of the runner API
- Update all runs-on fields:
  - For organization runners with group settings, add group options to runs-on
  - For personal repository runners, simply remove the group field

## 5. Execute Workflow
```markdown
Navigate to the Actions page and execute the workflow
```