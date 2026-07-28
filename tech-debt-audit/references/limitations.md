# Limitations

Static repository inspection cannot prove runtime reachability, production traffic patterns, private infrastructure behavior, or the absence of vulnerabilities. Optional tools may be unavailable. Very large repositories require sampling, which must be stated.

Confidence should fall when tests cannot run, generated/vendor code dominates a path, deployment configuration is absent, or behavior depends on external systems. Record these limits in the report rather than filling gaps with assumptions.
