# 问数 · Data Agent

一个基于 LangGraph 的 NL2SQL 数据问答系统。用户用中文提问，Agent 自动完成关键字提取、元数据检索、SQL 生成与校验、SQL 执行，并把结果以表格形式流式返回给前端。

```
用户提问 → 关键字提取 → 三路召回（字段 / 指标 / 字段值）→ 合并 → 过滤
        → 补充上下文 → 生成 SQL → 校验（失败则矫正）→ 执行 → 返回结果
```

## 技术栈

| 层 | 选型 |
| --- | --- |
| Web 框架 | FastAPI + Uvicorn |
| Agent 编排 | LangGraph 1.x |
| LLM | LangChain，默认 DeepSeek（可通过环境变量切换） |
| 元数据存储 | MySQL（meta 库：表、字段、指标） |
| 数据仓库 | MySQL（dw 库：星型模型示例数据） |
| 向量检索 | Qdrant + BAAI/bge-large-zh-v1.5 |
| 全文检索 | Elasticsearch 8（IK 分词），用于字段值召回 |
| 前端 | Vue 3 + Vite |
| 包管理 | uv（Python）/ npm（前端） |

## 目录结构

```
data_agent/
├── main.py                     # FastAPI 入口，挂载 /api 路由与 request_id 中间件
├── configs/
│   ├── app_config.yaml         # 基础设施连接配置、日志、LLM
│   └── meta_config.yaml        # 需要同步到知识库的表 / 字段 / 指标定义
├── deploy/docker/              # MySQL、ES、Kibana、Qdrant、Embedding 的容器编排
├── src/data_agent/
│   ├── agent/
│   │   ├── graph.py            # LangGraph 状态图定义
│   │   ├── state.py            # 全局状态结构
│   │   ├── nodes/              # 各流程节点
│   │   └── prompts/            # 提示词模板（.prompt）
│   ├── api/                    # 路由与依赖注入
│   ├── core/                   # 配置加载、日志、请求上下文、lifespan
│   ├── infra/                  # MySQL / Qdrant / ES / Embedding 客户端与仓储
│   ├── models/schemas/         # 请求响应模型
│   ├── scripts/
│   │   └── build_meta_knowledge.py   # 元数据知识库构建入口
│   └── services/               # QueryService、MetaKnowledgeService
├── frontend/                   # Vue 3 前端
└── tests/                      # 各基础设施与流程的验证脚本
```

## 快速开始

### 环境要求

