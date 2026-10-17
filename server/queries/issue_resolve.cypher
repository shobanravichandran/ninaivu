// Close an issue.
MATCH (:Customer {id: $cid})-[:RAISED]->(i:Issue {id: $iid})
SET i.status = 'resolved', i.resolved_at = $now, i.resolution = $resolution
RETURN i.id AS issue_id
