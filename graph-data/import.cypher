// import.cypher — 从 CSV 导入水浒传知识图谱到 Neo4j
//
// 数据集:
//   nodes.csv — 1,014 个节点（2,457个 Episodes + 实体）
//   edges.csv — 2,548 条边（MENTIONS 关系 + 事实）
//
// 来源: 水浒传 (Water Margin) · 186万字
// 图谱类型: MicroFish 种子文档提取本体 (10种实体类型 + 10种关系类型)

// ═══ 创建约束和索引 ═══
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Entity) REQUIRE n.uuid IS UNIQUE;
CREATE INDEX IF NOT EXISTS FOR (n:Entity) FOR (n.name);

// ═══ 导入节点 ═══
// CSV 格式: n.uuid, n.name, labels, props
LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
WITH row,
     replace(replace(replace(row.labels, '[', ''), ']', ''), '"', '') AS clean_labels,
     replace(replace(replace(row.props, '{', ''), '}', ''), '"', '') AS clean_props
CALL apoc.merge.node(split(clean_labels, ','), {uuid: row.`n.uuid`})
YIELD node
SET node.name = row.`n.name`
RETURN count(node) AS nodes_imported;

// ═══ 导入边 ═══
// CSV 格式: a.name, type(r), b.name, r.fact, r.uuid, props
LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row
MATCH (a {name: row.`a.name`})
MATCH (b {name: row.`b.name`})
CALL apoc.merge.relationship(a, row.`type(r)`, {}, {}, b)
YIELD rel
RETURN count(rel) AS edges_imported;

// ═══ 验证 ═══
MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count ORDER BY count DESC;
MATCH ()-[r]->() RETURN type(r) AS relation, count(r) AS count ORDER BY count DESC;
