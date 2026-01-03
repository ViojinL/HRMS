# 部署进度说明（本机 + VPS）

## 本机（Windows）

- 克隆并修改项目，新增 CI/CD 相关文件：`Dockerfile`、`docker-compose.prod.yml`、`scripts/entrypoint.sh`、`Jenkinsfile`，完善 `README.md` 生产部署说明，提供 `.env.prod.example`。
- 生成部署 SSH 密钥对：`deploy-ci-key`（私钥，留在本机并用于 Jenkins Credentials `vps-deploy-key`）和 `deploy-ci-key.pub`（公钥，待写入 VPS 的 `/home/deploy/.ssh/authorized_keys`）。
- 本地验证：已完成 `black`/`ruff` 修复，`python manage.py test apps.performance` 通过；可用 `ci/docker-compose.yml` 启动 CI 环境 Postgres。

## VPS

- 创建部署用户 `deploy`（无密码登录，仅 SSH key），已加入 `docker` 组；部署目录 `/srv/hrms` 已创建。
- Nginx：已添加 hrms 站点配置，反代到 `127.0.0.1:8000`，静态目录规划 `/srv/hrms/staticfiles`；域名 `hrms.kohinbox.top` 在 Cloudflare 上配置 SSL。
- 待完成：
  - 以 deploy 身份：`git clone https://github.com/ViojinL/HRMS.git .` 到 `/srv/hrms`，创建 `.env.prod`（参考 `.env.prod.example`）。
  - 安装 Docker/Compose，`docker compose -f docker-compose.prod.yml up -d --build`，验证容器与 Nginx 反代。

## Jenkins 流水线（Jenkinsfile）

- CI：Checkout → pip install → `docker compose -f ci/docker-compose.yml up -d db` → `manage.py migrate` + `apply_triggers.py`/`apply_views.py` → `black --check .` → `ruff check hrms/apps hrms/utils` → `python manage.py test apps.performance`。
- CD：用 Credentials `vps-deploy-key`（deploy 用户私钥）SSH 到 `198.12.74.104:20189` 的 `/srv/hrms`，执行 `git reset --hard origin/main`、`docker compose -f docker-compose.prod.yml up -d --build`，在容器内跑 `migrate`/`apply_triggers.py`/`apply_views.py`/`collectstatic`/`check`，最后 `curl https://hrms.kohinbox.top/health/` 健康检查。
- post：关闭 CI 阶段启动的数据库容器。

## 下一步清单

1. 把 `deploy-ci-key.pub` 写入 `/home/deploy/.ssh/authorized_keys`，测试 `ssh -p 20189 deploy@198.12.74.104`。
2. 填写 `/srv/hrms/.env.prod`，克隆仓库并构建：`docker compose -f docker-compose.prod.yml up -d --build`。
3. 在 Jenkins（建议装 VPS 上）配置 `vps-deploy-key` 私钥、创建 Pipeline Job 指向 GitHub 仓库与 Jenkinsfile，设置 GitHub Webhook。
4. 跑一遍流水线，确认 lint/test/部署/健康检查全部通过。
