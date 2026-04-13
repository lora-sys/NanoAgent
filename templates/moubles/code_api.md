# 模块：API 设计规范

## RESTful 标准
- URL 使用名词复数（如 `/users`）。
- 严格遵循 GET/POST/PUT/DELETE 语义。

## 数据契约
- 请求必须校验 Schema。
- 响应统一格式: `{ code, data, message }`。

## 安全性
- 接口必须包含 Auth 校验（公开接口除外）。
