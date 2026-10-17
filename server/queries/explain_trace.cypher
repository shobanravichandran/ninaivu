// Explainability: the handoff chain for an issue.
MATCH (:Customer {id: $cid})-[:RAISED]->(i:Issue {id: $iid})
OPTIONAL MATCH (h:Handoff)-[:FOR]->(i)
OPTIONAL MATCH (h)-[:FROM]->(f:Agent), (h)-[:TO]->(t:Agent)
RETURN i.title AS title, h.ts AS ts, f.name AS from_agent, t.name AS to_agent,
       h.reason AS reason, h.context AS context
ORDER BY ts
