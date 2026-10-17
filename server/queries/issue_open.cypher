// Shared state: open an issue in the current session.
MATCH (c:Customer {id: $cid})-[:HAD_SESSION]->(s:Session {id: $sid})
CREATE (c)-[:RAISED]->(i:Issue {id: $iid, title: $title, category: $category, status: 'open', opened_at: $now})
CREATE (i)-[:DISCUSSED_IN]->(s)
RETURN i.id AS issue_id
