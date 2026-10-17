// Domain action (mock): initiate a refund, scoped to the customer.
MATCH (:Customer {id: $cid})-[:PLACED]->(o:Order {id: $order_id})
CREATE (o)-[:HAS_REFUND]->(r:Refund {id: $rid, amount: $amount, status: 'initiated', created_at: $now, by_agent: $agent})
RETURN r.id AS refund_id
