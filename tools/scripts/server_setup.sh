#!/usr/bin/env bash
# =============================================================================
# server_setup.sh — 全宇360 建站平台服务器环境标准化安装脚本
# 
# 标准栈: Ubuntu 22.04/24.04 + Nginx + PHP 8.2 + MariaDB 10.11 + WP-CLI
# 执行方式: 由平台 admin-service 通过 SSH 远程执行（需 root 或 sudo 权限）
# 输出格式: 最后一行输出 MYSQL_ROOT_PASSWORD=<password>，供平台自动捕获
# =============================================================================

set -e

# ----- 颜色输出 -----
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ----- 权限检查 -----
if [ "$(id -u)" -ne 0 ]; then
  error "此脚本必须以 root 或 sudo 运行"
fi

# ----- 检测操作系统 -----
if [ -f /etc/os-release ]; then
  . /etc/os-release
  OS_NAME="$ID"
  OS_VERSION="$VERSION_ID"
else
  error "无法检测操作系统版本"
fi

info "操作系统: $OS_NAME $OS_VERSION"
if [ "$OS_NAME" != "ubuntu" ] && [ "$OS_NAME" != "debian" ]; then
  warn "当前脚本针对 Ubuntu/Debian 优化，其他系统可能出现兼容性问题"
fi

DEBIAN_FRONTEND=noninteractive
export DEBIAN_FRONTEND

# =============================================================================
# STEP 1: 系统更新
# =============================================================================
info "=== STEP 1/9: 系统更新 ==="
apt-get update -qq
apt-get upgrade -y -qq
info "系统更新完成"

# =============================================================================
# STEP 2: 安装基础工具
# =============================================================================
info "=== STEP 2/9: 安装基础工具 ==="
apt-get install -y -qq \
  curl wget git unzip zip rsync \
  lsof net-tools htop \
  software-properties-common \
  apt-transport-https ca-certificates gnupg2
info "基础工具安装完成"

# =============================================================================
# STEP 3: 安装 Nginx
# =============================================================================
info "=== STEP 3/9: 安装 Nginx ==="
apt-get install -y -qq nginx
systemctl enable nginx
systemctl start nginx
NGINX_VER=$(nginx -v 2>&1 | grep -o '[0-9.]*' | head -1)
info "Nginx $NGINX_VER 安装完成"

# =============================================================================
# STEP 4: 安装 PHP 8.2
# =============================================================================
info "=== STEP 4/9: 安装 PHP 8.2 ==="
# 添加 ondrej/php PPA（支持 Ubuntu 22.04/24.04）
add-apt-repository -y ppa:ondrej/php 2>/dev/null || true
apt-get update -qq

PHP_PACKAGES="
  php8.2-fpm
  php8.2-cli
  php8.2-common
  php8.2-mysql
  php8.2-curl
  php8.2-gd
  php8.2-intl
  php8.2-mbstring
  php8.2-soap
  php8.2-xml
  php8.2-xmlrpc
  php8.2-zip
  php8.2-bcmath
  php8.2-opcache
  php8.2-readline
"
# shellcheck disable=SC2086
apt-get install -y -qq $PHP_PACKAGES

systemctl enable php8.2-fpm
systemctl start php8.2-fpm

# PHP-FPM 性能配置
PHP_INI_CLI="/etc/php/8.2/cli/php.ini"
PHP_INI_FPM="/etc/php/8.2/fpm/php.ini"
for PHP_INI in "$PHP_INI_CLI" "$PHP_INI_FPM"; do
  if [ -f "$PHP_INI" ]; then
    sed -i 's/^upload_max_filesize.*/upload_max_filesize = 64M/' "$PHP_INI"
    sed -i 's/^post_max_size.*/post_max_size = 64M/' "$PHP_INI"
    sed -i 's/^memory_limit.*/memory_limit = 256M/' "$PHP_INI"
    sed -i 's/^max_execution_time.*/max_execution_time = 300/' "$PHP_INI"
    grep -q '^max_input_vars' "$PHP_INI" \
      && sed -i 's/^max_input_vars.*/max_input_vars = 3000/' "$PHP_INI" \
      || echo "max_input_vars = 3000" >> "$PHP_INI"
  fi
