// "What did this customer ask for since $since, and was it resolved?"
MATCH (:Customer {id: $cid})-[:RAISED]->(i:Issue)-[:DISCUSSED_IN]->(s:Session)
WHERE s.started_at >= $since
OPTIONAL MATCH (i)-[t:TRIED]->(p:Playbook)
WHERE t.success = true
RETURN i.id AS issue_id, i.title AS title, i.status AS status, i.opened_at AS opened_at,
       i.resolved_at AS resolved_at, i.resolution AS resolution,
       collect(DISTINCT p.name) AS fixes, count(DISTINCT s) AS sessions
ORDER BY opened_at DESC
