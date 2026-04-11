# SmartHome AI - 部署指南

## 项目概述

SmartHome AI 是一个基于 React + TypeScript 的智能家居公司商业展示网站，包含产品演示、功能介绍、技术架构展示和联系表单等功能。

## 技术栈

- **前端框架**: React 18 + TypeScript
- **构建工具**: Vite
- **样式方案**: CSS Modules / Tailwind CSS
- **路由管理**: React Router v6
- **表单验证**: 自定义验证逻辑
- **部署平台**: Vercel / Netlify (推荐)

---

## 环境准备

### 系统要求

- Node.js >= 18.0.0
- npm >= 9.0.0 或 yarn >= 1.22.0
- Git

### 环境变量配置

1. 复制环境变量示例文件：
```bash
cp .env.example .env
```

2. 填写实际的环境变量值：

| 变量名 | 说明 | 必填 | 示例值 |
|--------|------|------|--------|
| `VITE_API_BASE_URL` | 后端 API 基础地址 | 否 | `https://api.smarthome-ai.com` |
| `VITE_CONTACT_FORM_ENDPOINT` | 联系表单提交端点 | 是 | `https://formspree.io/your-form-id` |
| `VITE_ANALYTICS_ID` | 分析工具 ID (可选) | 否 | `GA-XXXXXXXXXX` |
| `VITE_SENTRY_DSN` | Sentry 错误追踪 (可选) | 否 | `https://xxx@sentry.io/xxx` |

> ⚠️ **安全提示**: 永远不要将 `.env` 文件提交到版本控制系统！

---

## 本地开发

### 1. 安装依赖

```bash
npm install
# 或
yarn install
```

### 2. 启动开发服务器

```bash
npm run dev
# 或
yarn dev
```

开发服务器将在 `http://localhost:5173` 启动，支持热重载。

### 3. 代码质量检查

```bash
# TypeScript 类型检查
npm run type-check

# ESLint 代码检查
npm run lint

# 运行测试
npm run test
```

---

## 生产构建

### 构建命令

```bash
npm run build
# 或
yarn build
```

### 构建优化配置

生产构建已启用以下优化：

- ✅ **代码压缩**: Terser 压缩 JavaScript 代码
- ✅ **Tree Shaking**: 移除未使用的代码
- ✅ **静态资源优化**: 图片、字体等资源自动优化
- ✅ **代码分割**: 按路由自动分割代码包
- ✅ **CSS 压缩**: 移除未使用的 CSS 样式

### 构建输出

构建产物位于 `dist/` 目录：

```
dist/
├── index.html          # 入口 HTML
├── assets/             # 静态资源
│   ├── index-[hash].js # 主应用脚本（带哈希）
│   ├── index-[hash].css # 样式文件（带哈希）
│   └── images/         # 优化后的图片
└── vite.svg            # favicon
```

### 本地预览生产构建

```bash
npm run preview
# 或
yarn preview
```

---

## 部署方案

### 方案一：Vercel 部署（推荐）

#### 优势
- 零配置部署
- 自动 HTTPS
- 全球 CDN 加速
- 自动预览部署
- 免费 tier 足够使用

#### 部署步骤

1. **安装 Vercel CLI**
```bash
npm install -g vercel
```

2. **登录 Vercel**
```bash
vercel login
```

3. **初始化项目**
```bash
vercel
```

4. **配置环境变量**

在 Vercel 控制台设置环境变量：
- 进入项目设置 → Environment Variables
- 添加 `.env` 中的所有变量
- 选择环境（Production/Preview/Development）

5. **部署到生产环境**
```bash
vercel --prod
```

#### vercel.json 配置

项目根目录已包含 `vercel.json` 配置文件：

```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        },
        {
          "key": "Strict-Transport-Security",
          "value": "max-age=31536000; includeSubDomains"
        },
        {
          "key": "Content-Security-Policy",
          "value": "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:;"
        }
      ]
    }
  ]
}
```

---

### 方案二：Netlify 部署

#### 部署步骤

1. **安装 Netlify CLI**
```bash
npm install -g netlify-cli
```

2. **登录 Netlify**
```bash
netlify login
```

3. **初始化项目**
```bash
netlify init
```

4. **部署**
```bash
netlify deploy --prod
```

#### netlify.toml 配置

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
    X-XSS-Protection = "1; mode=block"
    X-Content-Type-Options = "nosniff"
    Strict-Transport-Security = "max-age=31536000; includeSubDomains"
