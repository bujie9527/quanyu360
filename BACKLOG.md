# 全宇360 开发待办 Backlog

> 按优先级排列，每项完成后标记 ✅ 并注明完成日期。  
> 最后更新：2026-03-17

---

## 一、线上自动发布流程（CI/CD）

### 1-A  配置 GitHub Actions 自动发布密钥  `待做`
- **背景**：`deploy-prod.yml` 工作流已存在，但 GitHub Repository Secrets 尚未配置，自动触发无法 SSH 登录服务器。
- **任务**：
  - 在 GitHub → Settings → Secrets → Actions 添加以下 4 个 Secret：
    - `PROD_HOST` = `43.165.195.151`
    - `PROD_USER` = `ubuntu`
    - `PROD_PORT` = `22`
    - `PROD_SSH_KEY` = 服务器信息.txt 中的 ed25519 私钥全文
    - `PROD_APP_DIR` = `/opt/ai-workforce`
  - 推送一次提交到 `main` 验证自动触发是否成功。
- **验收**：GitHub Actions 运行成功，服务器完成 git pull + docker build + migrate。

---

## 二、服务器管理标准化（进行中）

> 📄 详细技术规范见：[`docs/SERVER_ENV_STANDARD.md`](docs/SERVER_ENV_STANDARD.md)

### 2-A  服务器新建表单简化  `✅ 已完成 2026-03-17`
- 表单精简为：名称、主机 IP、SSH 端口、SSH 用户、SSH 密码
- MySQL 信息由系统安装脚本自动生成，无需手动填写
- 新增 `setup_status` 字段（pending / running / completed / failed）
- 新增 `setup_log` 字段，存储安装日志

### 2-B  服务器环境标准化安装脚本  `✅ 已完成 2026-03-17`
- 脚本位置：`tools/scripts/server_setup.sh`
- 安装标准栈：**Ubuntu 22.04 + Nginx 1.24+ + PHP 8.2-FPM + MariaDB 10.11 LTS + WP-CLI**
- 执行方式：Admin 界面点击"初始化环境"，平台 SSH 远程执行脚本
- 实时日志：安装过程每 10 行回传一次，在前端日志面板展示
- 自动捕获：脚本最后一行输出 `MYSQL_ROOT_PASSWORD=xxx`，平台自动写入服务器记录
- 数据库迁移：`20260317_0028_server_setup_fields.py`

### 2-C  服务器 SSH 指令执行能力  `待做`
- **背景**：除了安装脚本，需要支持 admin 在界面上对服务器执行任意诊断命令。
- **任务**：
  - 后端增加 `POST /admin/servers/{id}/exec` 接口（SSH 执行单条命令，返回 stdout/stderr）
  - 前端在服务器详情页增加简易 Terminal 面板（输入命令 → 回车 → 显示结果）
  - 支持常用快捷命令：查看磁盘空间、查看 PHP 版本、重启 Nginx/PHP-FPM、查看 MySQL 状态
- **安全要求**：仅限 admin 角色，所有命令执行记录到审计日志
- **验收**：在服务器详情页可以输入 `df -h` 并看到服务器返回结果

### 2-D  WP 环境标准参考文档
- 详见 `docs/SERVER_ENV_STANDARD.md`
- 涵盖：OS 要求、PHP/Nginx/MariaDB 版本规范、目录结构、PHP-FPM 配置、Nginx 站点模板、WP-CLI 安装步骤、单站安装完整流程、安全要求

---

## 三、矩阵建站流程（Admin 端）

### 2-A  批量建站 Agent 标准化  `待做`
- **背景**：当前 `wp_site_install_workflow` 通过 seed 脚本创建，安装步骤尚未与真实 WP-CLI 工具对接。
- **任务**：
  - 在 `tool-service` 中实现 `wpcli_install_wordpress` Tool（SSH 到目标服务器，用 WP-CLI 安装 WordPress）。
  - 工具参数：`server_id`, `domain`, `db_name`, `admin_user`, `admin_password`, `admin_email`, `site_title`, `locale`（默认 `zh_CN`）。
  - 标准化安装流程步骤：
    1. SSH 连接服务器
    2. 创建 MySQL 数据库与用户
    3. 下载 WordPress 核心文件（`wp core download`）
    4. 生成 `wp-config.php`（`wp config create`）
    5. 安装 WordPress（`wp core install`）
    6. 安装默认主题（可配置）
    7. 回写安装结果到 `wordpress_sites` 表
  - 在 `workflow_steps` 中关联上述工具步骤。
- **验收**：Admin 界面"批量建站"触发后，可在"安装日志"面板看到实时步骤进度，完成后站点进入站点库。

