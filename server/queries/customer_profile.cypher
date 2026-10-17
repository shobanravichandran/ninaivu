// Context pack: who the agent is talking to.
MATCH (c:Customer {id: $cid})
RETURN c.id AS id, c.name AS name, c.tier AS tier
