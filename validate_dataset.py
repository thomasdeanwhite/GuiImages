import os
import sys

def list_files(dir):
    files = []
    for file in os.listdir(dir):
        files.append(file)
    return files


files = list_files(sys.argv[1])

def load_widgets(dir):
    counter = 0
    widgets = {}
    with open(dir + "/data.names", "r") as file:
        for line in file:
            widgets[line.strip()] = counter
            counter += 1
    return widgets


def load_bb(files, widgets):
    bounding_boxes = {}
    for file in files:
        widget = file.split(".")[2]
        weight = file.split("_")[1].split(".")[0]
        boxes = []
        weight_id = str(weight)
        bounding_boxes[weight_id] = {}

        with open(file, 'r') as f:
            widget_id = widgets[widget]
            for line in f:
                box = line.strip().split(" ")
                image_id = box[0]
                if not image_id in bounding_boxes[weight_id]:
                    bounding_boxes[weight_id][image_id] = []
                bounding_boxes[weight_id][image_id].append([
                    int(box[2]), int(box[3]), int(box[4]), int(box[5]),
                    int(box[1])])

        print(widget, weight)

widgets = load_widgets(sys.argv[2])

print(widgets)

load_bb(files, widgets)