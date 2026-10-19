import neo4j from "neo4j-driver";

const required = ["NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"];
for (const name of required) {
  if (!process.env[name]) throw new Error("Set " + name + " in the environment.");
}

export const driver = neo4j.driver(
  process.env.NEO4J_URI,
  neo4j.auth.basic(process.env.NEO4J_USERNAME, process.env.NEO4J_PASSWORD),
);
export const database = process.env.NEO4J_DATABASE || "neo4j";

