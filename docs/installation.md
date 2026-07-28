# Installation

## Clone the catalogue

```bash
git clone https://github.com/S1933/skills.git
cd skills
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate-skills.py
```

Point an Agent Skills-compatible client at the cloned directory, or symlink selected skill directories into the client’s skill root. Client locations differ; follow the client’s current documentation rather than copying a hardcoded global path.

## Install one skill

Copy or symlink the skill directory and every `supporting_files` entry listed for it in `skills-manifest.yaml`. Also install `requires_skills`; `optional_skills` are needed only for the corresponding integration. Check `clients`, `compatibility`, `requires_commands`, `requires_tools`, and `client_features` before activation.

## Public-only installation

Install entries whose manifest `visibility` is `public`. Do not install `private-skills/` into a shared or public environment. Private skills require separately maintained local configuration.

Create local environment configuration from the example when needed:

```bash
mkdir -p .local
cp .local/skills-environment.example.yaml .local/skills-environment.yaml
```

The real file is ignored by Git. Never commit hosts, users, account identifiers, project roots, or credentials.

## Validate an update

```bash
python3 -m unittest discover --start-directory tests --pattern 'test_*.py'
python3 -m unittest codex/tests/test_skill_policy.py
git-guardrails-claude-code/tests/test-guardrail.sh
python3 scripts/generate-catalogue.py --check
python3 scripts/generate-dependency-graph.py --check
python3 scripts/validate-evals.py
python3 scripts/validate-skills.py
```

Update with `git pull --ff-only`, review `CHANGELOG.md`, rerun validation, and restart or reload the client if it caches skill metadata.
