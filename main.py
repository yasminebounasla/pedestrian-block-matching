import argparse
import csv
import os

import cv2

import display
from block_matching import (
    SEARCH_MARGIN,
    compute_difference_image,
    find_best_match,
    to_luminance,
)
from selection import select_rectangle

RESULTS_DIR = "results"
RESULT_WINDOW = "Result: frame 1 vs frame 2"
BLOCKS_WINDOW = "Reference | Best match | Difference (x4)"
ESC_KEY = 27
NO_KEY = 255
KEY_POLL_DELAY_MS = 50
SUMMARY_HEADER = ["test", "x1", "y1", "x2", "y2", "dx", "dy", "mse", "mean_difference"]

# lit les farmes
def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Locate a pedestrian in the next video frame by block matching."
    )
    parser.add_argument("frame1", help="path to the first frame")
    parser.add_argument("frame2", help="path to the next frame")
    parser.add_argument(
        "--margin",
        type=int,
        default=SEARCH_MARGIN,
        help="search margin in pixels (default: %(default)s)",
    )
    return parser.parse_args()



def load_image(path):
    image = cv2.imread(path)
    if image is None:
        raise SystemExit(f"Cannot read image: {path}")
    return image


# attend une touche ; si on ferme une fenetre avec la croix, on fait comme ESC
def wait_for_user(window_names):
    while True:
        key = cv2.waitKey(KEY_POLL_DELAY_MS) & 0xFF
        if key != NO_KEY:
            return key
        if not all(display.is_window_open(name) for name in window_names):
            return ESC_KEY


def analyse(frame1, frame2, rect, margin):
    result = find_best_match(frame1, frame2, rect, margin) # find the best block  

    # afficher les resultat
    luma1 = to_luminance(frame1)
    luma2 = to_luminance(frame2)
    x1, y1, x2, y2 = rect
    mx1, my1, mx2, my2 = result.matched_rect
    reference_block = luma1[y1:y2, x1:x2]
    matched_block = luma2[my1:my2, mx1:mx2]
    difference = compute_difference_image(reference_block, matched_block)

    result_view = display.build_result_view(frame1, frame2, rect, result, margin)
    blocks_view = display.build_blocks_view(reference_block, matched_block, difference)
    return result, result_view, blocks_view


def build_record(index, rect, result):
    return {
        "test": index,
        "x1": rect[0],
        "y1": rect[1],
        "x2": rect[2],
        "y2": rect[3],
        "dx": result.dx,
        "dy": result.dy,
        "mse": round(result.mse, 3),
        "mean_difference": round(result.mean_difference, 3),
    }


# print le tableau récapitulatif
def print_summary(records):
    print()
    print(f"{'Test':>4}  {'Rectangle (x1, y1, x2, y2)':<28}{'(dx, dy)':<10}{'MSE':>10}{'Mean diff':>12}")
    for r in records:
        rectangle = f"({r['x1']}, {r['y1']}, {r['x2']}, {r['y2']})"
        shift = f"({r['dx']}, {r['dy']})"
        print(f"{r['test']:>4}  {rectangle:<28}{shift:<10}{r['mse']:>10}{r['mean_difference']:>12}")


def save_summary(records):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, "summary.csv")
    with open(path, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=SUMMARY_HEADER)
        writer.writeheader()
        writer.writerows(records)
    print(f"\nSummary saved to {path}")


def main():
    args = parse_arguments()
    frame1 = load_image(args.frame1)
    frame2 = load_image(args.frame2)
    if frame1.shape != frame2.shape:
        raise SystemExit("The two frames must have the same size.")

    records = []
    index = 1
    while True:
        print(f"Test {index}: drag a rectangle around the pedestrian (ESC to cancel).")
        rect = select_rectangle(frame1)
        if rect is None:
            break

        result, result_view, blocks_view = analyse(frame1, frame2, rect, args.margin)
        records.append(build_record(index, rect, result))

        display.save_image(os.path.join(RESULTS_DIR, f"test_{index:02d}_result.png"), result_view)
        display.save_image(os.path.join(RESULTS_DIR, f"test_{index:02d}_blocks.png"), blocks_view)
        display.show(RESULT_WINDOW, result_view)
        display.show(BLOCKS_WINDOW, blocks_view)

        print("Press any key for another test, ESC or close a window to quit.")
        key = wait_for_user([RESULT_WINDOW, BLOCKS_WINDOW])
        cv2.destroyAllWindows()
        if key == ESC_KEY:
            break
        index += 1

    cv2.destroyAllWindows()
    if records:
        print_summary(records)
        save_summary(records)


if __name__ == "__main__":
    main()