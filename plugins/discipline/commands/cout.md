---
description: Où sont partis mes jetons — le rapport de consommation, expliqué
---

# /cout — où sont partis mes jetons

Tu demandes le rapport de consommation. Tu fais **exactement** ceci :

1. Lance `ctx-cost --day $(date +%F)` (et `ctx-cost --top 12` si le jour n'a
   rien, pour voir les sessions voisines).
2. Si la commande n'existe pas (outil non installé), dis-le en une ligne et
   donne la commande d'installation : `~/.local/bin/ctx-cost`.
3. **Explique** le rapport en trois lignes maximum, avec le diagnostic :
   - combien de tours, quel contexte moyen par tour ;
   - la part de relecture, et ce que ça dit (si elle dépasse 80 %, le coût
     est le transport de la conversation, pas le travail) ;
   - **une** action concrète pour la prochaine session.

Ne reproduis pas le tableau en entier : il est déjà à l'écran. Ne moralise
pas. Le but est de **décider**, pas de se sentir coupable.

Si l'utilisateur demande pourquoi, explique le mécanisme : à chaque tour,
toute la conversation est renvoyée au modèle ; le coût est donc
`nombre de tours × contexte moyen`, et le contexte moyen croît avec la
longueur de la session. C'est pour cela que `/clear` entre deux tâches est
le geste le plus rentable, et qu'une session = un chantier.
