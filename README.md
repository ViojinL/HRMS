# HRMS

## 初始化测试数据

每次重新创建数据库或运行迁移后，请执行 `python hrms/init_data.py` 以恢复组织结构、员工账号和关键业务数据（账号统一是 `password123`），确保后续交互/审批流程可以在本地快速验证。可以把这条命令写入本地脚本或 CI 任务，在 `migrate` 之后自动调用。

## 生产部署

- **仓库地址**：`https://github.com/ViojinL/HRMS.git`，在 GitHub 上启用 Jenkins webhook，让每次 `main` 分支的提交触发流水线。CI 阶段运行 `python -m black --check .`、`python -m ruff check hrms/apps hrms/utils` 以及 `python hrms/manage.py test hrms/apps/performance`。
- **镜像与 Compose**：新增 `Dockerfile` + `scripts/entrypoint.sh`（migrate、apply_triggers、apply_views、collectstatic 后运行 Gunicorn），以及 `docker-compose.prod.yml`。`web` 服务挂载 `/srv/hrms/staticfiles`、`/srv/hrms/media`，向外暴露 `8000`，PostgreSQL 数据库使用 `prod_pgdata` 卷。
- **环境变量**：复制 `.env.prod.example` 为 `/srv/hrms/.env.prod` 并填写实际 `DJANGO_SECRET_KEY`、数据库密码、邮件配置等，Jenkins 避免将 secrets 提交；`docker compose -f docker-compose.prod.yml` 通过 `env_file` 读取。
- **Jenkins 部署**：`Jenkinsfile` deploy stage 通过 `ssh -p 20189 ly@198.12.74.104` 登录 VPS，`cd /srv/hrms`、`git reset --hard origin/main`、`docker compose -f docker-compose.prod.yml up -d --build`，然后在容器内依次执行 `manage.py migrate`、`apply_triggers.py`/`apply_views.py`、`collectstatic`、`check`，最后用 `curl -fsSL https://hrms.kohinbox.top/health/` 做健康检查。
- **Nginx/Cloudflare**：VPS 上 `/etc/nginx/sites-available/hrms` 将 HTTP 重定向到 HTTPS，并把 `/` 代理到 `http://127.0.0.1:8000`。静态目录指向 `/srv/hrms/staticfiles`，Cloudflare 的 `A` 记录指向 VPS IP，SSL 证书放在 `/etc/nginx/cert/public.pem` 与 `private.key`。
