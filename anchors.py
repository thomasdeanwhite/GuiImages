import os
import math
import random

import numpy as np
import tensorflow as tf
import cv2

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patches as patches
import config
import pymysql
import csv
from scipy.cluster.vq import kmeans,vq

image_segments = [13, 13]
segment_size = [1.0/image_segments[0], 1.0/image_segments[1]]

k_means_iterations = 1000

n_anchors = 5

bounding_boxes = []

def connect_to_db():
    db = pymysql.connect(config.db['location'], config.db['user'], config.db['password'], config.db['db'])
    return db

def load_sql_data():
    db = connect_to_db()

    cursor = db.cursor()
    sql = "SELECT XMin, XMax, YMin, YMax, LabelType, l.ImageId, IsTruncated FROM labels as l LEFT JOIN images AS i ON i.ImageId = l.ImageId LEFT JOIN label_types AS lt ON LabelTypeId = LabelType WHERE i.Subset='train' AND LabelName!='hyperlink';" # this needs to only use verified labels when we have more data

    labels = []
    image_labels = {}

    try:
        # Execute the SQL command
        cursor.execute(sql)
        # Fetch all the rows in a list of lists.
        results = cursor.fetchall()
        for row in results:

            row1 = row[1]
            row3 = row[3]

            if row[1] > 1.1:
                row1 = 1.1
            if row[3] > 1.1:
                row3 = 1.1

            width = row1 - row[0]
            height = row3 - row[2]

            if width <= 0 or height <= 0 or row[0] > 1 or row[2] > 1:
                continue

            image_id = str(row[5])
            if not image_id in image_labels:
                image_labels[image_id] = []

            # labels will be used to calculate anchors
            labels.append([width, height])
            image_labels[image_id].append([width, height, row[4]])
    except pymysql.InternalError as e:
        print (e)

    return {'labels':labels,
            'image_labels':image_labels}


def average_iou(centroids, labels):
    average_iou = 0
    count = 0
    for label in labels:
        best_iou = 0
        for centroid in centroids:
            difference = iou(centroid, label)

            if (difference > best_iou):
                best_iou = difference
        count = count + 1
        average_iou += best_iou

    return average_iou/count

def iou(ele1, ele2):
    numerator = (min(ele1[0], ele2[0]) * min(ele1[1], ele2[1]))
    denominator = ((max(ele1[0], ele2[0]) * max(ele1[1], ele2[1])))
    return numerator / denominator

random_padding = 0.001
random_mult = 1 - random_padding

def random_cluster_init(labels, kmeansplus=False):
    global n_anchors
    centroids = []


    while len(centroids) < n_anchors:
        if kmeansplus:

            if len(centroids) == 0:
                centroids.append(random.sample(list(labels), 1)[0])

            distances = []
            for i in range(len(labels)):
                distances.append(0.0)
                for j in centroids:
                    distance = iou(labels[i], j)
                    if distance > distances[i]:
                        distances[i] = distance

            furthest = 0

            for i in range(len(labels)):
                if distances[i] < distances[furthest]:
                    furthest = i
            centroids.append(labels[furthest])
        else:
            centroids.append([random.random()*random_mult + random_padding, random.random()*random_mult + random_padding])

    return np.array(centroids)

def gen_anchors():#k-means to generate bounding boxes
    global n_anchors, k_means_iterations
    data = load_sql_data()
    labels = data['labels']

    #labels = np.array(labels)

    centroids = []
    best_centroids = []
    best_iou = 0

    n_samples = 300

    centroids = []


    for centroid in centroids:
        best_centroids.append(centroid)

    best_iou = average_iou(centroids, labels)

    max_gens = 1000

    for iter in range(max_gens):
        centroids = random_cluster_init(labels)

        for iteration in range(k_means_iterations):
            assignments = []

            for i in range(n_anchors):
                assignments.append([])

            for label in labels:
                min_distance = 0
                cluster = 0
                for i in range(len(centroids)):
                    centroid = centroids[i]
                    distance = iou(label, centroid)
                    if distance > min_distance:
                        min_distance = distance
                        cluster = i

                assignments[cluster].append(label)

            new_centroids = []

            changed = False

            for a in assignments:
                assignment = np.array(a)

                centroid = [random.random()*random_mult + random_padding, random.random()*random_mult + random_padding]

                if len(assignment) > 0:
                    centroid = assignment.mean(axis=0)


                new_centroids.append(centroid)

                if not (centroids == centroid).all(1).any():
                    changed = True

            centroids = new_centroids

            if not changed:
                break

        avg_iou = average_iou(centroids, labels)

        if avg_iou > best_iou:
            best_iou = avg_iou
            best_centroids = centroids

            best_centroids = sorted(best_centroids, key=lambda centroid: -centroid[0]*centroid[1])

            cluster_string = ""
            for anchor in best_centroids:
                cluster_string = cluster_string  + str(anchor[0]*13) + ',' + str(anchor[1]*13) + ",  "

            print()
            print("best iou of", best_iou, "with clusters:",cluster_string )

        print("\rProgress: " + str(iter) + "/" + str(max_gens) + " [" + str(round(100*(iter/max_gens))) + "%]", end='')
    return best_centroids

def expand_anchor(anchor, x, y):
    offset_x = (segment_size[0] * (x + 0.5))
    offset_y = (segment_size[1] * (y + 0.5))
    return [(-anchor[0]/2) + offset_x, (anchor[0]/2) + offset_x,
            (-anchor[1]/2) + offset_y, (anchor[1]/2) + offset_y]

def convert_label(label):
    return [(label[0]+label[1])/2,
            (label[2] + label[3])/2,
            label[1]-label[0],
            label[3]-label[2]]

def convert_labels(labels): #convert labels into YOLOv2 format
    return list(map(convert_label, labels))

if __name__ == '__main__':
    anchors = gen_anchors()

    anchor_string = ""

    for anchor in anchors:
        anchor_string = anchor_string + str(anchor[0]*13) + ',' + str(anchor[1]*13) + ",  "

    print(anchor_string)

    fig1 = plt.figure()
    ax1 = fig1.add_subplot(111, aspect='equal')

    for anchor in anchors:
        shifted = expand_anchor(anchor, 0, 0)
        ax1.add_patch(
            patches.Rectangle(
                (shifted[0], shifted[2]),
                shifted[1]-shifted[0], shifted[3]-shifted[2],
                fill=False
            )
        )

    plt.axis('off')
    ax1.relim()
    ax1.autoscale_view(True, True, True)
    #plt.draw()
    #plt.show()
    fig1.savefig('anchors.png', dpi=90, bbox_inches='tight')