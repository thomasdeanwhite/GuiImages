import os
import sys


def list_files(dir):
    files = []
    for file in os.listdir(dir):
        files.append(dir + "/" + file)
    return files


def load_widgets(dir):
    counter = 0
    widgets = {}
    inverse = {}
    with open(dir + "/data.names", "r") as file:
        for line in file:
            widgets[line.strip()] = counter
            inverse[str(counter)] = line.strip()
            counter += 1
    return widgets, inverse

def to_standard(ele):
    return [ele[4], ele[0], ele[1], ele[2], ele[3], ele[5]]


def load_bb(files, widgets):
    bounding_boxes = {}
    test_data = []

    for file in files:
        widget = file.split(".")[2]
        weight = file.split("/")
        weight = weight[-1].split("_")[1].split(".")[0]
        weight_id = str(weight)
        if weight_id != "9000":
            continue
        if not weight_id in bounding_boxes:
            bounding_boxes[weight_id] = {}

        with open(file, 'r') as f:
            widget_id = widgets[widget]
            for line in f:
                box = line.strip().split(" ")
                if len(box) <= 5:
                    continue
                image_id = box[0]
                if int(image_id) < 244:
                    if not image_id in bounding_boxes[weight_id]:
                        bounding_boxes[weight_id][image_id] = []
                    if not image_id in test_data:
                        test_data.append(image_id)

                    bounding_boxes[weight_id][image_id].append(to_standard([
                        float(box[2]), float(box[3]), float(box[4]), float(box[5]), int(widget_id),
                        float(box[1])]))

    return bounding_boxes, test_data


def load_bb_test(file):
    bounding_boxes = []

    with open(file, 'r') as f:
        for line in f:
            box = line.strip().split(" ")
            widget_id = box[0]

            bounding_boxes.append(to_standard([
                float(box[1]), float(box[2]), float(box[3]), float(box[4]), int(widget_id), 1.0]))

    return bounding_boxes

def run_files(widgets, i_widgets, files, dataset):
    print("Loading bb data for " + dataset)

    boxes, test_data = load_bb(files, widgets)

    print("Processing from darknet into standard format")

    for weight in boxes:
        print("\r(" + dataset + ") Weight: " + weight, end="")
        box = boxes[weight]

        for image_id in box:
            fname = sys.argv[2] + "/processed/" + weight + "/labels"
            if not os.path.exists(os.path.dirname(fname)):
                os.makedirs(fname)
            with open(fname + "/" + image_id + ".txt", "w+") as f:
                f.write("")

        for image_id in box:
            image = box[image_id]
            with open(sys.argv[2] + "/processed/" + weight + "/labels/" + image_id + ".txt", "a") as f:
                for bb in image:
                    bbox_string = "{} {} {} {} {} {}\n".format(
                                         bb[0], bb[1], bb[2], bb[3], bb[4], bb[5])
                    f.write(bbox_string)

if __name__ == "__main__":
    print("Loading Widgets")
    widgets, i_widgets = load_widgets(sys.argv[2])

    run_files(widgets, i_widgets, list_files(sys.argv[1] + "/test"), "test")
    run_files(widgets, i_widgets, list_files(sys.argv[1] + "/train"), "train")
