# AI Workforce Platform 线上环境部署文档

## 1. 服务器信息

| 项目     | 值              |
|----------|------------------|
| 服务器IP | `<your_server_ip>` |
| 用户名   | `<your_ssh_user>` |
| 密码     | `<never_store_here>` |
| SSH 端口 | 22（默认）       |

> **安全提示**：严禁在仓库中保存明文密码/Token。建议仅使用 SSH 密钥登录，并在密码泄露后立即轮换。

---

## 2. 服务器配置要求

- **CPU**：4 核及以上
- **内存**：8 GB 及以上（推荐 16 GB）
- **磁盘**：50 GB 及以上
- **系统**：Ubuntu 22.04 LTS
- **网络**：需能访问外网（拉取镜像、模型 API）

---

## 3. 首次准备：连接服务器

```bash
# 从本机连接（会提示输入密码）
ssh <your_ssh_user>@<your_server_ip>
```

---

## 4. 安装依赖

### 4.1 安装 Docker 与 Docker Compose

```bash
# 更新包索引
sudo apt-get update

# 安装必要依赖
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# 添加 Docker 官方 GPG 密钥
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 添加 Docker 仓库
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 将当前用户加入 docker 组（避免每次 sudo）
sudo usermod -aG docker $USER
# 重新登录后生效，或执行：newgrp docker
```

### 4.2 安装 Git

```bash
sudo apt-get install -y git
```

### 4.3 验证安装

```bash
docker --version
docker compose version
git --version
```

---

## 5. 部署目录与代码

### 5.1 创建部署目录

```bash
sudo mkdir -p /opt/ai-workforce
sudo chown ubuntu:ubuntu /opt/ai-workforce
cd /opt/ai-workforce
```

### 5.2 拉取代码

```bash
# 若为 Git 仓库
git clone <你的仓库地址> .
# 或通过 scp/rsync 从本机上传
# rsync -avz --exclude 'node_modules' --exclude '.git' ./ ubuntu@43.165.195.151:/opt/ai-workforce/
```

---

## 6. 环境变量配置

### 6.1 生成生产环境配置

```bash
cd /opt/ai-workforce
cp .env.production.example .env.production
```

### 6.2 编辑 .env.production

**必须修改的配置：**

```bash
nano .env.production
```

| 变量 | 说明 | 示例 |
|------|------|------|
| `POSTGRES_PASSWORD` | PostgreSQL 密码 | 强密码，至少 16 位 |
| `REDIS_PASSWORD` | Redis 密码 | 强密码 |
| `JWT_SECRET_KEY` | JWT 签名密钥 | 随机长字符串（openssl rand -base64 48） |
| `INTERNAL_API_KEY` | 内部回调鉴权密钥（WP-CLI 回写凭证） | 随机长字符串 |
| `DATABASE_URL` | 数据库连接 | 包含上述 POSTGRES 密码 |
| `*_REDIS_URL` | 各服务 Redis 连接 | 包含 REDIS_PASSWORD |
| `ENABLED_TOOL_PLUGINS` | 工具插件白名单（可为空） | 留空自动发现；或 `wordpress,facebook,wpcli,ssh_command` |
| `CORS_ORIGINS` | 前端域名 | `["https://43.165.195.151"]` 或你的域名 |
| `NEXT_PUBLIC_*` | 前端 API 地址 | `https://43.165.195.151/api/...` 或你的域名 |

**若使用服务器 IP 直接访问（无域名）：**

```env
CORS_ORIGINS=["http://43.165.195.151","http://43.165.195.151:80"]
NGINX_HTTP_PORT=80

NEXT_PUBLIC_AUTH_SERVICE_URL=http://43.165.195.151/api/auth
NEXT_PUBLIC_PROJECT_SERVICE_URL=http://43.165.195.151/api/projects
NEXT_PUBLIC_AGENT_SERVICE_URL=http://43.165.195.151/api/agents
NEXT_PUBLIC_TASK_SERVICE_URL=http://43.165.195.151/api/tasks
NEXT_PUBLIC_WORKFLOW_SERVICE_URL=http://43.165.195.151/api/workflows
NEXT_PUBLIC_WORKFLOW_ENGINE_URL=http://43.165.195.151/api/executions
NEXT_PUBLIC_AGENT_RUNTIME_URL=http://43.165.195.151/api/runtime
```

**配置 LLM（OpenAI/Claude 等）：**

```env
OPENAI_API_KEY=sk-xxx
# 或
CLAUDE_API_KEY=sk-ant-xxx
```

---

## 7. 使用脚本管理服务

脚本位于 `tools/scripts/`，需在项目根目录执行。

### 7.1 启动

```bash
cd /opt/ai-workforce
sh tools/scripts/start.sh
```

### 7.2 停止

```bash
sh tools/scripts/stop.sh
```

### 7.3 重启

```bash
sh tools/scripts/restart.sh
```

### 7.4 查看状态

```bash
sh tools/scripts/status.sh
```

或使用便捷脚本（推荐，自动带上生产配置）：

```bash
sh tools/scripts/dc.sh ps
```

> **说明**：首次运行 `start.sh` 后会自动创建 `.env -> .env.production` 符号链接，直接运行 `docker compose ps` 也能正确读取变量。但推荐使用 `dc.sh` 或 `status.sh`，以便正确加载 `docker-compose.prod.yml`。

### 7.5 查看日志

```bash
# 所有服务
sh tools/scripts/dc.sh logs -f

# 指定服务
sh tools/scripts/dc.sh logs -f nginx
sh tools/scripts/dc.sh logs -f frontend
```

---

## 8. 防火墙与端口

确保服务器放行以下端口：

```bash
# 若使用 ufw
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw enable
sudo ufw status
```

---

