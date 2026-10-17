// Link an issue to an order. Both must belong to the same customer, which keeps tools scoped.
MATCH (c:Customer {id: $cid})-[:RAISED]->(i:Issue {id: $iid}), (c)-[:PLACED]->(o:Order {id: $order_id})
MERGE (i)-[:ABOUT]->(o)
RETURN o.id AS order_id
