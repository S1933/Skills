# Deployment checklist

- A failing behavioral or trigger case was observed before editing guidance.
- Frontmatter, name, description, invocation, and compatibility validate.
- Required/optional skills, tools, commands, aliases, and clients are declared.
- Main-file word budget passes or has a reviewed exception.
- Links, supporting files, YAML/JSON examples, diagrams, and scripts validate.
- Public content contains no secrets or private environment details.
- Dangerous examples have explicit safety constraints and regression cases.
- Positive, negative, ambiguous, collision, and compliance evaluations pass.
- Generated catalogue and dependency documentation is current.
- The diff was reviewed for duplicated guidance and accidental behavior loss.

Render Graphviz blocks with `../scripts/render-graphs.js` when visual verification is useful.
