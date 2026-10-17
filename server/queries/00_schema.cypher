// Indexes for every tenant graph. Statements are separated by semicolons.
// $EMBED_DIM is replaced at load time with the configured embedding dimension.
CREATE INDEX FOR (c:Customer) ON (c.id);
CREATE INDEX FOR (s:Session) ON (s.id);
CREATE INDEX FOR (m:Message) ON (m.id);
CREATE INDEX FOR (i:Issue) ON (i.id);
CREATE INDEX FOR (f:Fact) ON (f.id);
CREATE INDEX FOR (p:Playbook) ON (p.id);
CREATE INDEX FOR (a:Agent) ON (a.name);
CREATE INDEX FOR (o:Order) ON (o.id);
CREATE VECTOR INDEX FOR (f:Fact) ON (f.embedding) OPTIONS {dimension: $EMBED_DIM, similarityFunction: 'cosine'};
CREATE VECTOR INDEX FOR (p:Playbook) ON (p.embedding) OPTIONS {dimension: $EMBED_DIM, similarityFunction: 'cosine'}
