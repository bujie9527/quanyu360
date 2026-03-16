#!/usr/bin/env bash
# 在 Ubuntu 22.04 服务器上一键安装 Docker、Docker Compose、Git
# 用法: 在服务器上执行 bash setup-server.sh
# 建议: 先 ssh ubuntu@<server_ip> 登录后执行

set -e

echo "=== AI Workforce Platform 服务器环境初始化 ==="

# 检测系统
if [ -f /etc/os-release ]; then
  . /etc/os-release
  if [ "$ID" != "ubuntu" ]; then
    echo "警告: 此脚本针对 Ubuntu 编写，当前系统: $ID"
    read -p "是否继续? (y/N) " -n 1 -r
    echo
    [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
  fi
fi

echo "[1/4] 更新包索引..."
sudo apt-get update -qq

echo "[2/4] 安装基础依赖..."
sudo apt-get install -y ca-certificates curl gnupg lsb-release git

echo "[3/4] 安装 Docker..."
# 使用实际执行 docker 检查，避免 command -v 误判（如 PATH 中有损坏的符号链接）
if docker --version &>/dev/null; then
  echo "Docker 已安装: $(docker --version)"
else
  echo "正在添加 Docker 官方源并安装..."
  sudo mkdir -p /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  sudo apt-get update -qq
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  echo "Docker 安装完成: $(docker --version)"
fi

echo "[4/4] 配置 Docker 用户组..."
if getent group docker &>/dev/null; then
  if groups "$USER" | grep -q docker; then
    echo "用户 $USER 已在 docker 组中"
  else
    sudo usermod -aG docker "$USER"
    echo "已将 $USER 加入 docker 组。请重新登录或执行 'newgrp docker' 使配置生效。"
  fi
else
  echo "警告: docker 组不存在（Docker 可能未正确安装）。请检查上方安装日志，或重新运行此脚本。"
fi

echo ""
echo "=== 安装完成 ==="
echo "Docker:     $(docker --version 2>/dev/null || echo '未找到')"
echo "Compose:    $(docker compose version 2>/dev/null || echo '未找到')"
echo "Git:        $(git --version 2>/dev/null || echo '未找到')"
echo ""
echo "请重新 SSH 登录或执行: newgrp docker"
echo "然后按照 docs/DEPLOY_PRODUCTION.md 继续部署。"
