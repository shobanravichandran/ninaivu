// Episodic: open a new session for a customer.
MATCH (c:Customer {id: $cid})
CREATE (c)-[:HAD_SESSION]->(s:Session {id: $sid, started_at: $now, channel: $channel})
RETURN s.id AS session_id