```

---

### 方案三：AWS S3 + CloudFront

#### 适用场景
- 需要完全控制部署环境
- 已有 AWS 基础设施
- 需要自定义域名和 SSL 证书

#### 部署步骤

1. **创建 S3 桶**
```bash
aws s3 mb s3://smarthome-ai-website --region us-east-1
```

2. **配置静态网站托管**
- 启用静态网站托管
- 设置索引文档为 `index.html`
- 设置错误文档为 `index.html` (SPA 路由需要)

3. **上传构建文件**
```bash
aws s3 sync dist/ s3://smarthome-ai-website --delete
```

4. **创建 CloudFront 分发**
- 源：S3 桶
- 启用 HTTPS
- 配置自定义域名（可选）
- 设置缓存策略

5. **配置桶策略**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::smarthome-ai-website/*"
    }
  ]
}
```

---

## CI/CD 流程

### GitHub Actions 配置

项目包含 `.github/workflows/deploy.yml` 自动化部署流程：

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
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
      
      - name: Type check
        run: npm run type-check
      
      - name: Lint
        run: npm run lint
      
      - name: Test
        run: npm run test -- --coverage
      
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

### 环境变量密钥配置

在 GitHub 仓库设置中添加以下 Secrets：

- `VERCEL_TOKEN`: Vercel API Token
- `VERCEL_ORG_ID`: Vercel 组织 ID
- `VERCEL_PROJECT_ID`: Vercel 项目 ID

---

## 回滚方案

### Vercel 回滚

1. **通过 CLI 回滚**
```bash
vercel rollback [deployment-url]
```

2. **通过控制台回滚**
- 进入 Vercel 控制台
- 选择项目 → Deployments
- 找到要回滚的版本 → 点击 "Promote to Production"

### Netlify 回滚

1. **通过 CLI 回滚**
```bash
netlify deploy --prod --dir=dist --context=production
```

2. **通过控制台回滚**
- 进入 Netlify 控制台
- 选择项目 → Deploys
- 找到之前的成功部署 → 点击 "Publish deploy"

### 手动回滚（通用）

1. 从版本控制检出之前的稳定版本：
```bash
git checkout <commit-hash>
```

2. 重新构建并部署：
```bash
npm install
npm run build
# 执行部署命令
```

---

## 性能优化检查清单

### Lighthouse 评分优化（目标：90+）

- [ ] 启用 Gzip/Brotli 压缩
- [ ] 配置浏览器缓存策略
- [ ] 优化图片格式（使用 WebP）
- [ ] 预加载关键资源
- [ ] 移除未使用的 JavaScript
- [ ] 最小化主线程工作
- [ ] 减少 JavaScript 执行时间

### 无障碍性优化（目标：90+）

- [ ] 所有图片都有 alt 属性
- [ ] 表单元素都有 label
- [ ] 颜色对比度符合 WCAG 标准
- [ ] 支持键盘导航
- [ ] 屏幕阅读器友好
- [ ] 焦点状态可见

---

## 监控与维护

### 日志监控

- **Vercel**: 控制台 → Project → Functions → Logs
- **Netlify**: 控制台 → Site → Functions → Logs
- **自定义**: 集成 Sentry 进行错误追踪

### 性能监控

- Google Analytics 4
- Vercel Analytics
- Lighthouse CI（集成到 CI/CD）

### 定期维护任务

| 任务 | 频率 | 说明 |
|------|------|------|
| 依赖更新 | 每月 | 运行 `npm outdated` 检查更新 |
| 安全审计 | 每月 | 运行 `npm audit` |
| 性能测试 | 每季度 | 运行 Lighthouse 测试 |
| 备份部署配置 | 每次变更 | 保存部署配置文件 |

---

## 故障排查

### 常见问题

#### 1. 构建失败
```bash
# 清除缓存重新构建
rm -rf node_modules dist
npm install
npm run build
```

#### 2. 路由 404 错误
- 确保服务器配置了 SPA 回退规则
- 检查 `vercel.json` 或 `netlify.toml` 的重定向配置

#### 3. 环境变量未生效
- 确认变量名以 `VITE_` 开头
- 重新构建项目（环境变量在构建时注入）
- 检查部署平台的变量配置

#### 4. 联系表单提交失败
- 检查 `VITE_CONTACT_FORM_ENDPOINT` 配置
- 确认 CORS 设置正确
- 查看浏览器控制台错误信息

---

## 联系支持

如遇到部署问题，请提供以下信息：

1. 错误日志截图
2. 部署平台名称
3. Node.js 版本
4. 浏览器控制台错误（如适用）

---

**文档版本**: 1.0.0  
**最后更新**: 2026-04-11  
**维护团队**: SmartHome AI 开发团队
