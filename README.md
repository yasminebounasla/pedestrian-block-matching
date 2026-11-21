# pedestrian-block-matching

Suivi d'un piéton entre deux images consécutives d'une séquence vidéo par **block matching** sur la composante luminance.

C'est le principe de l'**estimation de mouvement** utilisée par les codecs vidéo : au lieu de recoder le piéton dans chaque image, on code son déplacement (le vecteur de mouvement) et la petite différence résiduelle, qui se compresse très bien.

## Principe

1. L'utilisateur trace à la souris un rectangle autour du piéton dans la première image : c'est le **bloc de référence** (rouge).
2. Dans la seconde image, la **zone de recherche** (verte) est le rectangle de référence agrandi d'une marge de `N` pixels de chaque côté.
3. Le bloc de référence est comparé à tous les blocs candidats de même taille, décalés d'un pixel à la fois : `(2N + 1)²` positions (121 pour `N = 5`).
4. La comparaison se fait sur la **luminance** `Y = 0.299 R + 0.587 G + 0.114 B`, avec la **SAD** (somme des différences absolues) :

   ```
   SAD = Σ |bloc_référence(i, j) − bloc_candidat(i, j)|
   ```

5. Le candidat de SAD minimale est la nouvelle position du piéton (jaune). Son décalage `(dx, dy)` est le **vecteur de mouvement**.
6. La **différence moyenne** `SAD / nombre de pixels` donne l'écart moyen de luminance par pixel (0 à 255) et permet de juger la qualité du match indépendamment de la taille du bloc.

Code couleur : **rouge** = bloc de référence, **vert** = zone de recherche, **jaune** = meilleur match.

## Structure

```
main.py             point d'entrée, boucle de tests et résumé
selection.py        sélection du rectangle à la souris (glisser-déposer)
block_matching.py   conversion en luminance, SAD, recherche du meilleur bloc
display.py          rectangles rouge/vert/jaune, vue des blocs, sauvegarde
data/               images d'entrée
results/            images de sortie et summary.csv
```

## Installation

```
pip install -r requirements.txt
```

## Utilisation

```
python main.py data/frame1.png data/frame2.png
```

Option : `--margin N` pour définir la marge de recherche en pixels (5 par défaut).

```
python main.py data/frame1.png data/frame2.png --margin 80
```

- Maintenir le clic gauche et faire glisser pour tracer le rectangle autour du piéton.
- Deux fenêtres s'affichent : le résultat sur les deux images, puis le bloc de référence, le meilleur bloc et leur différence (amplifiée ×4).
- Une touche quelconque lance un nouveau test sur une autre position ; `ESC` ou la fermeture d'une fenêtre quitte et affiche le tableau récapitulatif.
- Les images sont enregistrées dans `results/`, et le tableau dans `results/summary.csv`.

Les deux images doivent avoir la même taille.

## Résultats

| Test | Rectangle (x1, y1, x2, y2) | (dx, dy) | SAD | Différence moyenne |
|---|---|---|---|---|
| 1 | | | | |

## Choix des paramètres

- **Marge de recherche** : elle doit être supérieure au déplacement réel du piéton. Si le meilleur décalage tombe exactement sur la limite de la marge, c'est le signe que le mouvement la dépasse. Plus les images sont grandes ou espacées dans le temps, plus la marge doit l'être.
- **Rectangle serré** : le bloc doit contenir le piéton et le moins possible de fond. Le fond est fixe : s'il domine le bloc, il domine aussi la SAD et peut faire désigner une mauvaise position.
- **Images rapprochées** : des images consécutives de la vidéo donnent un petit déplacement et une pose quasi identique, donc une SAD faible au bon endroit.

## Limites

- La méthode suppose que tout le bloc se déplace de la même façon ; un changement de pose, d'échelle ou d'éclairage dégrade le résultat.
- La recherche est exhaustive : le nombre de candidats croît avec le carré de la marge.
- Seule la luminance est utilisée ; la couleur est ignorée.
- Les candidats qui sortent de l'image (piéton près du bord) sont ignorés.