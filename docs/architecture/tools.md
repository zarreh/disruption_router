# Tools

## Rulebook lookup (`router.tools.rulebook`)

`lookup_clauses` performs a structured, deterministic lookup from the typed
rulebook. It matches on:

- `event_type` keywords
- `severity` keywords
- optional event guards: `sales`, `delay_days`, `shipping_mode`,
  `customer_tier`, `category`, `alternate_available`

The returned clauses are sorted by priority so the most specific guidance is
considered first.

## Cost estimation (`router.tools.cost`)

A placeholder model estimates carrier delay cost. It is intended to be replaced
or extended with real carrier contract data in production.
