// Initialize Neo4j with constraints and indexes for the autonomous code improver

// Create uniqueness constraints
CREATE CONSTRAINT symbol_id_unique IF NOT EXISTS FOR (s:Symbol) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT edge_id_unique IF NOT EXISTS FOR (e:Edge) REQUIRE e.id IS UNIQUE;

// Create indexes for common queries
CREATE INDEX symbol_name_index IF NOT EXISTS FOR (s:Symbol) ON (s.name);
CREATE INDEX symbol_type_index IF NOT EXISTS FOR (s:Symbol) ON (s.type);
CREATE INDEX symbol_file_path_index IF NOT EXISTS FOR (s:Symbol) ON (s.file_path);
CREATE INDEX symbol_language_index IF NOT EXISTS FOR (s:Symbol) ON (s.language);
CREATE INDEX symbol_repo_id_index IF NOT EXISTS FOR (s:Symbol) ON (s.repo_id);
CREATE INDEX edge_type_index IF NOT EXISTS FOR (e:Edge) ON (e.type);
CREATE INDEX edge_repo_id_index IF NOT EXISTS FOR (e:Edge) ON (e.repo_id);

// Create full-text search index for symbols
CREATE FULLTEXT INDEX symbol_name_fulltext IF NOT EXISTS FOR (s:Symbol) ON EACH [s.name, s.description];

// Create procedures for common queries

// Procedure to get call graph
CREATE OR REPLACE PROCEDURE getCallGraph(repoId STRING)
YIELD caller, callee
MATCH (caller:Symbol {repo_id: repoId})-[:RELATES {type: 'calls'}]->(callee:Symbol {repo_id: repoId})
RETURN caller.name AS caller, callee.name AS callee;

// Procedure to get endpoints without validation
CREATE OR REPLACE PROCEDURE getEndpointsWithoutValidation(repoId STRING)
YIELD name, file_path, parameters
MATCH (func:Symbol {repo_id: repoId, type: 'function'})
WHERE func.metadata IS NOT NULL
AND func.metadata.parameters IS NOT NULL
AND size(func.metadata.parameters) > 0
AND NOT EXISTS {
    MATCH (func)-[:RELATES {type: 'calls'}]->(validator:Symbol)
    WHERE validator.name CONTAINS 'validate' OR validator.name CONTAINS 'check'
}
RETURN func.name AS name, func.file_path AS file_path, func.metadata.parameters AS parameters;

// Procedure to get orphan symbols
CREATE OR REPLACE PROCEDURE getOrphanSymbols(repoId STRING)
YIELD id, name, type, file_path
MATCH (s:Symbol {repo_id: repoId})
WHERE NOT EXISTS {
    MATCH ()-[:RELATES]->(s)
}
AND s.type <> 'module'
RETURN s.id AS id, s.name AS name, s.type AS type, s.file_path AS file_path;

// Procedure to get cycles
CREATE OR REPLACE PROCEDURE getCycles(repoId STRING)
YIELD cycle
MATCH (s1:Symbol {repo_id: repoId})-[:RELATES*]->(s2:Symbol {repo_id: repoId})
WHERE s1 = s2
WITH s1, s2
MATCH path = (s1)-[:RELATES*]->(s2)
RETURN [node IN nodes(path) | node.name] AS cycle
LIMIT 100;
