---
description: Clore une session proprement — les portes, le commit, la mesure, et le moment de /clear
---

# /fin — clore la session

Tu termines une tâche. Ce que tu fais, dans cet ordre, **sans rien demander** :

## 1. Les portes

Exécute les portes du projet. Sur un dépôt qui a un `Makefile` avec une cible
`ci`, une cible `arch` ou `stan`, ce sont elles. Sinon, les équivalents
lisibles : le formateur, l'analyseur statique, le contrôle des couches, la
suite de tests.

**Une seule fois.** Tu ne relances pas la suite complète après chaque
correction : tu la lances à la fin, sur l'état final. Si une porte échoue,
tu corriges, tu **relances seulement celle qui a échoué**.

Si le projet a une base de test partagée, utilise une base privée et
jamais deux suites en parallèle.

## 2. L'état du dépôt

`git status` puis `git diff --stat`. Si des fichiers de test (bases SQLite,
`*_test_*`) traînent, **ne les commite pas** : ajoute-les au `.gitignore`.

## 3. Le commit

Un seul commit, message en français, sujet de la forme
`feat(« module ») : ce que ça change` et un corps qui explique **ce qui a
été fait**, **les portes passées avec leurs chiffres**, et **ce qui reste à
décider**. Pas de rapport d'états des lieux : le commit est la livraison.

Si l'utilisateur a demandé de pousser, pousse sur la branche de travail.

## 4. La mesure

Lance `ctx-cost --day $(date +%F)` et **résume en deux lignes** : combien de
tours, quel contexte moyen, quelle part de relecture. Si la part de
relecture dépasse 80 %, dis-le : la prochaine session gagnera à être courte.

## 5. Le passage de relais

Dis exactement ceci, et rien de plus :

> Session close. La mesure est ci-dessus. **Tape `/clear`** avant la
> prochaine tâche : `/clear` est gratuit, `/compact` coûte une grosse
> requête, et ta session prochaine repartira avec 10 k au lieu de 200 k.

Si la tâche n'est pas terminée, dis ce qui reste (en trois lignes maximum)
et propose `/handoff` pour écrire le prompt de relève.
