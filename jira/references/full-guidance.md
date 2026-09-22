---
name: jira
description: Use when a locally configured Jira CLI is required to inspect or mutate issues, comments, assignments, transitions, Tempo entries, or Confluence pages.
compatibility: Environment-specific; requires the locally configured private Jira CLI.
---

# Jira CLI (locale)

> Dernière mise à jour : synchronisée avec le code source au 2026-07-21.

CLI Go locale (`<jira-cli-path>`, sources : `<jira-source-root>`) pour une
instance Jira Server/Data Center privée. **Ce n'est PAS
ankitpokhrel/jira-cli** : les sous-commandes `jira issue list`, `jira me`,
`jira issue move` n'existent pas ici.

## Commandes

| Intention utilisateur | Commande |
|---|---|
| Lister mes tickets assignés | `jira ls` |
| ... y compris résolus | `jira ls --all` |
| ... filtrés par statut | `jira ls --status "In Progress"` (plusieurs : `"To Do,In Review"`) |
| ... plus vieux que 3 mois | `jira ls --since all` (ou `30d`, `12w`, `24h`) |
| Recherche JQL libre | `jira search "project = INFRA AND status = 'In Progress'"` (`--json`) |
| Détail d'un ticket | `jira show PROJ-123` (`--comments N`, défaut 3, `0` pour aucun ; affiche aussi le contexte de l'épic parent et l'historique) |
| Créer un ticket (interactif) | `jira create` (pas à pas ; voir note ci-dessous) |
| Créer un ticket (script) | `jira create --epic KEY --title T [--description D] [--description-file F] [--points N] [--perimeter P]` |
| Voir les transitions possibles | `jira mv PROJ-123` (sans argument statut) |
| Changer le statut | `jira mv PROJ-123 "In Progress"` |
| Ajouter un commentaire | `jira comment PROJ-123 "texte"` (sans texte : lit stdin, ex. `echo "..." \| jira comment PROJ-123`) |
| Modifier un commentaire | `jira comment PROJ-123 --edit <id> "texte"` (id affiché par `jira show`) |
| Supprimer un commentaire | `jira comment PROJ-123 --delete <id>` |
| (Ré)assigner un ticket | `jira assign PROJ-123 jdupont` (`me` : soi-même ; sans user : désassigne) |
| Modifier un champ | `jira edit PROJ-123 --title "..."` (`--description`, `--assignee`, `--labels`, `--priority`) |
| Lister (JSON pour script) | `jira ls --json` (ou `jira ls --status "..." --json`) |
| Détail JSON d'un ticket | `jira show PROJ-123 --json` |
| Saisir du temps (Tempo) | `jira tempo log PROJ-123 2h` (durée : `2h`, `90m`, `1h30`, `0.5h` ; `--date YYYY-MM-DD`, défaut aujourd'hui ; `--comment "…"` ; `--account ACC` optionnel) |
| Récap du temps du mois | `jira tempo month` (`--month YYYY-MM`, défaut mois courant ; `--json`) |
| Lister les comptes Tempo | `jira tempo accounts` (`--all` inclut fermés/archivés ; `--json`) |
| Afficher une page Confluence | `jira confluence <URL\|pageId>` (URL complète, lien court `/x/…`, ou pageId numérique) |

## Comportements à connaître

- **`jira ls` ne montre par défaut que les tickets mis à jour depuis moins de 90 jours** et non résolus. Si l'utilisateur cherche un ticket absent de la liste, réessayer avec `--since all` avant de conclure qu'il n'existe pas.
- Pour changer un statut, si le nom exact de la transition est incertain, lancer d'abord `jira mv KEY` pour lister les transitions, puis appliquer. Le matching est insensible à la casse et accepte le nom de la transition ou du statut cible.
- Changer un statut ou ajouter un commentaire sont des actions mutatives : confirmer avec l'utilisateur si la demande est ambiguë (plusieurs tickets candidats, transition incertaine, texte du commentaire à rédiger soi-même).
- **`jira create`** a deux modes. **Interactif** (sans flag) : lit sur stdin, à faire lancer par l'utilisateur (`! jira create`) — il enchaîne Epic Link (`<epic-link-field>`, clé d'épic — le projet en est déduit), titre, description (multi-ligne, ligne vide pour finir), story points (`<story-points-field>`, optionnel). **Non-interactif** (dès qu'un `--epic` est passé) : `jira create --epic KEY --title T [--description D] [--description-file F] [--points N] [--perimeter P]` — lançable directement (aucun stdin requis, sauf `--description-file -`). `--epic` et `--title` obligatoires ; `\n` interprétés dans `--description`, `--description-file -` lit la description sur stdin. Les champs et valeurs par défaut propres à l'instance doivent venir de la configuration locale. Créer un ticket est une action mutative : confirmer les valeurs (surtout Epic Link) avant de lancer.
- **Universe Perimeter hérité de l'épic** : le champ `<perimeter-field>` n'est plus demandé — il est **récupéré depuis l'épic lié** (`--epic`) et recopié tel quel sur le ticket créé. `--perimeter P` reste disponible pour **forcer** un univers autorisé par l'instance. Si l'épic n'a pas d'univers renseigné : le mode interactif le demande, le mode non-interactif renvoie une erreur invitant à passer `--perimeter`.
- **`jira show`** enrichit l'affichage avec l'épic parent (champ *Epic Link*, `<epic-link-field>`) : clé/résumé/statut de l'épic dans les métadonnées et sa description en section « Contexte épic ». Utile pour comprendre le cadre d'un ticket sans lancer un second `jira show` sur l'épic. Si l'épic est inaccessible, un avertissement stderr est émis sans bloquer. `jira show` affiche aussi l'**historique** des modifications (section « Historique ») et l'**ID de chaque commentaire** (`#<id>`), à réutiliser avec `jira comment --edit/--delete`.
- **`jira search`** prend une requête JQL brute et affiche le même tableau que `jira ls`. À privilégier dès que le besoin sort des filtres de `ls` (par projet, label, sprint, rapporteur…). Attention aux guillemets shell : mettre le JQL entre guillemets doubles et les valeurs entre guillemets simples (ex. `"status = 'In Progress'"`).
- **`jira assign`** est une action mutative : `me`/`@me` = utilisateur courant, sans argument = désassignation. Confirmer la cible avant de lancer si la demande est ambiguë.
- **`jira comment --edit/--delete`** sont des actions mutatives sur un commentaire existant, identifié par son ID (obtenu via `jira show`). `--delete` supprime définitivement : confirmer avant de lancer.
- **`jira edit`** modifie uniquement les champs dont le flag est passé (`--title`, `--description`, `--assignee`, `--labels`, `--priority`). C'est une action mutative : confirmer avec l'utilisateur avant de lancer, surtout pour `--assignee` et `--description`. `--labels` remplace la liste complète.
- **`--json`** sur `ls` et `show` produit une sortie JSON structurée, utile pour le scripting et l'intégration. `jira ls --json` retourne un tableau d'issues, `jira show KEY --json` retourne le détail complet.
- **`jira tempo`** pilote Tempo Timesheets (plugin Jira Server/DC, servi par la même instance, même token). Trois sous-commandes : `tempo log` (saisie mutative), `tempo month` (lecture) et `tempo accounts` (listing). Voir la section Tempo ci-dessous.
- **`jira confluence`** affiche titre, espace, date de modification, lien et contenu texte d'une page Confluence (voir section Confluence ci-dessous). Prérequis : Confluence doit être configuré via `jira init`.
- En cas de doute sur la syntaxe, `jira help` (ou `jira --help`) affiche l'aide complète.
- Pour vérifier la version installée : `jira --version` (affiche `jira <tag>` ou `jira dev` pour un build sans tag).
- Pour générer un script de complétion shell : `jira completion <bash|zsh|fish>` (statique : sous-commandes + flags, pas de clés Jira).
- Erreur 401 ou "configuration introuvable" → demander à l'utilisateur de lancer `jira init` dans son terminal (config : `<jira-config-path>`).
- Après modification du code source, réinstaller avec `make install` (ou `go install .`) depuis `<jira-source-root>`.

### Workflow de création guidée par l'assistant

Quand l'utilisateur demande de créer une jira, **collecter les informations suivantes**. Repérer d'abord celles déjà présentes dans le prompt initial, puis **demander une par une, au fur et à mesure, uniquement celles qui manquent** (ne pas redemander ce qui est déjà fourni) :

1. **epic** — clé de l'épic (→ `--epic`) — *obligatoire*
2. **title** — titre du ticket (→ `--title`) — *obligatoire*
3. **description** (→ `--description` ou `--description-file`) — *obligatoire*
4. **sizing** — story points (→ `--points`) — *facultatif* ; ne pas bloquer si l'utilisateur ne le fournit pas.

**Ne pas demander le perimeter** : l'Universe Perimeter est hérité automatiquement de l'épic. Ne passer `--perimeter` que si l'utilisateur veut explicitement forcer un univers différent de celui de l'épic (valeurs : baremetal, kms, public cloud, domain, vps, telephony, vmware, nutanix, core).

Une fois les informations réunies, **toujours afficher un récapitulatif de la jira** (epic, title, description, sizing) et attendre la confirmation de l'utilisateur **avant** de lancer `jira create` (mode non-interactif : `jira create --epic KEY --title T --description D [--points N]`).

### Tempo (saisie de temps)

`jira tempo` s'appuie sur l'API Tempo Timesheets v4 (`/rest/tempo-timesheets/4/…`), servie par la même instance Jira Server/DC et authentifiée par le même Personal Access Token — aucune config supplémentaire.

- **`jira tempo log <KEY> <durée> [--date YYYY-MM-DD] [--comment "…"] [--account ACC]`** saisit un worklog.
  - `KEY` et `durée` sont **positionnels** (avant les flags).
  - Durées acceptées : `2h`, `90m`, `1h30`, `1h30m`, `0.5h`, `1.5h`, `7h` (unité `h` ou `m` obligatoire).
  - `--account` est **optionnel** : sur les instances où le compte est dérivé de l'issue (attributs de worklog vides côté API), il est inutile. Il reste disponible pour forcer un attribut compte quand l'instance en pose un. Pour connaître les clés de compte disponibles : `jira tempo accounts`.
  - L'auteur (`worker`) est déduit de l'utilisateur courant (clé technique Jira) ; la clé d'issue est résolue en id interne (`originTaskId`) ; si un compte est fourni, l'id de l'attribut est découvert dynamiquement via `/work-attributes`.
  - Date par défaut : aujourd'hui.
  - C'est une **action mutative** : confirmer issue / durée / date avant de lancer si la demande est ambiguë.
- **`jira tempo month [--month YYYY-MM] [--json]`** affiche le récap des saisies du mois : une ligne par worklog (jour, issue, durée, commentaire), le total global et les totaux par issue. Mois par défaut : mois courant.
- **`jira tempo accounts [--all] [--json]`** liste les comptes Tempo configurés sur l'instance. Par défaut seuls les comptes ouverts (OPEN) sont affichés ; `--all` inclut les fermés et archivés. La clé affichée est la valeur à passer à `--account`.

Exemple `jira tempo month` :

```
Juillet 2026 — total 21h30

  mar 01/07  PROJ-101      7h00  Migration endpoints
  mer 02/07  PROJ-101      7h00  Migration endpoints
  jeu 03/07  PROJ-98       7h30  Rate limiting

Par issue : PROJ-101 14h00 · PROJ-98 7h30
```

### Confluence

`jira confluence` accepte 3 formats de référence :
- **URL complète** : `https://confluence.example.com/display/DEV/Ma+Page`
- **Lien court** : `/x/abc123`
- **pageId numérique** : `123456789`

La commande affiche : titre, espace, date de dernière modification, lien web et contenu texte de la page. Les liens courts sont suivis automatiquement (jusqu'à 3 redirections).

Prérequis : l'URL et le token Confluence doivent être configurés via `jira init`. Si Confluence n'est pas configuré, la commande renvoie une erreur explicite.

### Exemples de sortie

`jira ls` :

```
KEY          STATUT        RÉSUMÉ
PROJ-101     In Progress   Migrer les endpoints v1 vers v2
PROJ-98      To Do         Ajouter le rate limiting sur /api/search
PROJ-95      In Review     Corriger le timeout sur le webhook Stripe

3 issue(s)
```

`jira show PROJ-101` :

```
PROJ-101  Migrer les endpoints v1 vers v2
──────────────────────────────────────────
Type :        Task
Statut :      In Progress
Priorité :    Medium
Assigné à :   Jean Dupont
Épic :        PROJ-50  Migration API v2  [In Progress]
Créée :       2026-06-15 10:30
Mise à jour : 2026-07-08 14:22
Lien :        https://jira.example.com/browse/PROJ-101

Contexte épic (PROJ-50) :
  Migration progressive de tous les endpoints REST de v1 vers v2,
  avec rétrocompatibilité maintenue pendant 3 mois.

Description :
  Reprendre les 12 endpoints sous /api/v1/ et créer leurs équivalents
  sous /api/v2/ avec le nouveau format de réponse.

Commentaires (1 dernier(s) sur 3) :

  [2026-07-08 14:22] Marie Martin (#45678)
  Les 4 premiers endpoints sont mergés, reste /users et /billing.

Historique :

  [2026-07-08 14:22] Marie Martin
    status : "To Do" → "In Progress"
    assignee : "" → "Jean Dupont"
```
