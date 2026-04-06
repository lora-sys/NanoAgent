# 模块：接口设计规范

## 1. RESTful 标准
- **URL**: 使用名词复数，禁止使用动词（例：`/users` 而非 `/getUsers`）。
- **Methods**: 严格遵循 GET/POST/PUT/DELETE 语义。

## 2. 数据契约
- **Request**: 必须进行严格的 Schema 校验。
- **Response**: 统一返回格式 `{ code: number, data: T, message: string }`。

## 3. 安全性
- **MUST**: 接口必须包含 Auth 校验逻辑（除非显式说明为公开接口）。