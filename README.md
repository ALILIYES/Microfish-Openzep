# MicroFish Docker

一键部署 **OpenZep + MiroFish + Neo4j** 多智能体群体智能预测系统。

> MiroFish 是一个下一代多智能体预测引擎，基于 OpenZep 知识图谱记忆服务和 Neo4j 图数据库，自动构建平行数字世界，让数千个独立人格的 Agent 自由交互、推演未来。

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
│  用户浏览器 ◄──── :3000 (前端)                 │
│  前端 Vite 代理 ──► :5001 (后端 API)          │
│  MiroFish 后端  ──► :8000 (OpenZep)          │
│  OpenZep     ──► :7687 (Neo4j)              │
└──────────────────────────────────────────────┘
```

| 服务 | 说明 | 端口 |
|------|------|------|
| **Neo4j 5** | 图数据库，存储知识图谱 | `7474` (UI), `7687` (Bolt) |
| **OpenZep** | Zep API 兼容记忆服务，基于 Graphiti 时序知识图谱 | `8000` |
| **MiroFish** | 多智能体预测引擎 (Vue3 前端 + Flask 后端) | `3000` (前端), `5001` (API) |

## 快速开始

### 前置要求

- [Docker & Docker Compose](https://www.docker.com/)
- 任意 OpenAI 兼容 LLM API Key（推荐 DeepSeek、SiliconFlow）

### 一键启动

```bash
# 1. 克隆项目
git clone https://github.com/ALILIYES/Microfish-Openzep.git
cd Microfish-Openzep

# 2. 运行安装脚本
bash setup.sh

# 3. 打开浏览器
# http://localhost:3000
```

安装脚本自动完成：
- 收集 LLM / Embedder 配置
- 写入 `.env`
- 构建并启动全部 3 个容器
- 等待健康检查通过

### 手动启动

```bash
# 1. 创建配置
cp .env.example .env
vim .env  # 填入 LLM_API_KEY 等必填项

# 2. 启动
docker compose up -d --build

# 3. 验证
curl http://localhost:8000/healthz
# {"status": "ok"}
```

## 本地开发

如果不使用 Docker，也可以分别本地启动。

### OpenZep 本地开发

```bash
cd openzep

# 1. 启动 Neo4j
docker run -d --name neo4j --restart unless-stopped \
  -p 7687:7687 -p 7474:7474 \
  -e NEO4J_AUTH=neo4j/password123 neo4j:5

# 2. 配置
cp .env.example .env  # 填入 LLM 配置

# 3. 安装 & 启动
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### MiroFish 本地开发

```bash
cd mirofish

# 1. 配置（确保 ZEP_BASE_URL 指向 OpenZep）
cp .env.example .env
# ZEP_BASE_URL=http://localhost:8000/api/v2

# 2. 安装依赖
npm run setup:all

# 3. 启动
npm run dev
```

## 配置说明

所有配置通过项目根目录的 `.env` 文件控制：

| 变量 | 必填 | 说明 |
|------|------|------|
| `LLM_API_KEY` | ✅ | LLM API Key |
| `LLM_BASE_URL` | ✅ | LLM 端点 URL |
| `LLM_MODEL` | ✅ | LLM 模型名称 |
| `LLM_SMALL_MODEL` | ❌ | 轻量任务用的小模型 |
| `EMBEDDER_API_KEY` | ❌ | Embedding 服务 Key（不支持 embedding 的 LLM 需单独配置） |
| `EMBEDDER_BASE_URL` | ❌ | Embedding 服务端点 |
| `EMBEDDER_MODEL` | ❌ | Embedding 模型 (默认: `BAAI/bge-m3`) |
| `NEO4J_PASSWORD` | ❌ | Neo4j 密码 (默认: `password123`) |
| `API_KEY` | ❌ | OpenZep API Key（留空则不禁用鉴权） |

### LLM 提供商配置示例

<details>
<summary>DeepSeek</summary>

```env
LLM_API_KEY=sk-your-key
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
EMBEDDER_MODEL=BAAI/bge-m3
EMBEDDER_API_KEY=sk-siliconflow-key
EMBEDDER_BASE_URL=https://api.siliconflow.cn/v1
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
<summary>Ollama (本地)</summary>

```env
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3.1:8b
EMBEDDER_MODEL=nomic-embed-text
```
</details>

## 项目结构

```
MicroFish-Docker/
├── docker-compose.yml    # 统一编排文件
├── .env.example          # 配置模板
├── setup.sh              # 一键安装脚本
├── .gitignore
├── README.md
├── openzep/              # OpenZep 记忆服务
│   ├── main.py           # FastAPI 入口
│   ├── config.py         # 配置类
│   ├── Dockerfile
│   ├── engine/           # Graphiti 引擎封装
│   ├── models/           # Pydantic 数据模型
│   └── routers/          # API 路由 (sessions, memory, users, graph...)
└── mirofish/             # MiroFish 预测引擎
    ├── Dockerfile
    ├── package.json      # Node 项目配置
    ├── backend/          # Flask 后端
    │   ├── run.py        # 启动入口
    │   ├── app/
    │   │   ├── api/      # 蓝图路由
    │   │   ├── services/ # 核心业务 (图谱构建, 模拟, 报告)
    │   │   └── utils/    # 工具类 (LLM客户端, 文件解析)
    │   └── scripts/      # 模拟脚本
    ├── frontend/         # Vue3 前端
    │   └── src/
    │       ├── components/  # UI 组件
    │       ├── views/       # 页面
    │       └── api/         # API 调用封装
    └── locales/          # 国际化 (中文/英文)
```

## OpenZep API 端点

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v2/sessions` | 创建会话 |
| `GET` | `/api/v2/sessions` | 列出会话 |
| `POST` | `/api/v2/sessions/search` | 跨会话语义搜索 |
| `POST` | `/api/v2/sessions/{id}/memory` | 添加记忆 |
| `GET` | `/api/v2/sessions/{id}/memory` | 获取记忆 |
| `POST` | `/api/v2/graph/search` | 图谱搜索 |
| ... | ... | 完整 Zep V2 REST API |

交互式文档：`http://localhost:8000/docs`

## 许可证

- **OpenZep**: [OpenZep Proprietary License](./openzep/LICENSE)
- **MiroFish**: [AGPL-3.0](./mirofish/LICENSE)

## 致谢

本项目整合了以下优秀开源项目，感谢原作者的杰出贡献：

- **[MiroFish](https://github.com/666ghj/MiroFish)** — 多智能体群体智能预测引擎，本项目核心。由 [@666ghj](https://github.com/666ghj) 开发，获盛大集团战略孵化支持。
- **[OpenZep](https://github.com/N1nEmAn/openzep)** — Zep API 兼容的自托管记忆服务，替代 Zep Cloud 实现本地知识图谱。由 [@N1nEmAn](https://github.com/N1nEmAn) 开发。
- **[Graphiti](https://github.com/getzep/graphiti)** — 时序知识图谱引擎，为 OpenZep 提供底层图谱能力。
- **[OASIS](https://github.com/camel-ai/oasis)** — 开放智能体社交交互模拟框架，为 MiroFish 提供多平台模拟能力。
- **[Neo4j](https://neo4j.com/)** — 图数据库，存储和查询知识图谱数据。
