# Pilot-Ready 实施指南

本指南描述真实工具连接器、资产管理与生产级运维能力的实现与使用。

## 1. 真实工具连接器

### 架构

- **Connector 抽象**：`tools/connectors/base.py` 定义 `BaseConnector`，支持凭证与配置注入
- **HTTP Connector**：`tools/connectors/http_connector.py` 通用 REST API 调用
- **Platform Tool 映射**：WorkflowStep 的 `config.tool_name` 可对应 platform Tool.slug，通过 `config.connector_config` 透传凭证

### Tool.config 透传

WorkflowStep 执行时，可从 platform `Tool.config` 注入：
- `base_url`、`api_key`、`headers` 等
- 通过 `ToolExecutionContext.connector_config` 传给插件

### 新增插件

1. 在 `tools/plugins/` 添加新插件类
2. 在 `tools/runtime/registry.py` 的 `PLUGIN_FACTORIES` 中注册
3. 配置 `ENABLED_TOOL_PLUGINS` 启用

**http_api 工具**：调用外部 REST API。WorkflowStep config 需包含 `connector_config`（含 `base_url`、`api_key` 等）。示例：
```json
{
  "tool_name": "http_api",
  "action": "request",
  "parameters": { "path": "GET /users", "query": {}, "body": null },
  "connector_config": { "base_url": "https://api.example.com", "api_key": "xxx" }
}
```

---

## 2. 资产管理

### Asset 模型

- `backend/common/app/models/platform.py`：`Asset` 表
- 字段：`tenant_id`、`project_id`、`name`、`storage_key`、`mime_type`、`size_bytes`、`metadata`
- 多租户隔离，按 project 归属

### 存储后端

- 使用 S3 兼容 API（MinIO、AWS S3）
- 配置：`S3_ENDPOINT_URL`、`S3_ACCESS_KEY`、`S3_SECRET_KEY`、`S3_BUCKET`
- 上传 API：`POST /projects/{id}/assets` → 返回预签名 URL 或直传

### 知识库集成

- Asset 类型 `document` 可用于 RAG
- 后续扩展：pgvector 向量化与检索

---

## 3. 生产级运维

### 健康检查

- **live**：进程存活
- **ready**：依赖可达（DB ping、Redis ping）
- 实现：`common/app/observability/health.py` 的 `check_ready()`

### Prometheus 指标

- 所有后端服务暴露 `/metrics`
- 公共模块：`common/app/observability/prometheus.py`
- 指标：请求计数、延迟分位、错误率

### 告警

- 配置：`ALERT_WEBHOOK_URL`（Slack 等）
- 触发：健康检查失败、任务失败率超阈值时调用 webhook

### 审计

- Project、Agent、Task、Workflow、Tool 的 CRUD 与执行写入 AuditLog
- 公共：`common/app/audit.py` 的 `log_audit()`

---

## 4. 部署检查清单

- [ ] 设置 `S3_*` 或 `MINIO_*` 环境变量
- [ ] 配置 `ALERT_WEBHOOK_URL`（可选）
- [ ] 执行 `alembic upgrade head`
- [ ] 运行 `make smoke` 验证
- [ ] 配置 Prometheus scrape `/metrics`
- [ ] 配置 Grafana 仪表盘（可选）
