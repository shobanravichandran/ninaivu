// History: the transcript of one session, in order.
MATCH (:Customer {id: $cid})-[:HAD_SESSION]->(:Session {id: $sid})-[:HAS_MESSAGE]->(m:Message)
RETURN m.seq AS seq, m.role AS role, m.agent AS agent, m.text AS text, m.ts AS ts
ORDER BY seq
