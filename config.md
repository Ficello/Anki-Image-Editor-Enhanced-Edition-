# Configuration — Image Editor Enhanced (Éditeur d'images médicales)

Ce module fournit des outils intégrés d'annotation, de recadrage, de floutage, de caviardage et de retouche d'illustrations médicales et anatomiques dans l'éditeur Anki.

## Paramètres de configuration

- `replace_all` (booléen, défaut : `false`) :
  Définit le comportement par défaut de la case à cocher « Remplacer sur toutes les cartes identiques » lors de l'enregistrement d'une image modifiée.
  - `false` : enregistre une copie éditée spécifique sans altérer les autres cartes utilisant l'image originale.
  - `true` : remplace toutes les occurrences de l'image source dans l'ensemble de la collection Anki.

- `default_ratio` (chaîne, défaut : `"free"`) :
  Format de découpe sélectionné par défaut à l'ouverture de l'outil de recadrage.
  - Valeurs admissibles : `"free"` (Libre), `"1:1"` (Carré), `"4:3"`, `"16:9"`, `"3:2"`.

- `export_quality` (entier, défaut : `95`) :
  Qualité de compression lors de l'exportation des images matricielles JPG ou WebP (de 50 à 100).

- `default_filter` (chaîne, défaut : `"none"`) :
  Filtre visuel appliqué par défaut à l'ouverture du recadreur.
  - Valeurs admissibles : `"none"` (Normal), `"invert"` (Négatif / Radiographie), `"high_contrast"` (Contraste renforcé), `"grayscale"` (Niveaux de gris).

- `shortcut_editor` (chaîne, défaut : `"Ctrl+Shift+I"`) :
  Raccourci clavier principal dans l'éditeur de note pour ouvrir l'image sous le curseur ou créer un dessin vectoriel. Géré automatiquement par le gestionnaire de raccourcis (`Customize Keyboard Shortcuts Enhanced`).
