// STRETCH: cluster open issues by shared orders/products with label propagation.
CALL algo.labelPropagation({nodeLabels: ['Issue', 'Order', 'Product'], relationshipTypes: ['ABOUT', 'CONTAINS']})
YIELD node, communityId
WITH communityId, collect(node) AS members
WITH communityId, [n IN members WHERE n:Issue AND n.status <> 'resolved'] AS open_issues
WHERE size(open_issues) >= $min_size
RETURN communityId, [n IN open_issues | n.title] AS titles, size(open_issues) AS open_count
ORDER BY open_count DESC
