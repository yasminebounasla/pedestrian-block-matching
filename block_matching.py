from dataclasses import dataclass

import cv2
import numpy as np

SEARCH_MARGIN = 5 
BLOCK_SIZE = 16


@dataclass(frozen=True)
class MatchResult:
    dx: int
    dy: int
    mse: float
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

# moyenne des differences au carre 
def compute_mse(block_a, block_b):
    difference = block_a.astype(np.int32) - block_b.astype(np.int32)
    return float(np.mean(difference ** 2))


# fabrique l'image de difference 
def compute_difference_image(block_a, block_b):
    difference = block_a.astype(np.int32) - block_b.astype(np.int32) 
    return np.abs(difference).astype(np.uint8) 


# verifier que le rectangle vert ne sort pas de l'image 
def is_inside_image(rect, image_shape):
    x1, y1, x2, y2 = rect
    height, width = image_shape[:2]
    return x1 >= 0 and y1 >= 0 and x2 <= width and y2 <= height



# trouver le bloc avec le moins de difference
def find_best_match(reference_image, next_image, rect, margin=SEARCH_MARGIN):
    # passer les deux images en luminance (niveaux de gris)
    reference_luma = to_luminance(reference_image)
    next_luma = to_luminance(next_image)

    # on decoupe le bloc rouge dans l'image entiere
    x1, y1, x2, y2 = rect
    reference_block = reference_luma[y1:y2, x1:x2]
    block_height, block_width = reference_block.shape

    # initialisation
    best_dx, best_dy = 0, 0
    best_mse = None
    best_block = None

    # la recherche : 121 (de -5 a +5 en x et en y)
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

            # decouper le candidat et le comparer a la reference
            cx1, cy1, cx2, cy2 = candidate_rect
            candidate_block = next_luma[cy1:cy2, cx1:cx2]
            mse = compute_mse(reference_block, candidate_block)

            # garder le candidat avec la plus petite MSE
            if best_mse is None or mse < best_mse:
                best_mse, best_dx, best_dy = mse, dx, dy
                best_block = candidate_block

    if best_mse is None:
        raise ValueError("No candidate position fits inside the image.")

    matched_rect = (
        x1 + best_dx,
        y1 + best_dy,
        x1 + best_dx + block_width,
        y1 + best_dy + block_height,
    )

    # difference moyenne en luminance (en valeur absolue)
    difference = reference_block.astype(np.int32) - best_block.astype(np.int32)
    mean_difference = float(np.mean(np.abs(difference)))

    return MatchResult(best_dx, best_dy, best_mse, mean_difference, matched_rect)





# appliquer le block matching sur tous les blocs de frame 2
def match_all_blocks(frame1, frame2, block_size=BLOCK_SIZE, margin=SEARCH_MARGIN):

    # charger les 2 frames
    luma1 = to_luminance(frame1)
    luma2 = to_luminance(frame2)
    height, width = luma2.shape

    # garder seulement les blocs  (pour parcourire les blocks de frame 2)
    usable_height = height - height % block_size
    usable_width = width - width % block_size

    # initialiser le residu a '0'
    residual = np.zeros((usable_height, usable_width), dtype=np.int16)  # int16 car le residu peut etre negatif
    matches = []

    # parcourir tous les blocks de l'image
    for y in range(0, usable_height, block_size):
        for x in range(0, usable_width, block_size):
            rect = (x, y, x + block_size, y + block_size)

            # le bloc vient de frame 2, on cherche best match dans frame 1 ( dans le margin seulement )
            result = find_best_match(luma2, luma1, rect, margin)
            mx1, my1, mx2, my2 = result.matched_rect

            current_block = luma2[y:y + block_size, x:x + block_size].astype(np.int16)
            matched_block = luma1[my1:my2, mx1:mx2].astype(np.int16)

            # placer le residu a la position du bloc
            residual[y:y + block_size, x:x + block_size] = current_block - matched_block
            matches.append((rect, result))

    return residual, matches