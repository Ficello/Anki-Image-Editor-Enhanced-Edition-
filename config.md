# Configuration — Éditeur d'Images Avancé (Image Editor Enhanced)

Ce module fournit des outils d'annotation, de recadrage, de floutage et de retouche d'illustrations médicales directement intégrés dans l'éditeur Anki.

## Préférences internes (`_hidden`)

- `_hidden.replaceAll` (booléen) : mémorise le choix par défaut de la case à cocher « Remplacer partout » lors de la sauvegarde d'une image modifiée.
  - Si `true` : remplace toutes les occurrences de l'image source dans l'ensemble de la collection Anki.
  - Si `false` : enregistre une copie éditée spécifique sans altérer les autres cartes utilisant l'image originale.
