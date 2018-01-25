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

db = connect_to_db()

cursor = db.cursor()

def load_sql_data():
    global db, cursor
    sql = "SELECT XMin, XMax, YMin, YMax, LabelType, ImageId, IsTruncated FROM labels" # this needs to only use verified labels when we have more data

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
            image_id = str(row[5])
            if not image_id in image_labels:
                image_labels[image_id] = []

            # labels will be used to calculate anchors
            labels.append([width, height])
            image_labels[image_id].append([float(row[0]), float(row[1]), float(row[2]), float(row[3]), int(row[4])-1])
    except pymysql.InternalError as e:
        print (e)

    return {'labels':labels,
            'image_labels':image_labels}



def iou(ele1, ele2):
    return (min(ele1[0], ele2[0]) * min(ele1[1], ele2[1])) / ((max(ele1[0], ele2[0]) * max(ele1[1], ele2[1])))

def convert_label(label):
    return [int(label[4]),
            (label[0]+label[1])/2,
            (label[2] + label[3])/2,
            label[1]-label[0],
            label[3]-label[2]]

def convert_labels(labels): #convert labels into YOLOv2 format
    return list(map(convert_label, labels))

def write_csv(image, dataset, labels):
    np.savetxt('public/labels/' + str(image) + '.txt', labels,
               delimiter=' ', fmt='%i %f %f %f %f')

    data_file = 'public/' + dataset + ".txt"

    try:
        file = open(data_file, 'a')
    except IOError:
        file = open(data_file, 'w+')

    file.write('/home/thomas/work/gui_image_identification/public/images/' +str(image)+".png\n")
    file.close()

if __name__ == '__main__':
    data = load_sql_data()

    sql = "SELECT ImageId, Subset, File FROM images" # this needs to only use verified labels when we have more data

    images = {}

    try:
        # Execute the SQL command
        cursor.execute(sql)
        # Fetch all the rows in a list of lists.
        results = cursor.fetchall()
        for row in results:
            images[str(row[0])] = row
    except pymysql.InternalError as e:
        print (e)

    sql = "SELECT LabelTypeId, LabelName FROM label_types ORDER BY LabelTypeId" # this needs to only use verified labels when we have more data

    label_names = []

    try:
        # Execute the SQL command
        cursor.execute(sql)
        # Fetch all the rows in a list of lists.
        results = cursor.fetchall()
        for row in results:
            label_names.append(row[1])
    except pymysql.InternalError as e:
        print (e)

    np.savetxt('public/data.names', label_names,
               delimiter=',', fmt='%s')

    try:
        os.remove('public/train.txt')
        os.remove('public/test.txt')
        os.remove('public/validate.txt')
    except OSError:
        pass

    for image in data['image_labels']:
        if os.path.isfile('public/'+images[image][2]):
            write_csv(image, images[image][1], convert_labels(data['image_labels'][image]))
