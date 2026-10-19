import { driver, database } from "./connection.mjs";

const projectId = process.argv[2] || "daily-task-graph-demo";
const session = driver.session({ database });
try {
  const cypher = [
    "MATCH (task:GraphNode {project_id: $projectId, node_type: 'Task'})",
    "WHERE task.status IN ['open', 'in_progress']",
    "OPTIONAL MATCH path = (task)-[:GRAPH_EDGE*1..]->(prerequisite:GraphNode {project_id: $projectId, node_type: 'Task'})",
    "WHERE path IS NULL OR (all(rel IN relationships(path) WHERE rel.kind = 'dependency') AND all(n IN nodes(path) WHERE n.project_id = $projectId))",
    "WITH task, collect(DISTINCT CASE WHEN prerequisite IS NOT NULL AND prerequisite.status <> 'done' THEN prerequisite.id END) AS unresolved",
    "WITH task, [id IN unresolved WHERE id IS NOT NULL] AS unresolved",
    "RETURN task.id AS taskId, CASE WHEN size(unresolved) > 0 THEN 'blocked' WHEN task.status = 'in_progress' THEN 'in_progress' ELSE 'ready' END AS readiness, unresolved AS unresolvedPrerequisites",
    "ORDER BY task.id",
  ].join("\n");
  const result = await session.executeRead((tx) => tx.run(cypher, { projectId }));
  for (const row of result.records) {
    console.log({ taskId: row.get("taskId"), readiness: row.get("readiness"), unresolvedPrerequisites: row.get("unresolvedPrerequisites") });
  }
} finally {
  await session.close();
  await driver.close();
}

