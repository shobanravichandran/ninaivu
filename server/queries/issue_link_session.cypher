// Episodic: mark an existing issue as discussed in this session.
MATCH (c:Customer {id: $cid})-[:RAISED]->(i:Issue {id: $iid}), (c)-[:HAD_SESSION]->(s:Session {id: $sid})
MERGE (i)-[:DISCUSSED_IN]->(s)
