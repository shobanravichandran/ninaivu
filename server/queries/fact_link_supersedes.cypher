// Semantic memory update, step 3: keep history.
MATCH (new:Fact {id: $fid}), (old:Fact {id: $old_fid})
CREATE (new)-[:SUPERSEDES]->(old)
