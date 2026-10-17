// Semantic memory update, step 2: new fact version with provenance.
MATCH (c:Customer {id: $cid})-[:HAD_SESSION]->(s:Session {id: $sid})
CREATE (c)-[:HAS_FACT]->(f:Fact {id: $fid, key: $key, text: $text, valid_from: $now, embedding: vecf32($vec)})-[:LEARNED_IN]->(s)
RETURN f.id AS fact_id
