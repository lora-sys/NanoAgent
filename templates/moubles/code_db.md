# 模块：数据库规范

## 建模
- 字段使用 `snake_case`。
- 表必须包含 `created_at` 和 `updated_at`。

## 索引
- 为高频查询字段创建索引。
- 禁止全表扫描。
