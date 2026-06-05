# MicroFish-Openzep

🚀 **一键部署 OpenZep + MiroFish + Neo4j** 多智能体群体智能预测系统，**自带水浒传知识图谱数据**。

> MiroFish 是下一代多智能体预测引擎，基于 OpenZep 知识图谱记忆服务和 Neo4j 图数据库，自动构建平行数字世界，让数千个独立人格的 Agent 自由交互、推演未来。
>
> 本项目将 MiroFish 与 OpenZep 整合为统一 Docker 编排，开箱即用。

## 特性

- 🔧 **一键启动** — 交互式脚本，3 分钟完成配置到运行
- 🧠 **自带图谱数据** — 预置水浒传知识图谱（1,014 节点 / 2,548 条边），无需重新生成
- 🐳 **全 Docker 化** — Neo4j + OpenZep + MiroFish 统一编排
- 🔑 **自由选择 LLM** — DeepSeek / SiliconFlow / Qwen / OpenAI / Ollama 任意兼容 API
- 🌍 **完全自托管** — 数据不出本地，无隐私风险

## 架构

```
┌──────────────────────────────────────────────┐
│                  Docker 网络                   │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Neo4j:5 │  │ OpenZep  │  │ MiroFish │   │
│  │  图数据库  │◄─│ 记忆服务   │◄─│ 预测引擎   │   │
│  │  :7687   │  │  :8000   │  │ :3000    │   │
│  │  :7474   │  │          │  │ :5001    │   │
│  └──────────┘  └──────────┘  └──────────┘   │
│                                              │
│  用户浏览器 ◄──── :3000 (前端 Vue3)            │
│  前端 Vite 代理 ──► :5001 (后端 Flask API)    │
│  MiroFish 后端  ──► :8000 (OpenZep FastAPI)  │
│  OpenZep     ──► :7687 (Neo4j Bolt)          │
└──────────────────────────────────────────────┘
```

| 服务 | 技术栈 | 端口 |
|------|--------|------|
| **Neo4j 5** | 图数据库 + APOC 插件 | `7474` (Browser), `7687` (Bolt) |
| **OpenZep** | FastAPI + Graphiti 时序知识图谱 | `8000` (API), `/docs` (Swagger) |
| **MiroFish** | Vue3 前端 + Flask 后端 | `3000` (前端), `5001` (API) |

## 快速开始

### 前置要求

