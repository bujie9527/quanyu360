# WordPress Integration Tool

## Functions

| Action | Description |
|--------|-------------|
| `publish_post` | Create and publish a new post |
| `update_post` | Update an existing post (title, content, status, tags) |
| `delete_post` | Delete a post (optionally bypass Trash with `force=true`) |

Uses WordPress REST API (`/wp-json/wp/v2/posts`).

## Credential Storage (Secure)

Credentials are **never** stored in code. Two options:

### 1. connector_config (Recommended)

Store in workflow node config or platform `Tool.config`:

```json
{
  "connector_config": {
    "base_url": "https://your-site.com",
    "basic_auth": {
      "user": "wp_username",
      "password": "xxxx xxxx xxxx xxxx"
    }
  }
}
```

- `base_url`: WordPress site URL (e.g. `https://mysite.com`)
- `basic_auth.user`: WordPress username
- `basic_auth.password`: Application Password (Users → Profile → Application Passwords)

Alternatively:

```json
{
  "connector_config": {
    "base_url": "https://your-site.com",
    "user": "wp_username",
    "password": "xxxx xxxx xxxx xxxx"
  }
}
```

### 2. Environment Variables (Development)

For local/dev, use env vars (never committed):

```env
WORDPRESS_SITE_URL=https://your-site.com
WORDPRESS_USER=wp_username
WORDPRESS_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

`connector_config` takes precedence over env vars.

## Workflow Node Example

```json
{
  "node_key": "publish_wordpress",
  "type": "tool_call",
  "config": {
    "tool_name": "wordpress",
    "action": "publish_post",
    "parameters": {
      "title": "{{context.title}}",
      "content": "{{context.content}}",
      "status": "publish"
    },
    "connector_config": {
      "base_url": "https://mysite.com",
      "basic_auth": {
        "user": "editor",
        "password": "xxxx xxxx xxxx xxxx"
      }
    }
  }
}
```

## Application Passwords

1. WordPress 5.6+: Users → Profile → Application Passwords
2. Create a new Application Password (e.g. "AiWorkerCenter")
3. Copy the generated password (shown once)
4. Use as `basic_auth.password` or `WORDPRESS_APP_PASSWORD`
