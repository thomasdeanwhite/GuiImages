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
    return [ele[4], ele[0]-ele[2]/2, ele[1]-ele[3]/2, ele[0]+ele[2]/2, ele[1]+ele[3]/2, ele[5]]


def load_bb(files, widgets):
    bounding_boxes = {}
    test_data = []

    for file in files:
        widget = file.split(".")[2]
        weight = file.split("/")
        weight = weight[-1].split("_")[1].split(".")[0]
        weight_id = str(weight)
        if not weight_id in bounding_boxes:
            bounding_boxes[weight_id] = {}

        with open(file, 'r') as f:
            widget_id = widgets[widget]
            for line in f:
                box = line.strip().split(" ")
                if len(box) <= 5:
                    continue
                image_id = box[0]
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


def iou(ele1, ele2, reverse=False):
    if not (ele1[1] <= ele2[3] and ele1[3] >= ele2[1] \
            and ele1[2] <= ele2[4] and ele1[4] >= ele2[2]):
        if not reverse:
            return iou(ele2, ele1, reverse=True)
        return 0
    intersect_x = abs(max(ele2[1] - ele1[3], ele1[1] - ele2[3]))
    intersect_y = abs(max(ele2[2] - ele1[4], ele1[2] - ele2[4]))
    numerator =  intersect_x * intersect_y
    area = ((ele1[3] - ele1[1]) * (ele1[4] - ele1[2])) + ((ele2[3] - ele2[1]) * (ele2[4] - ele2[2]))
    denominator = area - numerator
    if denominator == 0:
        return 0
    return numerator / denominator


def run_files(widgets, i_widgets, files, dataset):
    print("Loading bb data for " + dataset)

    boxes, test_data = load_bb(files, widgets)

    test_boxes = {}

    confusion = {}

    print("Loading real bb data for " + dataset)
    for image_id in test_data:
        path = sys.argv[2] + "/labels/" + str(image_id) + ".txt"
        test_boxes[str(image_id)] = load_bb_test(path)

    results = {}

    print("Comparing")

    for weight in boxes:
        print("\r(" + dataset + ") Weight: " + weight, end="")
        box = boxes[weight]

        for image_id in box:
            image = box[image_id]

            results = {}

            for row in image:

                comp_id = str(row[0])

                if not comp_id in results:
                    #iou, correct, total, confidence
                    results[comp_id] = [0, 0, 0, 0]

                best_iou = 0
                best_img = []
                for t_row in test_boxes[image_id]:
                    c_iou = iou(t_row, row)

                    if c_iou > best_iou:# and row[0] == t_row[0]:
                        best_iou = c_iou
                        best_img = t_row

                if best_iou > 0:
                    if row[0] == best_img[0]:
                        results[comp_id][1] += 1
                    if not str(row[0]) in confusion:
                        confusion[str(row[0])] = {}
                    if not str(best_img[0]) in confusion[str(row[0])]:
                        confusion[str(row[0])][str(best_img[0])] = 0
                    confusion[str(row[0])][str(best_img[0])] += 1
                    results[comp_id][0] += best_iou
                    results[comp_id][2] += 1
                    results[comp_id][3] += row[5]
            with open(sys.argv[2] + "/processed/output.csv", "a") as file:
                for comp_id in results:
                    row = results[comp_id]
                    #average IOU
                    if row[2] > 0:
                        row[0] /= row[2]
                        row[3] /= row[2]

                    file.write(str(weight) + "," + image_id + "," + i_widgets[comp_id] + "," + str(row[0]) + "," + str(row[1]) + "," + str(row[2]) + "," + str(row[3]) + "," + dataset + "\n")
    print()
    print(" " + "\t\t", end="")
    for j in range(10):
        print(i_widgets[str(j)] + "\t\t", end="")
    print()
    for i in range(10):
        print(i_widgets[str(i)] + "\t\t", end="")
        for j in range(10):
            if i in confusion and str(j) in confusion[str(i)]:
                print(str(round(confusion[str(i)][str(j)]/sum(confusion[str(i)].values()), 2)) + " \t",end="")
            else:
                print("0" + "\t\t", end="")
        print()

if __name__ == "__main__":
    print("Loading Widgets")
    widgets, i_widgets = load_widgets(sys.argv[2])

    with open(sys.argv[2] + "/processed/output.csv", "w") as file:
        file.write("weight,image,label,average_iou,correct_classifications,total_classifications,confidence,dataset\n")

    run_files(widgets, i_widgets, list_files(sys.argv[1] + "/test"), "test")
    run_files(widgets, i_widgets, list_files(sys.argv[1] + "/train"), "train")