## 9. 通过域名 platform.idouwa.com 访问

要使用 `platform.idouwa.com` 访问后台服务，按以下步骤配置。

### 9.1 配置 DNS

在域名服务商（如阿里云、腾讯云、Cloudflare）添加解析：

| 类型 | 主机记录 | 记录值 | TTL |
|------|----------|--------|-----|
| A | platform | 43.165.195.151 | 600 |

> 若服务器 IP 不同（如云厂商分配的弹性 IP），请使用实际公网 IP。

验证 DNS 生效：
```bash
ping platform.idouwa.com
```

### 9.2 确保 .env.production 中域名正确

`.env.production` 需包含：

```env
CORS_ORIGINS=["https://platform.idouwa.com","http://platform.idouwa.com"]
NGINX_HTTP_PORT=80

NEXT_PUBLIC_AUTH_SERVICE_URL=https://platform.idouwa.com/api/auth
NEXT_PUBLIC_PROJECT_SERVICE_URL=https://platform.idouwa.com/api/projects
NEXT_PUBLIC_AGENT_SERVICE_URL=https://platform.idouwa.com/api/agents
NEXT_PUBLIC_TASK_SERVICE_URL=https://platform.idouwa.com/api/tasks
NEXT_PUBLIC_WORKFLOW_SERVICE_URL=https://platform.idouwa.com/api/workflows
NEXT_PUBLIC_WORKFLOW_ENGINE_URL=https://platform.idouwa.com/api/executions
NEXT_PUBLIC_AGENT_RUNTIME_URL=https://platform.idouwa.com/api/runtime
NEXT_PUBLIC_API_GATEWAY_URL=https://platform.idouwa.com
```

### 9.3 防火墙放行 80 端口

```bash
sudo ufw allow 80/tcp
sudo ufw reload
```

### 9.4 重启服务使配置生效

若已修改 `.env.production`：

```bash
cd /opt/ai-workforce
sh tools/scripts/restart.sh
```

### 9.5 访问地址

| 入口 | 地址 |
|------|------|
| 前台 | http://platform.idouwa.com |
| 登录 | http://platform.idouwa.com/login |
| 管理后台 | http://platform.idouwa.com/admin |

### 9.6 配置 HTTPS（可选，推荐）

1. 安装 certbot：
```bash
sudo apt-get update
sudo apt-get install -y certbot
```

2. 申请证书（需暂停占用 80 端口的服务）：
```bash
# 临时停止 nginx 容器
cd /opt/ai-workforce
sh tools/scripts/dc.sh stop nginx

# 申请证书（按提示选择 standalone）
sudo certbot certonly --standalone -d platform.idouwa.com

# 重启 nginx
sh tools/scripts/dc.sh start nginx
```

3. 配置 Nginx 使用 SSL：需修改 `docker/nginx/nginx.conf` 增加 443 监听和证书路径，或使用外部反向代理（如云厂商负载均衡）做 SSL 卸载。配置 HTTPS 后需将 `CORS_ORIGINS` 和 `NEXT_PUBLIC_*` 中的 `http://` 改为 `https://`。

---

## 10. 健康检查

部署完成后，执行：

```bash
SMOKE_CHECK_MODE=proxy SMOKE_CHECK_BASE_URL=http://43.165.195.151 sh tools/scripts/smoke-check.sh
```

或手动验证：

```bash
curl http://43.165.195.151/health/live
curl http://43.165.195.151/api/auth/health/live
```

---

## 10. 访问地址

| 入口 | 地址 |
|------|------|
| 前端页面 | http://43.165.195.151 |
| 登录 | http://43.165.195.151/login |

> 若有域名，将 `43.165.195.151` 替换为域名，并配置 HTTPS（如 Nginx + Let's Encrypt）。

---

## 11. 故障排查

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| 502 Bad Gateway | 后端服务未启动或异常 | 见下方「502 排查步骤」 |
| 前端白屏 | NEXT_PUBLIC_* 配置错误 | 检查 .env.production 中 API 地址是否与访问域名一致 |
| 登录失败 | JWT 或 auth-service 异常 | 检查 JWT_SECRET_KEY、auth-service 日志 |
| 任务不执行 | task-worker / workflow-engine-worker 未启动 | 确认 worker 容器运行正常 |
| 建站/Agent 失败 | OPENAI_API_KEY 等未配置 | 配置 LLM 密钥并重启 agent-runtime |

### 常用命令

```bash
# 查看所有容器
docker ps -a

# 进入容器调试
docker exec -it <container_name> sh

# 查看资源占用
docker stats
```

---

## 12. 数据备份建议

```bash
# PostgreSQL 备份
docker exec postgres pg_dump -U platform_admin platform > backup_$(date +%Y%m%d).sql

# Redis 持久化在卷中，可按需导出
```

---

## 13. 更新部署

### 方式一：本地上传后重启（推荐）

在**本地**项目根目录执行同步脚本，一键将代码推送到服务器：

```bash
# 同步代码到服务器（排除 node_modules、.next、.git 等）
sh tools/scripts/sync-to-server.sh

# 若需同时同步 .env.production（慎用，会覆盖服务器上的配置）
sh tools/scripts/sync-to-server.sh --with-env
```

同步完成后，SSH 到服务器执行重启：

```bash
ssh <your_ssh_user>@<your_server_ip> "cd /opt/ai-workforce && sh tools/scripts/deploy.sh"
```

> `deploy.sh` 会执行：`compose up --build -d` + `alembic upgrade head` + `seed_wp_site_install_workflow.py`（幂等）。

### 方式二：服务器拉取代码

若服务器上通过 Git 管理代码：

```bash
cd /opt/ai-workforce
git pull
sh tools/scripts/deploy.sh
```
