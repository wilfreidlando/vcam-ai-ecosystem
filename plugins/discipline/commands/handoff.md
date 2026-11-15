---
description: Écrire le prompt de relève pour la session suivante — sans que rien ne soit redit
---

# /handoff — la relève

Tu termines une tâche **inachevée**, ou tu changes de chantier. Tu écris le
prompt que la session suivante recevra, pour qu'elle n'ait **rien** à
demander.

## Ce que tu fais

1. **Le dépôt** : `git log --oneline -5`, `git status`, `git diff --stat`.
2. **L'état réel** : qu'est-ce qui marche, qu'est-ce qui ne marche pas, quelle
   est la prochaine étape **concrète** (un fichier, une fonction, une porte).
3. **Le décor** : les règles du projet qui ne se devinent pas en lisant le
   code (les garde-fous, les permissions, les interdits).
4. **La structure** : où sont les dépôts, comment on teste, comment on
   déploie.

## Ce que tu écris

Un fichier `PROMPT-SESSION-<AAAAMMJJ>.md` **à la racine du workspace**
(le dossier qui contient les dépôts), et tu l'affiches dans ta réponse
finale, **entre deux marqueurs** pour que l'utilisateur puisse le copier
d'un clic.

Le format est celui de `PROMPT-SESSION-VCAM.md` s'il existe déjà dans le
workspace : garde-le, et remplace son contenu. Sinon, reprends cette
structure :

```markdown
# Prompt — <titre de la tâche>

## MA TÂCHE
<deux ou trois phrases : ce qu'il faut faire, précisément>

## Où l'on travaille
<les dépôts, leurs chemins, la branche, l'état (dernier commit)>

## Ce qui est déjà fait
<le travail de cette session, avec les portes passées>

## Ce qui reste
<la prochaine étape, concrète : un fichier, une fonction, un test>

## Les règles à ne pas oublier
<les garde-fous du projet, les interdits, les ports de test>

## Vérification
<les commandes exactes, et le résultat attendu>
```

## La règle qui compte

**Le prompt se suffit à lui-même.** La session suivante n'a pas le contexte
de celle-ci : elle ne sait ni ce qui a été essayé, ni ce qui a échoué, ni
pourquoi la décision a été prise. Tout ce qui n'est pas écrit ici sera
redécouvert — c'est-à-dire payé en jetons.

Termine par ceci, et rien de plus :

> Prompt écrit dans `PROMPT-SESSION-<date>.md`. Colle-le dans la session
> suivante, puis tape `/clear` ici : la suite est ailleurs.
