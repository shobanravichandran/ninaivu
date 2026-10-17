// Semantic memory: vector search over facts, filtered to this customer's current facts.
CALL db.idx.vector.queryNodes('Fact', 'embedding', 20, vecf32($qvec)) YIELD node, score
MATCH (:Customer {id: $cid})-[:HAS_FACT]->(node)
WHERE node.valid_to IS NULL
RETURN node.key AS key, node.text AS text, score
LIMIT 5
