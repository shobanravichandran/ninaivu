// UI graph view: the customer's memory neighbourhood (two hops, any direction, messages left out).
MATCH p = (:Customer {id: $cid})-[*1..2]-(n)
WHERE NOT n:Message
RETURN p
LIMIT 400
