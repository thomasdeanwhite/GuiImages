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

k_means_iterations = 100

n_anchors = 5

bounding_boxes = []

def connect_to_db():
    db = pymysql.connect(config.db['location'], config.db['user'], config.db['password'], config.db['db'])
    return db

def load_sql_data():
    db = connect_to_db()

    cursor = db.cursor()
    sql = "SELECT XMin, XMax, YMin, YMax, LabelType, l.ImageId, IsTruncated FROM labels as l LEFT JOIN images AS i ON i.ImageId = l.ImageId WHERE i.Subset='train';" # this needs to only use verified labels when we have more data

    labels = []
    image_labels = {}

    try:
        # Execute the SQL command
        cursor.execute(sql)
        # Fetch all the rows in a list of lists.
        results = cursor.fetchall()
        for row in results:
            width = row[1] - row[0]
            height = row[3] - row[2]

            if width == 0 or height == 0:
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



def iou(ele1, ele2):
    return (min(ele1[0], ele2[0]) * min(ele1[1], ele2[1])) / ((max(ele1[0], ele2[0]) * max(ele1[1], ele2[1])))

def gen_anchors():#k-means to generate bounding boxes
    global n_anchors, k_means_iterations
    data = load_sql_data()
    labels = data['labels']

    #labels = np.array(labels)

    centroids = []

    n_samples = 50

    centroids.append(random.sample(list(labels), 1)[0])

    while len(centroids) < n_anchors:
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





    centroids = np.array(centroids)

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

            centroid = assignment.mean(axis=0)

            new_centroids.append(centroid)

            if not (centroids == centroid).all(1).any():
                changed = True

        centroids = new_centroids

        if not changed:
            print("No changes after", iteration, "iterations")
            break

    return centroids

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
        anchor_string = anchor_string + str(round(anchor[0]*13, 4)) + ',' + str(round(anchor[1]*13, 4)) + ",  "

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