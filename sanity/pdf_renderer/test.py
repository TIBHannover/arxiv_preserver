import build.libpdf_python as pdf_python
import numpy as np
import cv2


def rescale_with_as(size, target_size_max):
    assert len(target_size_max) == len(size)
    ratio = float(size[0]) / size[1]
    target_ratio = float(target_size_max[0]) / target_size_max[1]
    # scale to max_height
    if ratio > target_ratio:
        return [int(target_size_max[0]), int(size[1] * target_size_max[0] / size[0])]

    # scale to max_width
    else:
        return [int(target_size_max[0] * target_size_max[1] / size[1]), int(target_size_max[1])]


with open('/home/matthias/downloads/1701.07875.pdf', 'rb') as f:
    data = f.read()
    document = pdf_python.Document(data)
    page = document.page(0)
    size = page.size()
    target_size = rescale_with_as(size, [500, 500])
    print(size)
    print(target_size)
    img = page.renderToArray()
    cv2.imwrite('messigray.png', img)
    img = page.renderToArray(target_size)
    cv2.imwrite('messigray_.png', img)
