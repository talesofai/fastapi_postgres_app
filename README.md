# FastAPI PostgreSQL API

这是一个使用 FastAPI 框架连接 PostgreSQL 数据库并提供 CRUD 操作的 API 应用程序。

## 功能

- 连接到 PostgreSQL 数据库
- 提供完整的 CRUD API 接口
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

- `GET /` - 测试 API 是否正常运行
- `POST /test-connection/` - 测试数据库连接
- `POST /items/` - 创建新项目
- `GET /items/` - 获取所有项目
- `GET /items/{item_id}` - 获取单个项目
- `PUT /items/{item_id}` - 更新项目
- `DELETE /items/{item_id}` - 删除项目

## Swagger 文档

启动应用后，访问 `http://localhost:8000/docs` 查看 API 文档。 