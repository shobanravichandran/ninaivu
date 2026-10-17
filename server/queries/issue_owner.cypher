// Routing: which agent owns this customer's most recent open issue?
MATCH (:Customer {id: $cid})-[:RAISED]->(i:Issue)-[:ASSIGNED_TO]->(a:Agent)
WHERE i.status <> 'resolved'
RETURN i.id AS issue_id, a.name AS owner, i.opened_at AS opened_at
ORDER BY opened_at DESC
LIMIT 1
