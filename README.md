# Registre de skills S1933

Un manifeste déclaratif de skills d'agents. Aucun contenu de skill n'est versionné ici — uniquement des entrées `{name, owner, repo, role}` dans `registry.json`. Les fichiers des skills sont récupérés au moment de l'installation depuis les dépôts upstream référencés sur [skills.sh](https://skills.sh/).

## Démarrage rapide

```bash
./install.sh            # efface les skills locales (en respectant .gitignore) + installe tout
./install.sh --dry-run  # aperçu, sans rien modifier
./validate-registry.sh  # vérifie count === skills.length, rôles valides, aucun doublon
```

`./install.sh` est idempotent : chaque exécution efface l'installation précédente (en respectant `.gitignore`) et réinstalle l'intégralité du registre à partir de zéro. Il n'existe volontairement aucun autre flag — garder la surface minimale.

### Pourquoi les installations sont globales

Ce checkout **est** le répertoire global des skills : `~/.claude/skills` est un lien symbolique vers `~/.agents/skills`, qui est ce dépôt. `install.sh` exécute donc `npx skills add -g`, dont la racine globale est exactement `~/.agents/skills` — la racine du dépôt. Les skills arrivent sous forme de répertoires de premier niveau, à côté de `registry.json`.

Sans `-g`, la CLI détecte un projet (ce dépôt contient un `.git`) et imbrique tout sous `./.agents/skills/` avec des liens symboliques dans `./.claude/skills/`, ce qui produit un dédoublement `~/.agents/skills/.agents/skills/`. `install.sh` supprime ces chemins à chaque exécution, et `.gitignore` les bloque.

## Ce qu'on trouve ici

