// Context pack: most recent finished sessions (episodic summaries).
MATCH (:Customer {id: $cid})-[:HAD_SESSION]->(s:Session)
WHERE s.summary IS NOT NULL
RETURN s.id AS session_id, s.started_at AS started_at, s.summary AS summary, s.sentiment AS sentiment
ORDER BY started_at DESC
LIMIT 3
