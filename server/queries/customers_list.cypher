// UI: customers in a tenant graph, with how many past sessions each has.
MATCH (c:Customer)
OPTIONAL MATCH (c)-[:HAD_SESSION]->(s:Session)
RETURN c.id AS id, c.name AS name, c.tier AS tier, count(s) AS sessions
ORDER BY id
