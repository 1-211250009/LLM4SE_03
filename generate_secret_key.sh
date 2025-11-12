#!/bin/bash

# JWT 密钥生成脚本
# 使用方法: ./generate_secret_key.sh

echo "生成 JWT 密钥..."
echo ""

# 方法1: 使用 Python (推荐)
if command -v python3 &> /dev/null; then
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    echo "✅ 使用 Python 生成:"
    echo "SECRET_KEY=$SECRET_KEY"
    echo ""
fi

# 方法2: 使用 OpenSSL
if command -v openssl &> /dev/null; then
    SECRET_KEY=$(openssl rand -hex 32)
    echo "✅ 使用 OpenSSL 生成:"
    echo "SECRET_KEY=$SECRET_KEY"
    echo ""
fi

# 方法3: 使用 /dev/urandom (Linux/macOS)
if [ -e /dev/urandom ]; then
    SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1)
    echo "✅ 使用 /dev/urandom 生成:"
    echo "SECRET_KEY=$SECRET_KEY"
    echo ""
fi

echo "📝 请将生成的 SECRET_KEY 复制到您的 .env 文件中"
echo ""
echo "⚠️  重要提示:"
echo "   - SECRET_KEY 应该至少 32 个字符"
echo "   - 生产环境请使用强密钥"
echo "   - 不要将真实的 SECRET_KEY 提交到 git"