### 2-B  站点库 → 租户授权流程完善  `待做`
- **背景**：后端 `assign_site_to_tenant` 接口已实现，但租户侧尚无入口查看/使用被授权站点。
- **任务**：
  - 在租户项目页面增加"已关联站点"列表（拉取 `project_id` 对应的 `wordpress_sites`）。
  - 允许租户在矩阵项目里查看站点状态、API Key、后台链接。
  - 支持站点与矩阵规划方案（SitePlan）的关联（`site_plan_items.wordpress_site_id`）。
- **验收**：租户登录后，在对应矩阵项目下能看到被授权的 WordPress 站点，并可跳转后台。

### 2-C  矩阵建站项目创建 Bug 修复  `待做`
- **背景**：用户反馈"新建矩阵建站项目时，点击创建按钮后按钮刷新一下又恢复原状，没有建立项目"。
- **任务**：
  - 复现并定位 `project-service` `/projects` POST 接口错误（检查 `project_type=matrix_site` 的校验和数据库写入）。
  - 检查前端 `createProject` 调用链路，查看 Network 请求是否返回非 200 错误。
  - 修复后验证：能正常创建矩阵类型项目，并在项目列表显示。
- **验收**：创建矩阵建站项目成功，跳转到项目详情页。

---

## 三、站点内容生产（矩阵建站后续）

### 3-A  站点文章批量生产 Agent  `待做`
- **背景**：矩阵站建好后，需要持续批量生产内容（SEO 导向）。
- **任务**：
  - 实现 `publish_article_to_wordpress` Tool（通过 WP REST API 发布文章）。
  - 设计内容生产工作流（选题 → AI 写作 → 图片配置 → 发布）。
  - 接入 Agent 进行关键词扩展与内容批量排期。
- **验收**：一次批量任务可向指定站点发布多篇 SEO 文章，并记录到任务系统。

### 3-B  WordPress REST API 连通性管理  `待做`
- **任务**：
  - 在站点库详情中展示 REST API 连通性检测结果（ping `/wp-json/wp/v2/posts`）。
  - 支持配置 Application Password（用于 API 写入）并安全存储。
  - `wordpress_sites` 表增加 `app_password` 加密字段。
- **验收**：站点库中可以一键测试 API 连通性，显示成功/失败及错误信息。

---

## 四、服务器端优化

### 4-A  站点内容缓存与 CDN 管理  `规划中`
- 对站群-1（`43.160.237.155`）服务器上的 WordPress 站点配置 Nginx 缓存规则。
- 规划 CDN 接入方案（Cloudflare / 国内 CDN）。

### 4-B  多服务器批量建站支持  `规划中`
- 当前批量建站仅支持选择单台服务器。
- 扩展为可在多台服务器之间按域名负载分配。

---

## 五、系统运维与监控

### 5-A  GitHub Actions 自动部署密钥配置  `同 1-A`
（见第一节）

### 5-B  服务器信息安全化  `待做`
- **背景**：服务器 IP、密码等信息直接存放在 `服务器信息.txt` 中，存在泄漏风险。
- **任务**：
  - 将服务器凭据迁移至系统设置（`system_configs` 表）或外部 Secret Manager。
  - 把 `服务器信息.txt` 从 Git 追踪中移除（`.gitignore`）。
- **验收**：仓库中不含明文密码，服务器通过系统设置页面管理。

### 5-C  日志与告警  `规划中`
- 集成结构化日志输出（当前已有 `structlog`）。
- 配置关键错误的告警通知（Telegram / 企业微信 Webhook）。

---

## 六、已完成 ✅

| 完成日期 | 内容 |
|---|---|
| 2026-03-17 | Git 同步发布彻底整改（deploy-from-git.sh、GitHub Actions、rollback 脚本、DEPLOY_PRODUCTION.md 更新） |
| 2026-03-17 | frontend/public 占位符修复，deploy.sh 迁移预检增强 |
| 2026-03-17 | WordPressSite 数据模型升级（server_id、install_task_run_id、nullable tenant/project） |
| 2026-03-17 | Alembic 迁移：20260317_0027 wordpress_site_pool |
| 2026-03-17 | Admin API：/admin/site-pool 批量建站与站点库接口 |
| 2026-03-17 | 前端：批量建站页面（/admin/site-install）、站点库页面（/admin/site-pool） |
| 2026-03-17 | 导航菜单重构：增加"建站中心"分组（域名库、服务器、批量建站、站点库） |
| 2026-03-17 | 修复 platform.py / api.ts 编码损坏 docstring（Python SyntaxError / webpack 构建失败） |
| 2026-03-17 | 线上部署成功，smoke checks 全部通过，Alembic 迁移成功 |