- Python 3.12.14+
- [uv](https://docs.astral.sh/uv/)
- Node.js 20+、npm
- Docker（用于启动 MySQL / ES / Qdrant / Embedding）

### 1. 启动依赖服务

```bash
cd deploy/docker
docker compose up -d
```

启动后各服务端口：

| 服务 | 端口 | 说明 |
| --- | --- | --- |
| MySQL | 3307 | 容器启动时自动导入 `mysql/dw.sql` 与 `mysql/meta.sql` |
| Elasticsearch | 9200 | 已内置 IK 分词插件 |
| Kibana | 5601 | 可选，用于查看 ES 数据 |
| Qdrant | 6333 / 6334 | HTTP / gRPC |
| Embedding | 8899 | text-embeddings-inference，首次启动会下载模型 |

### 2. 配置连接信息

编辑 `configs/app_config.yaml`，把各服务的 host / port 改为本地实际地址。若使用上面的 docker compose，对应关系为：

```yaml
db_meta:   { host: 127.0.0.1, port: 3307, ... }
db_dw:     { host: 127.0.0.1, port: 3307, ... }
qdrant:    { host: 127.0.0.1, port: 6333, embedding_size: 1024 }
embedding: { host: 127.0.0.1, port: 8899, model: BAAI/bge-large-zh-v1.5 }
es:        { host: 127.0.0.1, port: 9200, index_name: data_agent }
```

> 注意：`embedding.port` 要与容器映射出的端口一致（compose 中为 `8899:80`，因此填 8899），不是容器内部的 80。

LLM 相关配置建议用环境变量覆盖，避免把密钥写进配置文件。在项目根目录创建 `.env`：

```bash
LLM_MODEL=deepseek-chat
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=sk-xxxxxxxx
```

环境变量优先级高于 `configs/app_config.yaml`。

### 3. 安装依赖

```bash
uv sync
```

### 4. 构建元数据知识库

这一步把 `configs/meta_config.yaml` 中定义的表、字段、指标写入 meta 库、Qdrant 与 ES。**首次运行前必须执行，修改 `meta_config.yaml` 后也要重新执行。**

```bash
uv run -m src.data_agent.scripts.build_meta_knowledge -c configs/meta_config.yaml
```

### 5. 启动后端

```bash
uv run python main.py
```

服务监听 `http://localhost:8000`，接口文档见 `http://localhost:8000/docs`。

### 6. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问 `http://127.0.0.1:5173`。Vite 已配置 `/api` 代理到 `http://localhost:8000`，前后端无需额外处理跨域。

## 接口说明

### `POST /api/query`

请求体：

```json
{ "query": "上个月华东地区的 GMV 是多少？" }
```

响应为 `text/event-stream`，每条事件是一行 `data:` 加 JSON。事件有两种形态：

**阶段事件** —— 某个节点完成时推送，前端据此渲染执行轨迹：

```text
data:{"stage": "关键字提取"}
data:{"stage": "生成SQL"}
```

> `filter_table` 节点输出的键名是 `state` 而非 `stage`，属于已知实现细节，前端不做展示。

**结果事件** —— SQL 执行完成后推送，`result` 为行对象数组：

```text
data:{"result": [{"region_name": "华东", "order_amount": 1284300.5}]}
```

**错误事件** —— 任一环节抛出异常时推送：

```text
data:{"error": "..."}
```

## 维护元数据

`configs/meta_config.yaml` 是知识库的唯一来源，结构如下：

```yaml
tables:
  - name: fact_order
    role: fact                # dim / fact
    description: 订单事实表
    columns:
      - name: order_amount
        role: measure         # primary_key / foreign_key / dimension / measure
        description: 订单金额
        alias: [销售额, 收入]
        sync: false           # true 表示该字段的取值需要写入 ES 参与字段值召回

metrics:
  - name: GMV
    description: 所有订单的成交金额总和
    relevant_columns: [fact_order.order_amount]
    alias: [成交总额, 订单总额]
```

改动后重新执行第 4 步即可。

## 测试

`tests/` 下是各模块的手动验证脚本，覆盖配置加载、日志、各基础设施客户端、提示词与状态图。这些脚本**不是 pytest 用例**（没有断言，逻辑写在 `if __name__ == "__main__"` 里），需要逐个运行并看输出：

```bash
uv run python tests/test_app_config.py
uv run python tests/test_graph.py
```

多数脚本依赖真实服务（MySQL / Qdrant / ES / Embedding），运行前请确保第 1 步的容器已启动。

## 常见问题

**启动时报「请先调用 init 方法初始化」**
客户端管理器在 FastAPI lifespan 中初始化。直接 import 模块使用仓储时不会触发初始化，请通过接口调用，或在脚本中手动调用各 `init_*` 方法。

**Embedding 请求超时**
首次启动 text-embeddings-inference 会从 `hf-mirror.com` 下载 `bge-large-zh-v1.5`，耗时较长。等待容器日志出现模型加载完成后重试。

**生成的 SQL 总是选错表或指标**
说明召回结果不准。检查 `meta_config.yaml` 中相关表 / 指标的 `description` 与 `alias` 是否覆盖了用户的表达习惯，改完重新构建知识库。

**Qdrant 报维度不匹配**
`embedding_size` 必须与所用 embedding 模型的输出维度一致，`bge-large-zh-v1.5` 为 1024。