done

PHP_VER=$(php8.2 -r 'echo PHP_VERSION;' 2>/dev/null || echo "unknown")
info "PHP $PHP_VER 安装完成"

# =============================================================================
# STEP 5: 安装 MariaDB 10.11
# =============================================================================
info "=== STEP 5/9: 安装 MariaDB 10.11 ==="

# 生成随机 MariaDB root 密码
MYSQL_ROOT_PASSWORD=$(tr -dc 'A-Za-z0-9@#$%^&*' </dev/urandom | head -c 20)

# 添加 MariaDB 官方源
curl -sS https://downloads.mariadb.com/MariaDB/mariadb_repo_setup \
  | bash -s -- --mariadb-server-version="mariadb-10.11" 2>/dev/null

apt-get update -qq
apt-get install -y -qq mariadb-server mariadb-client

systemctl enable mariadb
systemctl start mariadb

# 安全初始化 MariaDB（设置 root 密码，移除匿名用户）
mysql -u root <<SQL
ALTER USER 'root'@'localhost' IDENTIFIED BY '${MYSQL_ROOT_PASSWORD}';
DELETE FROM mysql.user WHERE User='';
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
FLUSH PRIVILEGES;
SQL

MARIADB_VER=$(mysql --version | grep -o 'Distrib [0-9.-]*' | cut -d' ' -f2)
info "MariaDB $MARIADB_VER 安装完成，root 密码已设置"

# =============================================================================
# STEP 6: 创建 Web Root
# =============================================================================
info "=== STEP 6/9: 创建 Web Root ==="
mkdir -p /var/www/html
chown -R www-data:www-data /var/www
chmod -R 755 /var/www
info "Web Root /var/www 创建完成"

# =============================================================================
# STEP 7: 安装 WP-CLI
# =============================================================================
info "=== STEP 7/9: 安装 WP-CLI ==="
curl -sO https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
php8.2 wp-cli.phar --info --allow-root >/dev/null 2>&1 || error "WP-CLI phar 验证失败"
chmod +x wp-cli.phar
mv wp-cli.phar /usr/local/bin/wp
WPCLI_VER=$(wp --info --allow-root 2>/dev/null | grep 'WP-CLI version' | awk '{print $NF}')
info "WP-CLI $WPCLI_VER 安装完成 → /usr/local/bin/wp"

# =============================================================================
# STEP 8: Nginx 全局配置优化
# =============================================================================
info "=== STEP 8/9: Nginx 配置优化 ==="
cat > /etc/nginx/conf.d/performance.conf <<'NGINX_CONF'
# Performance tuning
client_max_body_size 64M;
client_body_buffer_size 128k;
keepalive_timeout 65;
gzip on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
NGINX_CONF

nginx -t && systemctl reload nginx
info "Nginx 配置优化完成"

# =============================================================================
# STEP 9: 版本摘要
# =============================================================================
info "=== STEP 9/9: 环境安装完成 ==="
echo ""
echo "=========================================="
echo " 服务器环境安装摘要"
echo "=========================================="
echo " OS      : $(lsb_release -ds 2>/dev/null || echo "$OS_NAME $OS_VERSION")"
echo " Nginx   : $(nginx -v 2>&1 | grep -o '[0-9.]*' | head -1)"
echo " PHP     : $(php8.2 -r 'echo PHP_VERSION;' 2>/dev/null)"
echo " MariaDB : $(mysql --version | grep -o 'Distrib [0-9.-]*' | cut -d' ' -f2)"
echo " WP-CLI  : $(wp --info --allow-root 2>/dev/null | grep 'WP-CLI version' | awk '{print $NF}')"
echo " Web Root: /var/www"
echo "=========================================="

# 输出 MySQL root 密码（平台自动捕获并存入数据库）
# 必须保持此格式，不要修改
echo "MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}"