| Source | Nombre | Rôle |
|---|---:|---|
| [`mattpocock/skills`](https://github.com/mattpocock/skills) | 16 | Ingénierie (grilling, TDD, diagnostic, revue de code, codebase-design) |
| [`obra/superpowers`](https://github.com/obra/superpowers) | 7 | Exécution (worktrees, sous-agents, orchestration de revue, vérification, clôture) |
| [`multica-ai/andrej-karpathy-skills`](https://github.com/multica-ai/andrej-karpathy-skills) | 1 | Discipline de code (anti-suringénierie) |
| [`anthropics/knowledge-work-plugins`](https://github.com/anthropics/knowledge-work-plugins) | 1 | Audit de dette technique |
| [`juliusbrussee/caveman`](https://github.com/juliusbrussee/caveman) | 1 | Style de sortie |
| [`ayghri/i-have-adhd`](https://github.com/ayghri/i-have-adhd) | 1 | Style de sortie |
| [`humanlayer/skills`](https://github.com/humanlayer/skills) | 1 | Explication visuelle (`show-me`) |
| [`hardikpandya/stop-slop`](https://github.com/hardikpandya/stop-slop) | 1 | Nettoyage de prose (suppression des marqueurs IA) |
| [`getsentry/skills`](https://github.com/getsentry/skills) | 1 | Revue de sécurité (basée OWASP) |
| **Total** | **30** | |

Matt Pocock (discipline d'ingénierie) × obra/superpowers (exécution/orchestration). Les deux collections prises intégralement provoqueraient des collisions de règles et des doublons ; nous avons donc retenu le meilleur de chacune. `obra/superpowers/brainstorming` est exclu — son HARD-GATE entre en conflit avec l'hybride.

## Rôles

Chaque entrée de `registry.json` possède un `role` ∈ {`discovery`, `design`, `implementation`, `setup`, `quality`, `delivery`, `style`} qui documente sa raison d'être. Distribution actuelle :

| Rôle | Nombre | Ce que ça couvre |
|---|---:|---|
| `discovery` | 2 | `grilling`, `grill-with-docs` — affiner la question avant de concevoir |
| `design` | 7 | `codebase-design`, `domain-modeling`, `prototype`, `to-spec`, `to-tickets`, `improve-codebase-architecture`, `writing-for-agents` |
| `implementation` | 4 | `tdd`, `executing-plans`, `subagent-driven-development`, `using-git-worktrees` |
| `quality` | 8 | `code-review`, `diagnosing-bugs`, `karpathy-guidelines`, `receiving-code-review`, `requesting-code-review`, `security-review`, `tech-debt`, `triage` |
| `delivery` | 3 | `finishing-a-development-branch`, `handoff`, `verification-before-completion` |
| `style` | 5 | `caveman`, `i-have-adhd`, `show-me`, `stop-slop`, `wait-what` — forme de la sortie |
| `setup` | 1 | `setup-matt-pocock-skills` — onboarding |

## Liste complète des skills

| Skill | Source | Rôle | Ce qu'elle fait |
|---|---|---:|---|
| `caveman` | juliusbrussee/caveman | style | Mode de sortie ultra-compressé |
| `code-review` | mattpocock/skills | quality | Revue des changements depuis un point fixe (commit/branche) |
| `codebase-design` | mattpocock/skills | design | Vocabulaire commun pour concevoir des modules profonds |
| `diagnosing-bugs` | mattpocock/skills | quality | Boucle de diagnostic rigoureuse pour bugs/régressions difficiles |
| `domain-modeling` | mattpocock/skills | design | Construire et affiner le modèle de domaine d'un projet |
| `executing-plans` | obra/superpowers | implementation | Exécuter un plan d'implémentation écrit |
| `finishing-a-development-branch` | obra/superpowers | delivery | Clôturer une branche terminée (vérification, merge) |
| `grill-with-docs` | mattpocock/skills | discovery | Affiner un plan via une interrogation ancrée dans la documentation |
| `grilling` | mattpocock/skills | discovery | Interroger l'utilisateur sans relâche sur un plan |
| `handoff` | mattpocock/skills | delivery | Condenser une conversation en document de passation |
| `i-have-adhd` | ayghri/i-have-adhd | style | Adapter la sortie à un lecteur TDAH |
| `improve-codebase-architecture` | mattpocock/skills | design | Repérer les opportunités d'approfondissement dans une base de code |
| `karpathy-guidelines` | multica-ai/andrej-karpathy-skills | quality | Réduire les erreurs de code courantes des LLM |
| `prototype` | mattpocock/skills | design | Prototype jetable pour répondre à une question de conception |
| `receiving-code-review` | obra/superpowers | quality | Traiter correctement les retours de revue reçus |
| `requesting-code-review` | obra/superpowers | quality | Revue avant commit (sécurité, portes de qualité) |
| `security-review` | getsentry/skills | quality | Revue de code sécurité à la recherche de vulnérabilités (basée OWASP) |
| `setup-matt-pocock-skills` | mattpocock/skills | setup | Configurer ce dépôt pour les skills d'ingénierie |
| `show-me` | humanlayer/skills | style | Expliquer visuellement le sujet en cours |
| `stop-slop` | hardikpandya/stop-slop | style | Supprimer les tics d'écriture IA de la prose |
| `subagent-driven-development` | obra/superpowers | implementation | Exécuter des plans via des sous-agents délégués |
| `tdd` | mattpocock/skills | implementation | Développement piloté par les tests (RED-GREEN-REFACTOR) |
| `tech-debt` | anthropics/knowledge-work-plugins | quality | Identifier, catégoriser et prioriser la dette technique |
| `to-spec` | mattpocock/skills | design | Transformer une conversation en spécification |
| `to-tickets` | mattpocock/skills | design | Découper un plan ou une spec en tickets |
| `triage` | mattpocock/skills | quality | Faire circuler les issues dans une machine à états de rôles |
| `using-git-worktrees` | obra/superpowers | implementation | Travail de fonctionnalité isolé via les worktrees git |
| `verification-before-completion` | obra/superpowers | delivery | Vérifier avant de déclarer le travail terminé |
| `wait-what` | mattpocock/skills | style | Reformuler quand un message n'est pas passé |
| `writing-for-agents` | mattpocock/skills | design | Rédiger des documents destinés à être consommés par des agents |

## Précédence des skills

Quand plusieurs skills sont actives, résoudre les conflits dans cet ordre (le
plus spécifique gagne) :

1. Workflow explicite propre à la tâche
2. Skill d'orchestration
3. Skill de domaine / de processus
4. Directive comportementale générale
5. Skill de style

Quand une **skill d'orchestration** est explicitement active, son protocole
d'exécution prime sur les directives comportementales génériques. Par exemple,
pendant `subagent-driven-development`, l'ambiguïté est tranchée par le protocole
d'arbitrage SDD — et non en s'arrêtant pour poser une question
(`karpathy-guidelines`).

## Contrat TDD / plan

`tdd` exige que les points d'accroche de test (test seams) soient établis avant
d'écrire les tests. Les plans censés s'exécuter de façon autonome doivent
décider des test seams *avant* d'entrer dans `subagent-driven-development`, afin
qu'une exécution autonome ne soit pas interrompue en cours de route.

```text
Découverte → Conception → Spec → Test seams décidés → Plan d'implémentation
   → Subagent-driven development → Cycles TDD
```

Les plans destinés à une exécution autonome doivent figer les test seams avant
d'entrer dans subagent-driven-development.

## Format du registre

```json
{"name": "tdd", "owner": "mattpocock", "repo": "skills", "role": "implementation"}
```

- `name` — unique dans tout le registre (garde-fou contre les collisions de namespace)
- `owner` + `repo` — identité de la source, doit correspondre à l'upstream
- `role` — obligatoire, l'un des sept ci-dessus
- `count` en tête doit être égal à `skills.length` (vérifié par `validate-registry.sh`)

Le lockfile vit en dehors de ce dépôt. Les installations globales enregistrent leur état dans `~/.agents/.skill-lock.json`, partagé avec les skills installées par d'autres moyens (les skills privées listées plus bas) ; `./install.sh` ne le réécrit donc jamais intégralement — `npx skills add` met à jour ses propres entrées.

## Ajouter une skill

1. Confirmer l'upstream sur [skills.sh](https://skills.sh/) — noter le couple `(owner, repo)` exact et le nom de la skill.
2. Éditer `registry.json` :
   - Ajouter `{name, owner, repo, role}` à `skills[]` en **ordre alphabétique par nom** (le validateur l'impose).
   - Incrémenter `count`, `version` et `generated_at`.
3. `./validate-registry.sh` puis `./install.sh --dry-run`.
4. Commiter et pousser — la CI lance automatiquement les tests unitaires, le contrôle d'intégrité, la validation de schéma et les vérifications d'accessibilité de l'upstream.

## Intégration continue

Trois workflows GitHub Actions dans `.github/workflows/` :

- **`validate-registry.yml`** — se déclenche sur push/PR touchant `registry.json`,
  le schéma, `install.sh`, `validate-registry.sh`, `.gitignore`, `scripts/**`,
  `tests/**`, ou lui-même. Étapes : tests unitaires, contrôle d'intégrité du
  registre (validation contre `registry.schema.json`), smoke test de `install.sh`
  en dry-run, et vérification que chaque entrée du registre a effectivement été
  planifiée dans la sortie du dry-run.
- **`verify-upstreams.yml`** — se déclenche sur push/PR touchant `registry.json`
  ou le script upstream, plus une fois par semaine (lundis 06:00 UTC) et sur
  déclenchement manuel. Résout chaque skill via l'arbre git récursif de GitHub et
  lit le `name:` du frontmatter (sans supposer de `directory-name`), de sorte
  qu'un changement de layout upstream ne casse **pas** la détection. Une skill
  manquante ou inaccessible fait échouer la CI de façon bloquante.
- **`check-upstream-drift.yml`** — hebdomadaire (mardis 07:00 UTC) +
  déclenchement manuel. Signale quand le SHA de blob d'un SKILL.md sélectionné a
  changé depuis la dernière revue humaine (`reviewed-upstreams.json`). Il ne fait
  que signaler la dérive — accepter un changement upstream reste une étape
  manuelle et délibérée.

## Arborescence

```
.
├── README.md
├── registry.json          # 30 entrées (la source de vérité)
├── registry.schema.json   # contrat structurel (JSON Schema)
├── reviewed-upstreams.json# dernier état upstream revu par un humain
├── install.sh             # durci : préflight, sauvegarde, rollback, validation
├── validate-registry.sh   # invariants métier (count, rôles, doublons, tri, TBD)
├── .gitignore             # exclut /[REMOVED-INTERNAL-SKILL]/, /[REMOVED-INTERNAL-SKILL]/, etc. + artefacts d'install parasites
├── scripts/
│   ├── verify-upstreams.py      # accessibilité (arbre git récursif + frontmatter)
│   └── check-upstream-drift.py  # dérive (SHA de blob vs reviewed-upstreams.json)
├── tests/                 # suite unittest de la stdlib
├── <skill-name>/          # un répertoire par skill installée, à la racine
└── .github/workflows/
    ├── validate-registry.yml
    ├── verify-upstreams.yml
    └── check-upstream-drift.yml
```

## Justification du `.gitignore`

`/[REMOVED-INTERNAL-SKILL]/`, `/[REMOVED-INTERNAL-SKILL]/`, `/[REMOVED-INTERNAL-MARKER]/`, `/[REMOVED-INTERNAL-SKILL]/`, `/[REMOVED-INTERNAL-SKILL]/`, `/[REMOVED-INTERNAL-SKILL]/`, `/[REMOVED-INTERNAL-SKILL]/` sont des skills privées ou personnalisées qui ne font pas partie de la distribution publique — elles sont préservées lors de l'effacement.

`/.agents/`, `/.claude/` et `/skills-lock.json` sont des artefacts de `npx skills add` à portée projet. Les installations étant globales (`-g`) et posées directement à la racine du dépôt, ces chemins ne devraient jamais réapparaître ; `./install.sh` les supprime à chaque exécution, en filet de sécurité.
