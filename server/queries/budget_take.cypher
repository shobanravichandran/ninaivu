// Demo budget: take one agent turn from today's allowance, atomically (writes to a graph run one at a time).
// Lives in its own graph (ninaivu_meta), never in a tenant's memory. ok = false means today's cap is used up.
MERGE (b:Budget {day: $day})
ON CREATE SET b.turns = 0
WITH b, b.turns < $cap AS ok
SET b.turns = b.turns + CASE WHEN ok THEN 1 ELSE 0 END
RETURN ok, b.turns AS turns
