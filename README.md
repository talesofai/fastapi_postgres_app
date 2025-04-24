# FastAPI PostgreSQL API

这是一个使用 FastAPI 框架连接 PostgreSQL 数据库并提供 CRUD 操作的 API 应用程序。支持图片元数据管理、Gemini API 图像描述生成和预设配置管理。

## 功能

- 连接到 PostgreSQL 数据库
- 提供完整的 CRUD API 接口
- 图片元数据管理
- Gemini API 图像描述生成
- 描述预设配置管理
- 可在阿里云 K8S 容器中部署

## 目录结构

```
fastapi_postgres_app/
├── main.py          # 主应用程序和路由
├── database.py      # 数据库配置和连接
├── models.py        # SQLAlchemy 模型定义
├── schemas.py       # Pydantic 模型定义
├── requirements.txt # 依赖项列表
├── Dockerfile       # 用于构建容器镜像
└── README.md        # 项目说明
```

## 安装和运行

### 本地运行

1. 安装依赖项：

```bash
pip install -r requirements.txt
```

2. 运行应用程序：

```bash
python main.py
```

### 使用 Docker 构建和运行

1. 构建 Docker 镜像：

```bash
docker build -t fastapi-postgres-api .
```

2. 运行 Docker 容器：

```bash
docker run -d -p 8000:8000 fastapi-postgres-api
```

### 在阿里云 K8S 中部署

1. 构建并推送镜像到阿里云容器镜像服务
2. 使用提供的镜像创建 K8S 部署

## API 端点

### 基础接口

- `GET /` - 测试 API 是否正常运行
- `POST /test-connection/` - 测试数据库连接

### 项目接口

- `POST /items/` - 创建新项目
- `GET /items/` - 获取所有项目
- `GET /items/{item_id}` - 获取单个项目
- `PUT /items/{item_id}` - 更新项目
- `DELETE /items/{item_id}` - 删除项目

### 图片接口 (Artifacts)

- `GET /artifacts/` - 获取所有图片
- `POST /artifacts/` - 创建新图片
- `GET /artifacts/{artifact_id}` - 获取特定图片
- `PUT /artifacts/{artifact_id}` - 更新图片
- `DELETE /artifacts/{artifact_id}` - 删除图片
- `GET /artifacts/md5/{md5}` - 通过 MD5 获取图片

### 描述预设接口 (Caption Presets)

- `GET /presets/` - 获取所有预设
- `POST /presets/` - 创建新预设
- `GET /presets/{preset_key}` - 获取特定预设
- `PUT /presets/{preset_key}` - 更新预设
- `DELETE /presets/{preset_key}` - 删除预设

### 图片描述接口 (Captions)

- `GET /captions/` - 获取所有描述
- `POST /captions/` - 创建新描述
- `GET /captions/{caption_id}` - 获取特定描述
- `PUT /captions/{caption_id}` - 更新描述
- `DELETE /captions/{caption_id}` - 删除描述
- `GET /captions/artifact/{artifact_id}` - 获取特定图片的所有描述
- `GET /captions/artifact/{artifact_id}/preset/{preset_key}` - 获取特定图片使用特定预设的描述

## Swagger 文档

启动应用后，访问 `http://localhost:8000/docs` 查看 API 文档。

## 数据库模型

### Artifact

- `id`: UUID (主键)
- `md5`: 字符串 (唯一)
- `width`: 整数
- `height`: 整数
- `size`: 整数
- `format`: 字符串
- `original_filename`: 字符串
- `original_path`: 字符串
- `upload_time`: 大整数
- `tags`: 字符串数组
- `is_deleted`: 布尔值
- `deleted_time`: 字符串

### CaptionPreset

- `preset_key`: 字符串 (主键)
- `config`: JSONB (包含模型、提示词等配置)
- `description`: 文本
- `creator_id`: UUID
- `create_time`: 大整数
- `is_deleted`: 布尔值
- `deleted_time`: 大整数

### Caption

- `id`: UUID (主键)
- `artifact_id`: UUID (外键，关联 Artifact)
- `type`: 字符串
- `preset_key`: 字符串 (外键，关联 CaptionPreset)
- `upload_time`: 大整数
- `text`: 文本
- `extra_data`: JSONB
- `is_deleted`: 布尔值
- `deleted_time`: 大整数