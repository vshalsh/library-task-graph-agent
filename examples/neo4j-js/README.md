# Neo4j JavaScript adapter example

This standalone Node.js example imports task-graph v1 JSON into Neo4j and queries task readiness. It is isolated under this directory so you can copy it into another repository. The Python package remains the canonical validator and critical-path calculator; validate input before importing. See the official [Neo4j JavaScript Driver manual](https://neo4j.com/docs/javascript-manual/current/).

## Requirements

- Node.js LTS and npm
- Neo4j 4.4+ database, local or hosted
- A graph JSON file that passes task_graph_agent.validate_graph

## Run

From this directory:

    npm install
    export NEO4J_URI="neo4j+s://your-instance.databases.neo4j.io"
    export NEO4J_USERNAME="neo4j"
    export NEO4J_PASSWORD="your-password"
    export NEO4J_DATABASE="neo4j" # optional
    npm run import -- ../../examples/sample-task-graph.json
    npm run readiness -- daily-task-graph-demo

Keep credentials in environment variables or a secret manager; never commit them. The importer parameterizes data, uses fixed labels and relationship types, and groups writes in a managed transaction. Evidence is stored as JSON text because graph properties cannot hold nested objects.

## Mapping

- Nodes use the fixed GraphNode label with project_id, id, node_type, and input fields as properties.
- depends_on edges are stored in normalized dependent-to-prerequisite direction.
- blocks edges are reversed to that same direction.
- clarified_by edges are preserved separately and never treated as prerequisites.
- A composite uniqueness constraint and MERGE make repeated node and relationship imports idempotent.

This is a starter adapter, not a snapshot-reconciliation tool: removing an edge or node from source JSON does not delete the old database record. Use a dedicated database for the demo, and add explicit versioned reconciliation before sharing a database with other applications. The Cypher query demonstrates readiness only; use the Python core for full validation, blocker chains, and duration-aware critical path.

## Reuse in another repository

Copy this directory, install neo4j-driver, then adapt the input path and database configuration. The files are plain Node.js ES modules with no framework requirement.