- [Docker Desktop](https://www.docker.com/)（含 Docker Compose v2）
- 任意 OpenAI 兼容 LLM API Key
- 推荐 16GB+ 内存

### 方式一：一键安装（推荐）

```bash
git clone https://github.com/ALILIYES/Microfish-Openzep.git
cd Microfish-Openzep
bash setup.sh
```

脚本会引导你填写 LLM 配置，然后自动启动全部服务。

### 方式二：手动配置

```bash
git clone https://github.com/ALILIYES/Microfish-Openzep.git
cd Microfish-Openzep

# 1. 配置环境变量
cp .env.example .env
vim .env  # 至少填入 LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

# 2. 启动
docker compose up -d --build

# 3. 验证
curl http://localhost:8000/healthz
# {"status": "ok"}
```

打开浏览器访问：
- 前端界面：**http://localhost:3000**
- API 文档：**http://localhost:8000/docs**
- Neo4j 控制台：**http://localhost:7474**

### 恢复水浒传知识图谱

项目已内置预生成的水浒传知识图谱数据，无需重新处理 186 万字原文：

```bash
cd graph-data
bash restore-graph.sh
```

| 指标 | 数值 |
|------|------|
| 节点数 | 1,014 |
| 边数 | 2,548 |
| Episodes | 2,457 |
| 实体类型 | 10 种（朝廷官员、武将、梁山好汉、宗教人物等） |
| 压缩包大小 | ~27 MB |

详细说明见 [graph-data/README.md](./graph-data/README.md)。

## 配置说明

### 必填环境变量

| 变量 | 说明 |
|------|------|
| `LLM_API_KEY` | LLM API Key |
| `LLM_BASE_URL` | LLM 端点 URL |
| `LLM_MODEL` | LLM 模型名称 |

### 可选环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_SMALL_MODEL` | 同 LLM_MODEL | 轻量任务用小模型 |
| `EMBEDDER_API_KEY` | 同 LLM_API_KEY | Embedding 服务 Key |
| `EMBEDDER_BASE_URL` | 同 LLM_BASE_URL | Embedding 服务端点 |
| `EMBEDDER_MODEL` | `BAAI/bge-m3` | Embedding 模型 |
| `NEO4J_PASSWORD` | `password123` | Neo4j 数据库密码 |
| `API_KEY` | 留空 | OpenZep API 鉴权 Key |

### LLM 配置示例

<details>
<summary>DeepSeek（推荐，性价比高）</summary>

```env
LLM_API_KEY=sk-your-key
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
# DeepSeek 不支持 embedding，需单独配置
EMBEDDER_API_KEY=sk-siliconflow-key
EMBEDDER_BASE_URL=https://api.siliconflow.cn/v1
EMBEDDER_MODEL=BAAI/bge-m3
```
</details>

<details>
<summary>SiliconFlow</summary>

```env
LLM_API_KEY=sk-your-key
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL=Qwen/Qwen2.5-72B-Instruct
EMBEDDER_MODEL=BAAI/bge-m3
```
</details>

<details>
<summary>阿里百炼 (Qwen)</summary>

```env
LLM_API_KEY=sk-your-key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
EMBEDDER_MODEL=text-embedding-v3
```
</details>

<details>
<summary>OpenAI</summary>

```env
LLM_API_KEY=sk-your-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
EMBEDDER_MODEL=text-embedding-3-small
```
</details>

<details>
<summary>Ollama（本地模型）</summary>

```env
LLM_API_KEY=ollama
LLM_BASE_URL=http://host.docker.internal:11434/v1
LLM_MODEL=llama3.1:8b
EMBEDDER_MODEL=nomic-embed-text
```
</details>

## 本地开发

不使用 Docker 时，可分别本地运行各服务。

### OpenZep

```bash
cd openzep

# 先启动 Neo4j
docker run -d --name neo4j --restart unless-stopped \
  -p 7687:7687 -p 7474:7474 \
  -e NEO4J_AUTH=neo4j/password123 neo4j:5

# 安装依赖 & 启动
cp .env.example .env  # 编辑填入 LLM 配置
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### MiroFish

```bash
cd mirofish

# 配置连接 OpenZep
cp .env.example .env
# 确保 ZEP_BASE_URL=http://localhost:8000/api/v2

npm run setup:all   # 安装前后端依赖
npm run dev         # 同时启动前后端
```

## 项目结构

```
Microfish-Openzep/
├── docker-compose.yml    # 统一 Docker 编排
├── setup.sh              # 一键安装脚本
├── .env.example          # 统一配置模板
├── .dockerignore
├── .gitignore
├── README.md
│
├── graph-data/           # ★ 水浒传预生成知识图谱
│   ├── cypher_nodes_export.csv.gz   # 节点 (9 MB)
│   ├── cypher_edges_export.csv.gz   # 边 (18 MB)
│   ├── import.cypher                 # Neo4j 导入脚本
│   ├── restore-graph.sh              # 一键恢复
│   └── README.md
│
├── openzep/              # OpenZep 记忆服务
│   ├── main.py           # FastAPI 入口
│   ├── config.py         # 配置 (Pydantic Settings)
│   ├── Dockerfile
│   ├── engine/           # Graphiti 图谱引擎封装
│   ├── models/           # Pydantic 数据模型
│   ├── routers/          # Zep V2 REST API 路由
│   └── tests/
│
└── mirofish/             # MiroFish 预测引擎
    ├── Dockerfile
    ├── package.json      # Node 项目 (concurrently 前后端)
    ├── backend/          # Flask 后端
    │   ├── run.py
    │   ├── app/
    │   │   ├── api/      # 蓝图 (graph, simulation, report)
    │   │   ├── services/ # 核心业务 (图谱构建/OASIS模拟/报告生成)
    │   │   └── utils/    # LLM客户端/文件解析/日志
    │   └── scripts/      # 模拟运行脚本
    ├── frontend/         # Vue3 前端
    │   └── src/
    │       ├── components/  # 5 步向导组件
    │       ├── views/       # 页面视图
    │       └── api/         # 后端 API 封装
    └── locales/          # 国际化 (zh / en)
```

## API 端点

### OpenZep (Zep V2 兼容)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/healthz` | 健康检查 |
| `POST` | `/api/v2/sessions` | 创建会话 |
| `GET` | `/api/v2/sessions` | 列出所有会话 |
| `POST` | `/api/v2/sessions/search` | 跨会话语义搜索 |
| `GET` | `/api/v2/sessions/{id}` | 获取会话详情 |
| `PATCH` | `/api/v2/sessions/{id}` | 更新会话元数据 |
| `POST` | `/api/v2/sessions/{id}/memory` | 添加记忆，触发图谱更新 |
| `GET` | `/api/v2/sessions/{id}/memory` | 获取记忆上下文 |
| `POST` | `/api/v2/sessions/{id}/users` | 用户关联 |
| `POST` | `/api/v2/graph/search` | 知识图谱语义搜索 |
| ... | ... | 完整 20 个端点见交互式文档 |

> Swagger 文档：**http://localhost:8000/docs**

### MiroFish

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | 健康检查 |
| `POST` | `/api/graph/build` | 构建知识图谱 |
| `POST` | `/api/simulation/start` | 启动模拟 |
| `GET` | `/api/simulation/status` | 查询模拟状态 |
| `POST` | `/api/report/generate` | 生成预测报告 |

## 许可证

- **OpenZep**: [OpenZep Proprietary License](./openzep/LICENSE) — Copyright © 2026 N1nEmAn
- **MiroFish**: [AGPL-3.0](./mirofish/LICENSE)

## 致谢

本项目整合了以下优秀开源项目，感谢原作者的杰出贡献：

- **[MiroFish](https://github.com/666ghj/MiroFish)** — 多智能体群体智能预测引擎，本项目核心。由 [@666ghj](https://github.com/666ghj) 开发，获盛大集团战略孵化支持。
- **[OpenZep](https://github.com/N1nEmAn/openzep)** — Zep API 兼容的自托管记忆服务，替代 Zep Cloud 实现本地知识图谱。由 [@N1nEmAn](https://github.com/N1nEmAn) 开发。
- **[Graphiti](https://github.com/getzep/graphiti)** — 时序知识图谱引擎，为 OpenZep 提供底层图谱能力。
- **[OASIS](https://github.com/camel-ai/oasis)** — 开放智能体社交交互模拟框架，为 MiroFish 提供多平台模拟能力。
- **[Neo4j](https://neo4j.com/)** — 图数据库，存储和查询知识图谱数据。

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=ALILIYES/Microfish-Openzep&type=date&legend=top-left)](https://www.star-history.com/#ALILIYES/Microfish-Openzep&type=date&legend=top-left)
