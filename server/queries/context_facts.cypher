// Context pack: current (non-superseded) facts about the customer.
MATCH (:Customer {id: $cid})-[:HAS_FACT]->(f:Fact)
WHERE f.valid_to IS NULL
RETURN f.id AS fact_id, f.key AS key, f.text AS text, f.valid_from AS since
ORDER BY since DESC
LIMIT 20
