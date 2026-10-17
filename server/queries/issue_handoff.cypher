// Coordination: atomic ownership transfer. Zero rows means the caller is not the current owner.
MATCH (:Customer {id: $cid})-[:RAISED]->(i:Issue {id: $iid})-[r:ASSIGNED_TO]->(from:Agent {name: $from_agent})
MATCH (to:Agent {name: $to_agent})
DELETE r
CREATE (i)-[:ASSIGNED_TO {since: $now}]->(to)
CREATE (h:Handoff {id: $hid, reason: $reason, context: $context, ts: $now})
CREATE (h)-[:FROM]->(from), (h)-[:TO]->(to), (h)-[:FOR]->(i)
RETURN h.id AS handoff_id
