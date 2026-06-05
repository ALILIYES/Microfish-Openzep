#!/usr/bin/env bash
# setup.sh — MicroFish-Docker 一键启动脚本
#
# 用法:
#   交互式:        bash setup.sh
#   非交互式:      LLM_API_KEY=sk-xxx LLM_BASE_URL=... bash setup.sh
#   本地开发模式:   OPENZEP_MODE=local bash setup.sh
#
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[ OK ]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERR ]${NC} $*"; exit 1; }
step()    { echo -e "\n${BOLD}${CYAN}▶ $*${NC}"; }

# ── 前置检查 ──────────────────────────────────────────────
command -v docker >/dev/null 2>&1 || error "请先安装 Docker"
docker compose version >/dev/null 2>&1 || error "请先安装 Docker Compose"

# ── 欢迎 ──────────────────────────────────────────────────
echo
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║     MicroFish Docker 一键安装向导       ║${NC}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════╝${NC}"
echo
echo -e "  包含: Neo4j + OpenZep + MiroFish"
echo

# ── .env 处理 ─────────────────────────────────────────────
ENV_FILE=".env"

if [[ -f "$ENV_FILE" ]]; then
    warn ".env 已存在，将读取现有配置"
    echo
    source_env() {
        while IFS='=' read -r key val; do
            [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue
            key=$(echo "$key" | tr -d '[:space:]')
            val=$(echo "$val" | tr -d '\r' | sed 's/^["'"'"']*//;s/["'"'"']*$//')
            printf -v "$key" '%s' "$val" 2>/dev/null || true
        done < "$ENV_FILE"
    }
    source_env
else
    info "首次运行，将创建 .env"
    echo
fi

# ── 交互式收集配置 ───────────────────────────────────────
# 仅在交互模式且变量未设置时询问
prompt() {
    local var="$1" prompt="$2" default="${3:-}" secret="${4:-0}"
    local current="${!var:-}"
    [[ -n "$current" ]] && { printf -v "$var" '%s' "$current"; return 0; }
    [[ ! -t 0 ]] && { [[ -n "$default" ]] && printf -v "$var" '%s' "$default"; return 0; }
    if [[ -n "$default" ]]; then
        printf "%b" "${BOLD}${prompt} [默认: ${default}]: ${NC}"
    else
        printf "%b" "${BOLD}${prompt}: ${NC}"
    fi
    if [[ "$secret" == "1" ]]; then read -rs val; echo; else read -r val; fi
    printf -v "$var" '%s' "${val:-$default}"
}

step "LLM 大模型配置"
prompt LLM_BASE_URL "LLM Base URL" "${LLM_BASE_URL:-https://api.deepseek.com/v1}"
prompt LLM_API_KEY "LLM API Key" "${LLM_API_KEY:-}" 1
prompt LLM_MODEL "LLM 模型名称" "${LLM_MODEL:-deepseek-chat}"
echo
prompt SEPARATE_EMBEDDER "单独配置 Embedder？[y/N]" "N" 0
if [[ "$SEPARATE_EMBEDDER" =~ ^[Yy]$ ]]; then
    prompt EMBEDDER_BASE_URL "Embedder Base URL" "${EMBEDDER_BASE_URL:-https://api.siliconflow.cn/v1}"
    prompt EMBEDDER_API_KEY "Embedder API Key" "${EMBEDDER_API_KEY:-}" 1
    prompt EMBEDDER_MODEL "Embedder 模型" "${EMBEDDER_MODEL:-BAAI/bge-m3}"
else
    EMBEDDER_BASE_URL="${EMBEDDER_BASE_URL:-}"
    EMBEDDER_API_KEY="${EMBEDDER_API_KEY:-}"
    EMBEDDER_MODEL="${EMBEDDER_MODEL:-BAAI/bge-m3}"
fi

step "安全配置"
prompt API_KEY "OpenZep API Key（留空自动生成）" "${API_KEY:-}" 1 0
[[ -z "$API_KEY" ]] && API_KEY="mfish-$(date +%s | md5sum 2>/dev/null || echo $RANDOM | head -c8)"
prompt NEO4J_PASSWORD "Neo4j 数据库密码" "${NEO4J_PASSWORD:-password123}" 0 0
NEO4J_PASSWORD="${NEO4J_PASSWORD:-password123}"

# ── 写入 .env ─────────────────────────────────────────────
step "写入配置文件"
[[ -f "$ENV_FILE" ]] && cp "$ENV_FILE" "${ENV_FILE}.bak" && info "已备份 .env → .env.bak"

cat > "$ENV_FILE" <<EOF
# ═══════════════════════════════════════════
# MicroFish-Docker 配置
# 生成时间: $(date '+%Y-%m-%d %H:%M:%S')
# ═══════════════════════════════════════════

# LLM
LLM_API_KEY=${LLM_API_KEY}
LLM_BASE_URL=${LLM_BASE_URL}
LLM_MODEL=${LLM_MODEL}
LLM_SMALL_MODEL=${LLM_SMALL_MODEL:-${LLM_MODEL}}

# Embedder
EMBEDDER_API_KEY=${EMBEDDER_API_KEY}
EMBEDDER_BASE_URL=${EMBEDDER_BASE_URL}
EMBEDDER_MODEL=${EMBEDDER_MODEL}

# Neo4j
NEO4J_PASSWORD=${NEO4J_PASSWORD}

# OpenZep Auth
API_KEY=${API_KEY}
EOF
success ".env 写入完成"

# ── 检查并创建 MiroFish 的 .env ──────────────────────────
MIROFISH_ENV="mirofish/.env"
if [[ ! -f "$MIROFISH_ENV" ]]; then
    info "创建 MiroFish .env..."
    cat > "$MIROFISH_ENV" <<EOF
# MiroFish 本地开发用 .env（Docker Compose 下由统一 .env 注入）
LLM_API_KEY=${LLM_API_KEY}
LLM_BASE_URL=${LLM_BASE_URL}
LLM_MODEL_NAME=${LLM_MODEL}
ZEP_API_KEY=${API_KEY}
ZEP_BASE_URL=http://localhost:8000/api/v2
EOF
    info "MiroFish .env 已创建"
fi

# ── 启动服务 ──────────────────────────────────────────────
step "启动 Docker Compose"
docker compose up -d --build

# ── 等待健康检查 ──────────────────────────────────────────
info "等待 OpenZep 就绪..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/healthz >/dev/null 2>&1; then
        success "OpenZep 服务已就绪"
        break
    fi
    sleep 2
    [[ "$i" -eq 30 ]] && warn "健康检查超时，请运行: docker compose logs openzep"
done

# ── 完成 ──────────────────────────────────────────────────
echo
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${GREEN}║        启动完成！                        ║${NC}"
echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════╝${NC}"
echo
echo -e "  Neo4j Browser: ${BOLD}http://localhost:7474${NC} (neo4j / ${NEO4J_PASSWORD})"
echo -e "  OpenZep API:   ${BOLD}http://localhost:8000${NC}"
echo -e "  OpenZep 文档:  ${BOLD}http://localhost:8000/docs${NC}"
echo -e "  MiroFish 前端: ${BOLD}http://localhost:3000${NC}"
echo -e "  MiroFish 后端: ${BOLD}http://localhost:5001${NC}"
echo
echo -e "  查看日志: ${BOLD}docker compose logs -f${NC}"
echo -e "  停止服务: ${BOLD}docker compose down${NC}"
echo
