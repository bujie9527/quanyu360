# 服务器环境标准规范

> 全宇360 建站平台 · 服务器标准化文档  
> 版本：v1.0 · 2026-03-17  
> 目标：所有纳入建站平台的服务器，必须通过本规范描述的标准化安装脚本完成环境初始化，确保 WP-CLI 批量建站可稳定执行。

---

## 一、支持的操作系统

| 发行版 | 版本 | 状态 |
|---|---|---|
| Ubuntu | **22.04 LTS** (Jammy) | ✅ 主要支持 |
| Ubuntu | 24.04 LTS (Noble) | ✅ 支持 |
| Debian | 12 (Bookworm) | ✅ 支持 |
| CentOS / AlmaLinux | 9+ | ⚠️ 有限支持（需单独测试） |

> 推荐使用 **Ubuntu 22.04 LTS**，所有脚本默认以此为基准。

---

## 二、软件栈版本标准（LEMP Stack）

### 2.1 Web Server
| 软件 | 版本要求 | 说明 |
|---|---|---|
| Nginx | **1.24+** | 使用官方 apt 源，推荐 mainline |

### 2.2 PHP
| 软件 | 版本要求 | 说明 |
|---|---|---|
| PHP | **8.2**（首选）/ 8.3 | 使用 `ondrej/php` PPA |
| php8.2-fpm | 同上 | 进程管理器 |
| php8.2-cli | 同上 | WP-CLI 执行依赖 |
| php8.2-mysql | 同上 | WordPress 数据库驱动 |
| php8.2-curl | 同上 | HTTP 请求 |
| php8.2-gd | 同上 | 图片处理 |
| php8.2-intl | 同上 | 国际化支持 |
| php8.2-mbstring | 同上 | 多字节字符串 |
| php8.2-xml | 同上 | XML 解析 |
| php8.2-xmlrpc | 同上 | XML-RPC 协议 |
| php8.2-zip | 同上 | 插件/主题安装 |
| php8.2-bcmath | 同上 | 精度计算 |
| php8.2-soap | 同上 | SOAP 接口 |
| php8.2-opcache | 同上 | 性能缓存 |

### 2.3 数据库
| 软件 | 版本要求 | 说明 |
|---|---|---|
| MariaDB | **10.11 LTS** | 使用官方 MariaDB apt 源 |

> 选择 MariaDB 而非 MySQL 的原因：
> - 完全兼容 MySQL 协议，WordPress/WP-CLI 无感知
> - LTS 版本安全支持至 2028 年
> - 性能与稳定性更优

### 2.4 WP-CLI
| 软件 | 版本要求 | 安装路径 |
|---|---|---|
| WP-CLI | **最新稳定版**（>=2.10） | `/usr/local/bin/wp` |

WP-CLI 官方最低 PHP 要求：**PHP 7.4+**  
本平台强制使用 PHP 8.2+，超出最低要求，向上兼容。

### 2.5 其他工具
| 软件 | 用途 |
|---|---|
| curl | 下载 WP-CLI、WordPress 核心 |
| wget | 备用下载工具 |
| git | 版本管理 |
| unzip | 解压插件/主题 |
| rsync | 文件同步 |
| lsof / net-tools | 网络诊断 |

---

## 三、目录结构标准

```
/var/www/                          ← Web Root 根目录
├── html/                          ← 默认占位（Nginx 默认站点）
└── {domain}/                      ← 每个 WordPress 站点独立目录
    ├── public_html/               ← WordPress 文件根目录（document root）
    └── logs/                      ← 站点 Nginx 日志

/etc/nginx/sites-available/        ← Nginx 站点配置
/etc/nginx/sites-enabled/          ← 软链接激活的配置

/etc/php/8.2/fpm/pool.d/           ← PHP-FPM 站点池配置
```

> 平台默认 `web_root = /var/www`，每个 WordPress 站点安装在 `/var/www/{domain}/public_html/`。

---

## 四、数据库命名规范

| 内容 | 命名规则 | 示例 |
|---|---|---|
| 数据库名 | `wp_{domain_slug}` （下划线替换 `.` 和 `-`） | `wp_example_com` |
| 数据库用户 | 同数据库名 | `wp_example_com` |
| 表前缀 | `wp_` | `wp_posts` |
| MariaDB root 用户 | `root` | — |
| MariaDB root 密码 | 安装时随机生成16位，写入服务器记录 | — |

---

## 五、PHP-FPM 配置标准

