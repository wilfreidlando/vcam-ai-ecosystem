---
name: session-courte
description: La discipline de consommation — pourquoi une session longue coûte cher, et les cinq gestes qui changent la facture. À activer au début d'une session, ou quand la barre d'état dépasse 50 % de contexte.
metadata:
  origin: vcam-ecosystem
---

# La session courte

## Le fait, en une phrase

À chaque tour de modèle, **toute la conversation est renvoyée**. Le coût d'une
session n'est donc pas `ce que je fais`, mais `nombre de tours × taille du
contexte`. Mesuré sur une session réelle : 2 272 tours, 200,9 k de contexte
moyen, **99,2 % de relecture**, et **0,8 %** d'écriture. Le travail utile
était la partie la plus petite de la facture.

## Les cinq gestes, par rendement décroissant

1. **`/clear` entre deux tâches sans lien.** C'est **gratuit** — contrairement
   à `/compact`, qui relit toute la conversation pour la résumer. Une session
   qui passe de 250 k à 10 k divise le coût de tous les tours suivants.
2. **Une session = un chantier.** Quatre chantiers dans une session, c'est
   quatre chantiers qui se paient mutuellement en contexte.
3. **Des sorties d'outils petites.** Ce qui entre dans le contexte est
   renvoyé à chaque tour. Cent kilo-octets de journal de tests, c'est cent
   kilo-octets × tous les tours. Tronque, résume, sous-agent.
4. **Un sous-agent qui rend un résumé.** Il lit dans son propre contexte et
   rend dix lignes ; tu ne paies que dix lignes. Un sous-agent qui rend sa
   sortie brute paie deux fois.
5. **Le bon modèle, le bon effort.** L'effort est facturé comme de la sortie :
   `max` sur une tâche mécanique est du gaspillage. Mais c'est le **dernier**
   levier : le contexte coûte plus cher que le modèle.

## Ce qui ne marche pas

- **Compter les jetons à la fin.** La mesure sert à décider la prochaine
  session, pas à se sentir coupable de la dernière.
- **Sonder pendant une attente.** Chaque sondage est un tour qui renvoie tout
  le contexte. Utilise une commande en arrière-plan, et laisse la notification
  te réveiller.
- **Relancer la suite complète quatre fois.** Une fois, à la fin, sur l'état
  final. Si une porte échoue, relance **celle-là**.
- **Une session qui commence par « reprends ce qu'on faisait »** : ce que la
  session précédente a coûté ne vient pas avec elle — il faut le réécrire
  (c'est à ça que sert `/handoff`).

## La règle du moment

Quand la barre d'état franchit **60 %**, la session a déjà payé deux fois ce
qu'elle aurait coûté. À ce moment-là, `/clear` — et le contexte se trouve
dans le prompt de relève, dans le commit, ou dans la tête du commanditaire,
pas dans 200 kilo-octets re-relus à chaque tour.
