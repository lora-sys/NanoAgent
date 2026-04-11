# SmartHome AI - 部署指南

## 📋 概述

本文档提供 SmartHome AI 产品展示网站的完整部署流程，包括本地开发、生产构建和云端部署。

## 🚀 快速开始

### 前置要求

- Node.js >= 18.0
- npm >= 9.0 或 yarn >= 1.22
- Git

### 本地开发环境设置

```bash
# 1. 克隆项目
git clone <repository-url>
cd smarthome-ai

# 2. 安装依赖
npm install

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入实际配置

# 4. 启动开发服务器
npm run dev
```

访问 `http://localhost:5173` 查看本地开发版本。

## 🏗️ 生产构建

### 构建优化配置

项目已配置以下生产优化：

- ✅ 代码压缩 (Terser)
- ✅ Tree Shaking
- ✅ 静态资源优化
- ✅ CSS 压缩
- ✅ 代码分割 (Code Splitting)

### 构建命令

```bash
# 生产构建
npm run build

# 预览生产构建
npm run preview
```

构建输出目录：`dist/`

## ☁️ 部署方案

### 方案 A: Vercel 部署（推荐）

```bash
# 1. 安装 Vercel CLI
npm i -g vercel

# 2. 登录 Vercel
vercel login

# 3. 部署
vercel --prod
```

**Vercel 配置文件** (`vercel.json`) 已包含在项目根目录：

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "devCommand": "npm run dev",
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-XSS-Protection", "value": "1; mode=block" },
        { "key": "Strict-Transport-Security", "value": "max-age=31536000; includeSubDomains" },
        { "key": "Content-Security-Policy", "value": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:;" }
      ]
    }
  ]
}
```

### 方案 B: Netlify 部署

```bash
# 1. 安装 Netlify CLI
npm i -g netlify-cli

# 2. 登录 Netlify
netlify login

# 3. 部署
netlify deploy --prod --dir=dist
```

**Netlify 配置文件** (`netlify.toml`)：

```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-Content-Type-Options = "nosniff"
    Strict-Transport-Security = "max-age=31536000; includeSubDomains"
```

### 方案 C: AWS S3 + CloudFront

```bash
# 1. 构建项目
npm run build

# 2. 同步到 S3
aws s3 sync dist/ s3://<your-bucket-name> --delete

# 3. 使 CloudFront 缓存失效
aws cloudfront create-invalidation --distribution-id <your-distribution-id> --paths "/*"
```

## 🔒 安全配置

### 环境变量安全

**重要**: 永远不要将敏感信息提交到版本控制！

```bash
# .env 文件应包含在 .gitignore 中
# 只提交 .env.example 作为模板
```

### 安全响应头

项目已配置以下安全头：

| 头名称 | 值 | 说明 |
|--------|-----|------|
| Content-Security-Policy | 限制资源加载源 | 防止 XSS 攻击 |
| Strict-Transport-Security | max-age=31536000 | 强制 HTTPS |
| X-Content-Type-Options | nosniff | 防止 MIME 类型嗅探 |
| X-Frame-Options | DENY | 防止点击劫持 |
| X-XSS-Protection | 1; mode=block | XSS 过滤器 |

### 联系表单安全

联系表单配置：
- 前端验证（必填字段、邮箱格式）
- CSRF 令牌保护（生产环境）
- 速率限制（防止滥用）
- 输入 sanitization

## 🔄 CI/CD 流程

### GitHub Actions 配置

`.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run tests
        run: npm test
      
      - name: Build
        run: npm run build
      
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

### 回滚方案

**Vercel 回滚**:
```bash
# 列出所有部署
vercel ls

# 回滚到指定部署
vercel rollback <deployment-url>
```

**Netlify 回滚**:
1. 登录 Netlify Dashboard
2. 选择站点 → Deploys
3. 点击要回滚的版本 → Publish deploy

## 📊 性能监控

### Lighthouse 评分目标

- 性能: ≥ 90
- 无障碍: ≥ 90
- 最佳实践: ≥ 90
- SEO: ≥ 90

### 运行 Lighthouse 测试

```bash
# 使用 Chrome DevTools
# 或命令行:
npm run lighthouse
```

## 🐛 故障排查

### 常见问题

**1. 构建失败**
```bash
# 清除缓存重新构建
rm -rf node_modules dist
npm install
npm run build
```

**2. 环境变量未加载**
```bash
# 确保 .env 文件存在且格式正确
cat .env
# 重启开发服务器
```

**3. 联系表单不工作**
- 检查后端 API 端点配置
- 验证 CORS 设置
- 查看浏览器控制台错误

## 📞 技术支持

如有部署问题，请联系：
- 邮箱：support@smarthome-ai.com
- 文档：https://docs.smarthome-ai.com

---

**最后更新**: 2026-04-11
**版本**: 1.0.0
