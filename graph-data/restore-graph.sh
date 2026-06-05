#!/usr/bin/env bash
# restore-graph.sh — 恢复水浒传知识图谱到 Neo4j
#
# 用法:
#   1. 确保 Neo4j 运行中 (docker compose up -d neo4j)
#   2. bash restore-graph.sh
#
# 需要工具: gzip, Docker
set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[ OK ]${NC} $*"; }

THIS_DIR="$(cd "$(dirname "$0")" && pwd)"
NODES_CSV="${THIS_DIR}/cypher_nodes_export.csv"
EDGES_CSV="${THIS_DIR}/cypher_edges_export.csv"

# ── 解压 ──
if [[ ! -f "$NODES_CSV" ]]; then
    if [[ -f "${NODES_CSV}.gz" ]]; then
        info "解压节点数据..."
        gzip -dk "${NODES_CSV}.gz"
    else
        echo "错误: 找不到 cypher_nodes_export.csv 或 .gz"
        exit 1
    fi
fi

if [[ ! -f "$EDGES_CSV" ]]; then
    if [[ -f "${EDGES_CSV}.gz" ]]; then
        info "解压边数据..."
        gzip -dk "${EDGES_CSV}.gz"
    else
        echo "错误: 找不到 cypher_edges_export.csv 或 .gz"
        exit 1
    fi
fi

# ── 获取 Neo4j 容器名 ──
CONTAINER=$(docker ps --format '{{.Names}}' | grep -i neo4j | head -1)
if [[ -z "$CONTAINER" ]]; then
    echo "错误: 找不到运行中的 Neo4j 容器"
    echo "请先启动: docker compose up -d neo4j"
    exit 1
fi
info "Neo4j 容器: ${CONTAINER}"

# ── 复制 CSV 到容器 ──
info "复制数据到容器..."
docker cp "$NODES_CSV" "${CONTAINER}:/var/lib/neo4j/import/nodes.csv"
docker cp "$EDGES_CSV" "${CONTAINER}:/var/lib/neo4j/import/edges.csv"
docker cp "${THIS_DIR}/import.cypher" "${CONTAINER}:/var/lib/neo4j/import/import.cypher"

# ── 执行 Cypher 导入 ──
info "正在导入图谱（可能需要几分钟）..."
docker exec "$CONTAINER" cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-password123}" \
    -f /var/lib/neo4j/import/import.cypher 2>&1 | tail -5

success "图谱恢复完成！"
echo
echo "打开 Neo4j Browser: http://localhost:7474"
echo "运行测试查询: MATCH (n) RETURN labels(n), count(n)"
