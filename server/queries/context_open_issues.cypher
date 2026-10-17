// Context pack: open issues with current owner and related order.
MATCH (:Customer {id: $cid})-[:RAISED]->(i:Issue)
WHERE i.status <> 'resolved'
OPTIONAL MATCH (i)-[:ASSIGNED_TO]->(a:Agent)
OPTIONAL MATCH (i)-[:ABOUT]->(o:Order)
RETURN i.id AS issue_id, i.title AS title, i.category AS category, i.status AS status,
       i.opened_at AS opened_at, a.name AS owner, o.id AS order_id
ORDER BY opened_at DESC
