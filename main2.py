import argparse
import os

import cv2
import numpy as np

import display
from block_matching import match_all_blocks
from main import load_image, wait_for_user

RESULTS_DIR = "results_tp6"
RESIDUAL_WINDOW = "TP6 - Residual image"


def main():
    parser = argparse.ArgumentParser(description="Block matching on all 16x16 blocks.")
    parser.add_argument("frame1", help="path to the first frame (reference)")
    parser.add_argument("frame2", help="path to the next frame")
    args = parser.parse_args()

    frame1 = load_image(args.frame1)
    frame2 = load_image(args.frame2)
    if frame1.shape != frame2.shape:
        raise SystemExit("The two frames must have the same size.")

    print("Block matching in progress...")
    residual, matches = match_all_blocks(frame1, frame2)

    mean_mse = np.mean([result.mse for _, result in matches])
    print(f"Number of blocks : {len(matches)}")
    print(f"Average MSE      : {mean_mse:.2f}")

    residual_view = display.build_residual_view(residual)
    path = os.path.join(RESULTS_DIR, "residual.png")
    display.save_image(path, residual_view)
    print(f"Residual image saved to {path}")

    display.show(RESIDUAL_WINDOW, residual_view)
    wait_for_user([RESIDUAL_WINDOW])
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()