// Episodic: close a session with the curator's summary.
MATCH (:Customer {id: $cid})-[:HAD_SESSION]->(s:Session {id: $sid})
SET s.ended_at = $now, s.summary = $summary, s.sentiment = $sentiment
RETURN s.id AS session_id
