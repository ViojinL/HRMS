# HRMS 项目软件测试与集成部署报告

## 1. 项目概览
HRMS 是一个基于 Django + PostgreSQL 的人力资源管理系统。为了保障代码质量和自动化发布，项目引入了完整的 CI/CD 流水线，实现了从代码提交到生产环境发布的全自动化。

---

## 2. 测试体系说明

项目采用了多层次的分级测试策略，确保代码的鲁棒性、安全性与规范性。

### 2.1 自动化单元测试 (Unit Testing)
*   **工具框架**：`pytest` + `pytest-django`
*   **测试内容**：
    *   **核心逻辑验证**：涵盖组织架构、员工管理、请假审批、考勤计算等模块。
    *   **数据模型测试**：验证数据库约束（如请假时间重叠约束）和 Triggers/Views 的正确性。
    *   **绩效算法验证**：重点测试了“规则得分”的计算公式，确保其能根据出勤率和请假率正确计算分值。
*   **覆盖率统计**：使用 `pytest-cov` 监控代码覆盖率，确保核心业务模块（`apps/`）的覆盖度超过预定阈值。

### 2.2 代码风格与规范 (Linting & Formatting)
*   **工具**：`black`
*   **目的**：统一团队代码风格。每次流水线运行都会自动格式化代码，避免因琐碎的格式问题（PEP8）导致代码合入冲突。

### 2.3 安全扫描 (Security Scan)
*   **工具**：`bandit`
*   **内容**：自动扫描 Django 源代码中的静态安全隐患（如 SQL 注入风险、危险的系统调用、不安全的加密配置等）。

---

## 3. Jenkins CI/CD 流水线设计

流水线使用 `Jenkinsfile` (Declarative Pipeline) 定义，采用容器化构建方案。

### 3.1 流水线阶段 (Stages)
1.  **Checkout**: 从 GitHub 拉取主仓最新代码。
2.  **Start DB**: 启动一个干净的侧车 (Sidecar) 数据库容器（ci/docker-compose.yml），为测试提供真实的 SQL 环境。
3.  **Install dependencies**: 在 CI 容器内安装 `requirements.txt` 中的所有依赖。
4.  **Migrate & SQL scripts**: 执行数据库迁移，并应用项目中定义的视图 (Views) 和触发器 (Triggers)。
5.  **Lint & Format**: 运行 `black` 检查并格式化代码。
6.  **Security Scan**: 运行 `bandit` 生成安全报告并存档。
7.  **Test**: 执行 `pytest`。
    *   生成 **JUnit XML** 格式结果供 Jenkins 各插件解析。
    *   使用 `--self-contained-html` 生成嵌入样式的可视化报告 (`report.html`)。
    *   生成 **HTML 代码覆盖率报告** (`htmlcov/`)。
8.  **Deploy**: 只有当上述阶段全部通过时，才会通过 SSH 登录 VPS 执行生产发布脚本。

### 3.2 部署逻辑 (Deployment)
*   **远程同步**：通过 `git config --global --add safe.directory` 信任目录，并执行 `git reset --hard` 同步。
*   **平滑重启**：运行 `docker compose up -d --build` 重新构建镜像并应用配置（如 `.env.prod`）。
*   **环境一致性**：CI 阶段删除 Compose 文件版本声明，以适配生产环境 Docker 版本。

---

## 4. 生产环境架构与 Nginx 配置

系统采用 **Nginx 反向代理 + Docker Compose** 的高性能生产方案。

### 4.1 核心架构
`客户端 (Browser)` -> `HTTPS (443)` -> `Nginx (Host)` -> `Unix Socket/TCP (8000)` -> `Python Gunicorn (Container)`

### 4.2 Nginx 的关键配置
1.  **反向代理 (Reverse Proxy)**：统一入口，支持负载均衡扩展。
2.  **静态资源优化**：Nginx 直接读取挂载的 `staticfiles` 目录，不经过 Django 逻辑，大幅提升响应速度。
3.  **安全性**：
    *   配置 `proxy_set_header X-Forwarded-Proto` 确保 Django 正确识别 HTTPS 协议。
    *   配置 `client_max_body_size` 限制文件上传大小。
4.  **SSL 证书**：由 Nginx 管理 TLS 握手， Django 只负责业务逻辑。

---

## 5. 演示数据初始化 (init_data.py)
为了支持系统演示，开发了完善的数据填充工具：
*   **驱动逻辑**：基于真实请假记录（Leave Records）反向影响考勤，进而影响绩效。
*   **分布均匀**：生成的绩效数据在 30-100 分之间自然分布，解决了“全是 100 分”的不合理现状。
*   **一键恢复**：支持 `--force` 参数快速清空并重置环境。

---
**报告日期：** 2026-01-03
**版本：** v1.2
