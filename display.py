import os

import cv2
import numpy as np

from block_matching import compute_search_area

RED = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (0, 255, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

LINE_THICKNESS = 1
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.5
TEXT_THICKNESS = 1
LABEL_ORIGIN = (6, 18)
LABEL_LINE_HEIGHT = 20

BLOCK_VIEW_TARGET_HEIGHT = 240
SEPARATOR_WIDTH = 10
DIFFERENCE_GAIN = 4


def to_bgr(image):
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    return image.copy()

def draw_rect(image, rect, color):
    x1, y1, x2, y2 = rect
    cv2.rectangle(image, (x1, y1), (x2, y2), color, LINE_THICKNESS)


def put_label(image, text, line=0):
    x, y = LABEL_ORIGIN
    origin = (x, y + line * LABEL_LINE_HEIGHT)
    cv2.putText(image, text, origin, FONT, FONT_SCALE, BLACK, TEXT_THICKNESS + 2)
    cv2.putText(image, text, origin, FONT, FONT_SCALE, WHITE, TEXT_THICKNESS)

# Fabrique l'image finale
def build_result_view(frame1, frame2, rect, result, margin):
    left = to_bgr(frame1)
    right = to_bgr(frame2)

    draw_rect(left, rect, RED)
    draw_rect(right, compute_search_area(rect, margin, frame2.shape), GREEN)
    draw_rect(right, rect, RED)
    draw_rect(right, result.matched_rect, YELLOW)

    put_label(left, "Frame 1 - reference block (red)")
    put_label(right, "Frame 2 - search area (green), best match (yellow)")
    put_label(right, f"dx={result.dx}  dy={result.dy}  MSE={result.mse:.2f}", line=1)

    return np.hstack([left, right])


# agrandit un petit bloc
def enlarge(block, scale):
    return cv2.resize(block, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)


# fabrique l'image avec 3 blocs (reference, meilleur match, difference)
def build_blocks_view(reference_block, matched_block, difference):
    amplified = np.clip(difference.astype(np.int32) * DIFFERENCE_GAIN, 0, 255).astype(np.uint8)
    scale = max(1, BLOCK_VIEW_TARGET_HEIGHT // reference_block.shape[0])
    height = reference_block.shape[0] * scale
    separator = np.full((height, SEPARATOR_WIDTH), 255, dtype=np.uint8)

    parts = []
    for block in (reference_block, matched_block, amplified):
        parts.append(enlarge(block, scale))
        parts.append(separator)
    return np.hstack(parts[:-1])


# verifie si la fenetre est encore ouverte (False si on a clique sur la croix)
def is_window_open(window_name):
    try:
        return cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) >= 1
    except cv2.error:
        return False


def show(window_name, image):
    cv2.imshow(window_name, image)


def save_image(path, image):
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    cv2.imwrite(path, image)



# rendre le residu affichable avec une normalisation min-max
def build_residual_view(residual):
    return cv2.normalize(residual, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)