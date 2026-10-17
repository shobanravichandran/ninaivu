// Procedural memory: relevance first, then learned success rate.
// Keep playbooks in the category whose cosine distance is within $margin of the closest match,
// then rank those near-equal candidates by success rate.
CALL db.idx.vector.queryNodes('Playbook', 'embedding', 20, vecf32($qvec)) YIELD node, score
WITH node, score WHERE node.category = $category
WITH min(score) AS best, collect(node) AS nodes, collect(score) AS scores
UNWIND range(0, size(nodes) - 1) AS i
WITH nodes[i] AS node, scores[i] AS distance, best
WHERE distance <= best + $margin
RETURN node.id AS playbook_id, node.name AS name, node.steps AS steps,
       node.success_count AS successes, node.fail_count AS failures, distance,
       toFloat(node.success_count) / (node.success_count + node.fail_count + 1) AS success_rate
ORDER BY success_rate DESC
LIMIT 3
