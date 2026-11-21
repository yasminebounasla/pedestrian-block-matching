from dataclasses import dataclass

import cv2
import numpy as np

SEARCH_MARGIN = 5 # le rectangle vert 


@dataclass(frozen=True)
class MatchResult:
    dx: int
    dy: int
    sad: int
    mean_difference: float
    matched_rect: tuple


# transfomation l'image vers un niveau de gris
def to_luminance(image):
    if image.ndim == 2:  # (hauteur, largeur) = 2 , RGB : (hauteur, largeur, 3) = 3
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


# calcule de rectangle vert
def compute_search_area(rect, margin, image_shape):
    x1, y1, x2, y2 = rect
    height, width = image_shape[:2]
    return (
        max(x1 - margin, 0),
        max(y1 - margin, 0),
        min(x2 + margin, width),
        min(y2 + margin, height),
    )

# mesure la difference entre deux blocs ( Petit = ils se ressemblent )
def compute_sad(block_a, block_b):
    difference = block_a.astype(np.int32) - block_b.astype(np.int32)
    return int(np.abs(difference).sum())


# fabrique l'image de difference 
def compute_difference_image(block_a, block_b):
    difference = block_a.astype(np.int32) - block_b.astype(np.int32) 
    return np.abs(difference).astype(np.uint8) 


# verifier que le rectangle vert ne sort pas de l'image 
def is_inside_image(rect, image_shape):
    x1, y1, x2, y2 = rect
    height, width = image_shape[:2]
    return x1 >= 0 and y1 >= 0 and x2 <= width and y2 <= height


# tourver le bloc avec le mois de diff 
def find_best_match(reference_image, next_image, rect, margin=SEARCH_MARGIN):
    # passer les deux images en luminance (niveaux de gris)
    reference_luma = to_luminance(reference_image)
    next_luma = to_luminance(next_image)

    # On decoupe le bloc rouge dans l'image entiere
    x1, y1, x2, y2 = rect
    reference_block = reference_luma[y1:y2, x1:x2]
    block_height, block_width = reference_block.shape

    # initialisation 
    best_dx, best_dy = 0, 0  
    best_sad = None

    # elle va etre executer 121 fois (-5, -4, .. ,0 , .. , 4, 5)
    for dy in range(-margin, margin + 1):
        for dx in range(-margin, margin + 1):
            candidate_rect = (
                x1 + dx,
                y1 + dy,
                x1 + dx + block_width,
                y1 + dy + block_height,
            )

            # ignorer si on sort de l'image
            if not is_inside_image(candidate_rect, next_luma.shape):
                continue

            # decouper le candidat dans frame 2 et le comparer a la reference
            cx1, cy1, cx2, cy2 = candidate_rect
            candidate_block = next_luma[cy1:cy2, cx1:cx2]
            sad = compute_sad(reference_block, candidate_block)

            # garder le candidat avec le plus petit SAD 
            if best_sad is None or sad < best_sad:
                best_sad, best_dx, best_dy = sad, dx, dy  # (dx, dy) represnete le vecteur du mouvement 

    if best_sad is None:
        raise ValueError("No candidate position fits inside the image.")

    # le resultat ( le mouvement )
    matched_rect = (
        x1 + best_dx, # haut-gauche
        y1 + best_dy,
        x1 + best_dx + block_width,  # bas-droit ( c'est le mm avec : haut-gauche + width )
        y1 + best_dy + block_height,
    )
    mean_difference = best_sad / reference_block.size
    return MatchResult(best_dx, best_dy, best_sad, mean_difference, matched_rect)