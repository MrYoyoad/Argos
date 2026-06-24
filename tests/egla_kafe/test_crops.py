"""Unit tests for make_speaker_crops.py pure logic (clustering + box geometry)."""
import numpy as np
import make_speaker_crops as M


def _det(xc):
    # (xc_norm, yc_norm, x, y, w, h) with a plausible face box for a 1000x600 frame
    return (xc, 0.4, xc * 1000 - 40, 200, 80, 100)


def test_three_clusters_drops_center_listener():
    # left ~0.2, center ~0.5, right ~0.8 (the constant listener is the middle)
    dets = []
    for xc in (0.2, 0.5, 0.8):
        dets += [_det(xc + j * 0.005) for j in range(-2, 3)]
    clusters, dropped = M.cluster_speakers(dets, n_speakers=2, n_people=3)
    assert dropped is True
    assert len(clusters) == 2
    assert clusters[0]["x_center"] < 0.35  # left kept
    assert clusters[1]["x_center"] > 0.65  # right kept


def test_two_person_master_keeps_both():
    dets = []
    for xc in (0.3, 0.7):
        dets += [_det(xc + j * 0.005) for j in range(-2, 3)]
    clusters, dropped = M.cluster_speakers(dets, n_speakers=2)
    assert dropped is False
    assert len(clusters) == 2
    assert clusters[0]["x_center"] < clusters[1]["x_center"]


def test_square_crop_box_is_square_and_in_frame():
    W, H = 1000, 600
    x0, y0, w, h = M.square_crop_box([100, 200, 80, 100], W, H, pad=1.9)
    assert w == h
    assert 0 <= x0 and x0 + w <= W
    assert 0 <= y0 and y0 + h <= H


def test_square_crop_box_clamps_oversize():
    W, H = 400, 300
    x0, y0, w, h = M.square_crop_box([10, 10, 500, 500], W, H, pad=1.9)
    assert w == h <= min(W, H)
    assert x0 >= 0 and y0 >= 0 and x0 + w <= W and y0 + h <= H