```ini
; /etc/php/8.2/fpm/pool.d/www.conf（全局默认值）
[www]
user = www-data
group = www-data
pm = dynamic
pm.max_children = 20
pm.start_servers = 4
pm.min_spare_servers = 2
pm.max_spare_servers = 8
pm.max_requests = 500

; php.ini 关键配置
upload_max_filesize = 64M
post_max_size = 64M
memory_limit = 256M
max_execution_time = 300
max_input_vars = 3000
```

---

## 六、Nginx 站点模板

每个 WordPress 站点使用以下 Nginx 配置模板（变量 `{DOMAIN}` 由建站脚本替换）：

```nginx
server {
    listen 80;
    server_name {DOMAIN} www.{DOMAIN};
    root /var/www/{DOMAIN}/public_html;
    index index.php index.html;

    access_log /var/www/{DOMAIN}/logs/access.log;
    error_log  /var/www/{DOMAIN}/logs/error.log;

    client_max_body_size 64M;

    location / {
        try_files $uri $uri/ /index.php?$args;
    }

    location ~ \.php$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/run/php/php8.2-fpm.sock;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }

    location ~ /\.ht {
        deny all;
    }
}
```

---

## 七、WP-CLI 安装步骤

```bash
# 1. 下载 WP-CLI
curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar

# 2. 验证
php wp-cli.phar --info

# 3. 设为全局命令
chmod +x wp-cli.phar
mv wp-cli.phar /usr/local/bin/wp

# 4. 验证安装
wp --info
```

---

## 八、标准化初始化脚本 `server_setup.sh`

> 脚本由平台 admin-service 通过 SSH 远程执行，一键完成环境初始化。  
> 执行时间约 3~8 分钟（取决于网络速度）。  
> 执行结果实时回传到平台，存入 `servers.setup_log`。

### 脚本执行顺序：

```
1. 系统更新（apt update && apt upgrade）
2. 安装基础工具（curl, wget, git, unzip, rsync）
3. 安装 Nginx
4. 添加 ondrej/php PPA，安装 PHP 8.2 及所有扩展
5. 安装 MariaDB 10.11，自动设置 root 密码（随机生成）
6. 创建 Web Root 目录 /var/www，设置权限
7. 安装 WP-CLI 到 /usr/local/bin/wp
8. 重启 Nginx、PHP-FPM
9. 输出版本摘要（Nginx/PHP/MariaDB/WP-CLI 版本）
10. 输出 MariaDB root 密码（平台自动捕获并存储）
```

### 脚本位置：
```
tools/scripts/server_setup.sh
```

---

## 九、WP-CLI 单站安装流程

每个 WordPress 站点通过以下 WP-CLI 命令序列安装（由建站 Workflow 执行）：

```bash
DOMAIN="example.com"
DB_NAME="wp_example_com"
DB_USER="wp_example_com"
DB_PASS="<随机16位密码>"
ADMIN_USER="admin"
ADMIN_PASS="<用户设置>"
ADMIN_EMAIL="admin@example.com"
SITE_TITLE="Example Site"
WP_DIR="/var/www/${DOMAIN}/public_html"

# 1. 创建目录
mkdir -p "$WP_DIR" /var/www/"${DOMAIN}"/logs

# 2. 创建 MySQL 数据库和用户
mysql -u root -p"${MYSQL_ROOT_PASS}" <<SQL
  CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
  CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASS}';
  GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'localhost';
  FLUSH PRIVILEGES;
SQL

# 3. 下载 WordPress
wp core download --path="$WP_DIR" --locale=zh_CN --allow-root

# 4. 生成配置
wp config create \
  --path="$WP_DIR" \
  --dbname="$DB_NAME" \
  --dbuser="$DB_USER" \
  --dbpass="$DB_PASS" \
  --dbhost=localhost \
  --allow-root

# 5. 安装 WordPress
wp core install \
  --path="$WP_DIR" \
  --url="http://${DOMAIN}" \
  --title="$SITE_TITLE" \
  --admin_user="$ADMIN_USER" \
  --admin_password="$ADMIN_PASS" \
  --admin_email="$ADMIN_EMAIL" \
  --allow-root

# 6. 配置 Nginx 站点（从模板生成）
# 7. 重载 Nginx
nginx -t && systemctl reload nginx

# 8. 设置文件权限
chown -R www-data:www-data "$WP_DIR"

# 9. 回写结果到平台
echo "INSTALLED:${DOMAIN}:${DB_NAME}:${DB_USER}"
```

---

## 十、安全要求

- SSH 连接必须使用密码认证或公钥认证（不允许空密码）
- MariaDB root 密码在安装时随机生成，存储于平台加密字段
- WordPress 数据库账号仅具有对应单库权限（最小权限原则）
- 每站点 Nginx 日志独立存储
- 不对外暴露 phpMyAdmin（平台通过 API 管理数据库）
