import pytest
import validate_dataset

def test_iou_one_dim():
    rect1 = [0, 0, 0, 1, 1]
    rect2 = [0, 0.5, 0.5, 1.5, 1.5]

    assert 0.14285714285714285 == validate_dataset.iou(rect1, rect2)
    assert 0.14285714285714285 == validate_dataset.iou(rect2, rect1)


def test_iou_inside():
    rect1 = [0, 0, 0, 1, 1]
    rect2 = [0, 0.5, 0.5, 1, 1]

    assert 0.25 == validate_dataset.iou(rect1, rect2)
    assert 0.25 == validate_dataset.iou(rect2, rect1)

def test_iou_zero():
    rect1 = [0, 0, 0, 1, 1]
    rect2 = [0, 1.0, 1.0, 2.0, 2.0]

    assert 0 == validate_dataset.iou(rect1, rect2)
    assert 0 == validate_dataset.iou(rect2, rect1)

def test_iou_zero_dim():
    rect1 = [0, 0, 0, 1, 1]
    rect2 = [0, 1.0, 1.0, 1.0, 1.0]

    assert 0 == validate_dataset.iou(rect1, rect2)
    assert 0 == validate_dataset.iou(rect2, rect1)
    assert 0 == validate_dataset.iou(rect2, rect2)