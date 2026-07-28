# Description optimisation

Descriptions are discovery metadata. They should answer only “when should this load?” because agents may see them before the skill body.

For automatic skills, start with `Use when` and list observable task types, symptoms, or conditions. Prefer concrete domain vocabulary and likely user phrasing. Do not summarize the workflow, advertise benefits, write in first person, or repeat the skill name.

For manual wrappers, use `Use when explicitly ...` and name the user-visible outcome. Keep descriptions between 80 and 250 characters when practical and never above the repository maximum.

Before finalizing, test positive prompts, nearby negative prompts, ambiguous wording, and collisions with related skills. Optimize for precision and recall together; adding every possible keyword usually harms precision.

Extended examples are in [full guidance](full-guidance.md#skill-discovery-optimization-sdo).
