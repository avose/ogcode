################################################################################################
'''
Copyright 2025 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds utilities for working with vectors: contours, lines, etc.
'''
################################################################################################

import cv2
import numpy as np
from typing import List, Tuple

################################################################################################

################################################################
# Convert contours into numpy array of line segments.
################################################################
def contours_to_lines(contours: List[np.ndarray]) -> np.ndarray:
    lines = []
    for contour in contours:
        if len(contour) < 2:
            continue
        start_points = contour
        end_points = np.roll(contour, -1, axis=0)
        segment_pairs = np.stack([start_points, end_points], axis=1)
        lines.append(segment_pairs)

    if len(lines) > 0:
        return np.concatenate(lines, axis=0)
    else:
        return np.empty((0, 2, 2), dtype=float)

################################################################
# Bresenham's line algorithm for integer pixel coordinates.
################################################################
def bresenham_line(p0, p1):
    x0, y0 = p0
    x1, y1 = p1
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        points.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy
    return points

################################################################
# Simplify lines by rasterizing onto a low-resolution canvas and
# extracting contributing segments. Returns array of lines.
################################################################
def simplify_lines(
        lines: np.ndarray,
        edges: np.ndarray,
        scale: float = 0.5
) -> Tuple[np.ndarray, np.ndarray]:
    if lines.shape[0] == 0:
        return np.empty((0, 2, 2), dtype=float), edges

    orig_height, orig_width = edges.shape[:2]
    width = int(orig_width * scale)
    height = int(orig_height * scale)

    min_xy = np.array([0.0, 0.0])
    max_xy = np.array([width, height], dtype=float)
    span = max_xy - min_xy

    canvas = np.zeros((height, width), dtype=bool)
    norm_points = (lines - min_xy) / span
    scaled_points = ((norm_points * [width, height]) - 0.5).astype(int)

    kept_segments = []

    for i in range(scaled_points.shape[0]):
        p1_canvas, p2_canvas = scaled_points[i]
        line_pixels = bresenham_line(tuple(p1_canvas), tuple(p2_canvas))

        start_pixel = None
        last_pixel = None

        for x, y in line_pixels:
            if 0 <= y < height and 0 <= x < width:
                if not canvas[y, x]:
                    canvas[y, x] = True
                    if start_pixel is None:
                        start_pixel = (x, y)
                    last_pixel = (x, y)
                else:
                    if start_pixel is not None and last_pixel is not None:
                        p_start = ((np.array(start_pixel) + 0.5) / [width, height]) * [orig_width, orig_height]
                        p_end = ((np.array(last_pixel) + 0.5) / [width, height]) * [orig_width, orig_height]
                        kept_segments.append([p_start, p_end])
                        start_pixel = None
                        last_pixel = None

        if start_pixel is not None and last_pixel is not None:
            p_start = ((np.array(start_pixel) + 0.5) / [width, height]) * [orig_width, orig_height]
            p_end = ((np.array(last_pixel) + 0.5) / [width, height]) * [orig_width, orig_height]
            kept_segments.append([p_start, p_end])

    # Convert boolean canvas to uint8 RGB image for visualization.
    canvas_image = (canvas.astype(np.uint8) * 255)
    edges_rgb = cv2.cvtColor(canvas_image, cv2.COLOR_GRAY2RGB)
    edges_resized = cv2.resize(edges_rgb, (orig_width, orig_height), interpolation=cv2.INTER_NEAREST)

    return np.array(kept_segments), edges_resized

################################################################
# Rotate the lines in the associated coordinate space.
################################################################
def rotate_lines(lines, height=None, width=None, clockwise=True):
    lines = lines.reshape(-1, 2, 2)

    if height is None or width is None:
        max_y = int(np.max(lines[:, :, 1]))
        max_x = int(np.max(lines[:, :, 0]))
        height = max_y + 1
        width = max_x + 1

    if clockwise:
        # (x, y) -> (height - y, x)
        lines = np.stack([height - lines[:, :, 1], lines[:, :, 0]], axis=-1)
    else:
        # (x, y) -> (y, width - x)
        lines = np.stack([lines[:, :, 1], width - lines[:, :, 0]], axis=-1)

    return lines

################################################################
# Flip the lines in the associated coordinate space.
################################################################
def flip_lines(lines, height=None, width=None, vertical=True):
    lines = lines.reshape(-1, 2, 2)

    if height is None or width is None:
        max_y = int(np.max(lines[:, :, 1]))
        max_x = int(np.max(lines[:, :, 0]))
        height = max_y + 1
        width = max_x + 1

    if vertical:
        # (x, y) -> (x, height - y)
        lines = np.stack([lines[:, :, 0], height - lines[:, :, 1]], axis=-1)
    else:
        # (x, y) -> (width - x, y)
        lines = np.stack([width - lines[:, :, 0], lines[:, :, 1]], axis=-1)

    return lines

################################################################################################
