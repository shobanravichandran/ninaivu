// UI: customers in a tenant graph.
MATCH (c:Customer)
RETURN c.id AS id, c.name AS name, c.tier AS tier
ORDER BY id
