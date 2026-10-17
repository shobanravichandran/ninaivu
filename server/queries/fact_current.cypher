// Semantic memory: the current version of one fact key (used to skip no-op updates).
MATCH (:Customer {id: $cid})-[:HAS_FACT]->(f:Fact {key: $key})
WHERE f.valid_to IS NULL
RETURN f.id AS fact_id, f.text AS text
