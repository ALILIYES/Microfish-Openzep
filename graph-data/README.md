# 水浒传知识图谱

基于 **水浒传（Water Margin）186万字** 全文，通过 MicroFish 构建的知识图谱。

## 统计

| 指标 | 数量 |
|------|------|
| 节点 | 1,014 |
| 边 | 2,548 |
| Episodes | 2,457 |
| 实体类型 | 10 种 |

### 实体类型分布
- CourtOfficial (朝廷官员)
- MilitaryOfficer (武将)
- RebelLeader (梁山好汉)
- ReligiousLeader (宗教人物)
- LocalGentry (地方豪绅)
- Commoner (平民)
- Merchant (商人)
- Scholar (学者)
- Organization (组织)
- Person (人物)

## 快速恢复

```bash
# 1. 确保 Neo4j 在运行
docker compose up -d neo4j

# 2. 一键恢复
bash restore-graph.sh
```

**注意**：首次恢复前需在 Neo4j 中安装 APOC 插件。

在 `docker-compose.yml` 中已预设 `NEO4J_PLUGINS: '["apoc"]'`，如果 Neo4j 是本地裸跑的：

```bash
# 本地 Neo4j
cp nodes.csv edges.csv import.cypher /path/to/neo4j/import/
cypher-shell -u neo4j -p yourpassword -f import.cypher
```

## 文件说明

| 文件 | 大小 | 说明 |
|------|------|------|
| `cypher_nodes_export.csv.gz` | 9 MB | 压缩的节点数据 |
| `cypher_edges_export.csv.gz` | 18 MB | 压缩的边数据 |
| `import.cypher` | 1 KB | Neo4j 导入脚本 |
| `restore-graph.sh` | 2 KB | 一键恢复脚本 |

> 总计约 **27 MB**，解压后可直接导入任何 Neo4j 5.x 实例。
