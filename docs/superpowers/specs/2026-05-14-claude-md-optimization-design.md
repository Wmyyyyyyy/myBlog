# CLAUDE.md Optimization Design

**Date:** 2026-05-14
**Goal:** Optimize CLAUDE.md for clarity, completeness, and strict execution

## 1. Project Overview

**Purpose:** Quick reference for project context and development setup

**Content:**
- Tech stack summary (Vue 3 + FastAPI + PostgreSQL + Redis + Celery)
- Key features list
- Prerequisites
- Running commands (Backend, Frontend, Celery)

## 2. Architecture

**Purpose:** Unified code organization conventions

**Content:**
- Backend directory structure with module responsibilities
- Frontend directory structure
- Database design principles (async SQLAlchemy, Redis usage)
- Key technical decisions (DFA algorithm, image storage, API response format)

## 3. Development Guidelines

**Purpose:** Coding behavior guidelines

### 3.1 Core Principles (Andrej Karpathy)

保留现有四个核心原则：
1. 编码前思考 — 不要假设，不确定时询问
2. 简洁优先 — 最少代码解决问题，不 speculative
3. 精准修改 — 只改该改的，不碰无关代码
4. 目标驱动执行 — 定义可验证成功标准

### 3.2 Git 工作流

**分支策略：**
- `master` — 主分支，保护分支
- 功能开发使用 feature 分支
- 命名规范：`feature/功能名`、`fix/bug描述`

**Commit 规范：**
- 格式：`<type>: <description>`
- Type：feat、fix、refactor、test、docs、chore
- 示例：`feat: add user authentication`

**PR 流程：**
1. 功能完成后创建 PR
2. 必须经过 Code Review
3. CI 通过后合并
4. 合并后删除分支

### 3.3 API 规范

**路径命名：**
- 使用复数名词：`/api/users`、`/api/blogs`
- 嵌套资源：`/api/blogs/{id}/comments`

**版本控制：**
- URL 路径版本：`/api/v1/users`
- 保持向后兼容

**错误码约定：**
```json
{"code": 0, "message": "success", "data": {...}}
{"code": 40001, "message": "Validation error", "errors": {...}}
```
错误码结构：`<模块><序号>`，如 40001 = 通用模块验证错误

## 4. Testing & Quality

**Purpose:** Ensure code correctness

**Content:**
- Backend: pytest + pytest-asyncio + httpx
- Frontend: vitest + @vue/test-utils + Playwright E2E
- CI/CD: GitHub Actions with Docker Compose

## 5. Execution Rules

**Purpose:** Enforce strict execution process

### 5.1 TDD 强制

- 所有新功能必须先写测试
- 测试失败后才能写实现代码
- 重构前后必须保证测试通过

### 5.2 Code Review 强制

- 提交前必须进行 self-review
- 检查：是否遵循 Core Principles、是否有死代码、是否匹配现有风格

### 5.3 Simplify 强制

- 每次提交代码前自动调用 simplify skill 进行代码审查
- 修改涉及多个文件时，必须使用 `/simplify` 检查代码复用性、质量和效率问题

### 5.4 Debugging 规则

- 遇到 bug 必须先调用 debugging skill
- 修复后 grep 相似模式，防止遗漏

### 5.5 Cross-Testing 规则

- 后端修改后立即测试前端对应组件
- 前端修改后立即测试后端对应组件

## 6. Subagent Usage

**Purpose:** Parallel task execution

- 每次对话开始时，自动评估是否需要启动子代理（Agent 工具）来并行执行独立任务

---

## 新 CLAUDE.md 结构

```
1. 项目基础（Project Overview + Environment）
2. 架构规范（Architecture）
3. 开发规范（Development Guidelines）
   3.1 Core Principles
   3.2 Git 工作流
   3.3 API 规范
4. 测试与质量（Testing & Quality）
5. 执行规则（Execution Rules）
   5.1 TDD 强制
   5.2 Code Review 强制
   5.3 Simplify 强制
   5.4 Debugging 规则
   5.5 Cross-Testing 规则
6. Subagent Usage
```

## Changes Summary

**精简内容：**
- 移除重复的 Common Tasks 示例（保留核心决策说明）
- 合并 Testing 章节

**补充内容：**
- Git 工作流（分支策略、Commit 规范、PR 流程）
- API 规范（路径命名、版本控制、错误码约定）

**强化执行：**
- TDD 强制要求
- Code Review self-review 清单
- Simplify 强制调用
- Debugging 规则明确化
