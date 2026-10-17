// Procedural memory: similar playbooks in a category, ranked by learned success rate.
CALL db.idx.vector.queryNodes('Playbook', 'embedding', 10, vecf32($qvec)) YIELD node, score
WITH node, score WHERE node.category = $category
RETURN node.id AS playbook_id, node.name AS name, node.steps AS steps,
       node.success_count AS successes, node.fail_count AS failures,
       toFloat(node.success_count) / (node.success_count + node.fail_count + 1) AS success_rate
ORDER BY success_rate DESC
LIMIT 3
