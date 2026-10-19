import fs from "node:fs/promises";
import { driver, database } from "./connection.mjs";

const inputPath = process.argv[2] || "../../examples/sample-task-graph.json";
const graph = JSON.parse(await fs.readFile(inputPath, "utf8"));
if (graph.schema_version !== "1.0" || !graph.project?.id || !Array.isArray(graph.nodes) || !Array.isArray(graph.edges)) {
  throw new Error("Expected task-graph v1 JSON. Validate with the Python core before importing.");
}

const projectId = graph.project.id;
const nodeRows = graph.nodes.map((node) => {
  const properties = {};
  for (const key of ["type", "title", "description", "status", "priority", "estimate_minutes", "due_date"]) {
    if (node[key] !== undefined) properties[key === "type" ? "node_type" : key] = node[key];
  }
  properties.evidence_json = JSON.stringify(node.evidence || []);
  return { id: node.id, properties };
});
const dependencyRows = [];
const clarificationRows = [];
for (const edge of graph.edges) {
  if (edge.type === "depends_on") {
    dependencyRows.push({ dependent_id: edge.from, prerequisite_id: edge.to, source_type: edge.type });
  } else if (edge.type === "blocks") {
    dependencyRows.push({ dependent_id: edge.to, prerequisite_id: edge.from, source_type: edge.type });
  } else if (edge.type === "clarified_by") {
    clarificationRows.push({ from_id: edge.from, to_id: edge.to, source_type: edge.type });
  } else {
    throw new Error("Unsupported edge type: " + edge.type);
  }
}

const session = driver.session({ database });
try {
  const constraintResult = await session.run("CREATE CONSTRAINT graph_node_identity IF NOT EXISTS FOR (n:GraphNode) REQUIRE (n.project_id, n.id) IS UNIQUE");
  await constraintResult.consume();
  await session.executeWrite(async (tx) => {
    await tx.run("UNWIND $rows AS row MERGE (n:GraphNode {project_id: $projectId, id: row.id}) SET n += row.properties", { projectId, rows: nodeRows });
    if (dependencyRows.length) {
      await tx.run("UNWIND $rows AS row MATCH (dependent:GraphNode {project_id: $projectId, id: row.dependent_id}) MATCH (prerequisite:GraphNode {project_id: $projectId, id: row.prerequisite_id}) MERGE (dependent)-[:GRAPH_EDGE {kind: 'dependency', source_type: row.source_type}]->(prerequisite)", { projectId, rows: dependencyRows });
    }
    if (clarificationRows.length) {
      await tx.run("UNWIND $rows AS row MATCH (source:GraphNode {project_id: $projectId, id: row.from_id}) MATCH (target:GraphNode {project_id: $projectId, id: row.to_id}) MERGE (source)-[:GRAPH_EDGE {kind: 'clarified_by', source_type: row.source_type}]->(target)", { projectId, rows: clarificationRows });
    }
  });
  console.log("Imported " + nodeRows.length + " nodes for project " + projectId + ".");
} finally {
  await session.close();
  await driver.close();
}

