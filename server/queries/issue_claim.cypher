// Coordination: race-safe claim. Returns a row only if the issue was unassigned.
MATCH (:Customer {id: $cid})-[:RAISED]->(i:Issue {id: $iid})
WHERE NOT (i)-[:ASSIGNED_TO]->()
MATCH (a:Agent {name: $agent})
CREATE (i)-[:ASSIGNED_TO {since: $now}]->(a)
RETURN a.name AS owner
