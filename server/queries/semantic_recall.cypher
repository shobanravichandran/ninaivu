// Semantic memory: vector search over facts, filtered to this customer's current facts.
// distance is cosine distance: lower means closer in meaning.
CALL db.idx.vector.queryNodes('Fact', 'embedding', 20, vecf32($qvec)) YIELD node, score
MATCH (:Customer {id: $cid})-[:HAS_FACT]->(node)
WHERE node.valid_to IS NULL
RETURN node.key AS key, node.text AS text, score AS distance
ORDER BY distance
LIMIT 5
