// Semantic memory update, step 1: close the current version of a fact key.
MATCH (:Customer {id: $cid})-[:HAS_FACT]->(old:Fact {key: $key})
WHERE old.valid_to IS NULL
SET old.valid_to = $now
RETURN old.id AS old_fact_id
