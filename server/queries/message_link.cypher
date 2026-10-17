// History: chain messages in order.
MATCH (a:Message {id: $prev_mid}), (b:Message {id: $mid})
CREATE (a)-[:NEXT]->(b)
