// Domain tool: order details, scoped to the customer.
MATCH (:Customer {id: $cid})-[:PLACED]->(o:Order {id: $order_id})
OPTIONAL MATCH (o)-[:CONTAINS]->(p:Product)
OPTIONAL MATCH (o)-[:HAS_REFUND]->(r:Refund)
RETURN o.id AS order_id, o.status AS status, o.amount AS amount, o.date AS date,
       collect(DISTINCT p.name) AS products,
       collect(DISTINCT {id: r.id, status: r.status, amount: r.amount, created_at: r.created_at}) AS refunds
