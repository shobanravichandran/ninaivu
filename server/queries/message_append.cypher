// History: append one message to a session.
// Returns the previous last message id (if any) so the caller can run message_link.
MATCH (:Customer {id: $cid})-[:HAD_SESSION]->(s:Session {id: $sid})
OPTIONAL MATCH (s)-[:HAS_MESSAGE]->(prev:Message)
WITH s, prev ORDER BY prev.seq DESC LIMIT 1
CREATE (s)-[:HAS_MESSAGE]->(m:Message {id: $mid, seq: coalesce(prev.seq, 0) + 1, role: $role, agent: $agent, text: $text, ts: $now})
RETURN m.id AS message_id, prev.id AS prev_message_id
