// Procedural memory: learn from an attempt. $success_int is 1 or 0.
MATCH (:Customer {id: $cid})-[:RAISED]->(i:Issue {id: $iid}), (p:Playbook {id: $pid})
CREATE (i)-[:TRIED {success: $success_int = 1, at: $now}]->(p)
SET p.success_count = p.success_count + $success_int,
    p.fail_count = p.fail_count + 1 - $success_int
RETURN p.success_count AS success_count, p.fail_count AS fail_count
