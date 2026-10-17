// UI: every version of every fact, current and superseded, newest first per key.
MATCH (:Customer {id: $cid})-[:HAS_FACT]->(f:Fact)
RETURN f.id AS fact_id, f.key AS key, f.text AS text, f.valid_from AS valid_from, f.valid_to AS valid_to
ORDER BY key, valid_from DESC
