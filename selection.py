import cv2

WINDOW_NAME = "Select the pedestrian (hold left button and drag, ESC to cancel)"
RECT_COLOR = (0, 0, 255)
RECT_THICKNESS = 1
ESC_KEY = 27  
REFRESH_DELAY_MS = 20
CONFIRMATION_DELAY_MS = 500


# pour assurer que la souris rest tjr dans l'image
def clamp_point(point, image_shape):
    height, width = image_shape[:2]  
    x, y = point
    return min(max(x, 0), width), min(max(y, 0), height)  # si x négative il devien 0 , si x plsu de with en return width


# retourner les 4 coordonnees du rectangle
def normalize_corners(first_point, second_point):
    x1, y1 = first_point
    x2, y2 = second_point
    return min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2) # en haut-gauche c'est le plus petit , bas-droit c'est le plus garnde



# return l'image original avec le rectangle rouge
def draw_selection(image, start, end):
    canvas = image.copy()
    if start is not None:
        cv2.rectangle(canvas, start, end, RECT_COLOR, RECT_THICKNESS)
    return canvas


def select_rectangle(image):
    # etat initial : rien n'est encore selectionne
    selection = {"start": None, "end": None, "dragging": False, "done": False}

    # appelee par OpenCV à chaque action de la souris
    def on_mouse(event, x, y, flags, param):
        point = clamp_point((x, y), image.shape)  # garde la souris dans l'image

        # appui (on note le point de depart)
        if event == cv2.EVENT_LBUTTONDOWN:
            selection.update(start=point, end=point, dragging=True)

        # (bouton maintenu) on met a jour le point d'arrivage
        elif event == cv2.EVENT_MOUSEMOVE and selection["dragging"]:
            selection["end"] = point

        # ron termine la selection
        elif event == cv2.EVENT_LBUTTONUP and selection["dragging"]:
            x1, y1, x2, y2 = normalize_corners(selection["start"], point)
            if x1 == x2 or y1 == y2:
                # rectangle vide (simple clic) : on recommence a zero
                selection.update(start=None, end=None, dragging=False)
            else:
                # rectangle valide : done=True fait sortir de la boucle
                selection.update(end=point, dragging=False, done=True)

    cv2.namedWindow(WINDOW_NAME)                    
    cv2.setMouseCallback(WINDOW_NAME, on_mouse)     # branche la souris sur on_mouse

    # affiche le rectangle en direct tant que la selection n'est pas finie
    while not selection["done"]:
        canvas = draw_selection(image, selection["start"], selection["end"])
        cv2.imshow(WINDOW_NAME, canvas)

        # attendre 20ms pour passer a la prochaine itiration 
        if cv2.waitKey(REFRESH_DELAY_MS) & 0xFF == ESC_KEY:
            cv2.destroyWindow(WINDOW_NAME)
            return None


    # montre le rectangle final 0,5 s puis ferme la fenêtre
    canvas = draw_selection(image, selection["start"], selection["end"])
    cv2.imshow(WINDOW_NAME, canvas)
    cv2.waitKey(CONFIRMATION_DELAY_MS)
    cv2.destroyWindow(WINDOW_NAME)

    # renvoie (x1, y1, x2, y2)t
    return normalize_corners(selection["start"], selection["end"])


if __name__ == "__main__":
    import sys

    frame = cv2.imread(sys.argv[1])
    if frame is None:
        raise SystemExit("Cannot read image: " + sys.argv[1])
    print("Selected rectangle (x1, y1, x2, y2):", select_rectangle(frame))