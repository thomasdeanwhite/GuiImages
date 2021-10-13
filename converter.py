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
    sql = "SELECT XMin, XMax, YMin, YMax, LabelType, ImageId, IsTruncated FROM labels ORDER BY LabelId" # this needs to only use verified labels when we have more data

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
            image_labels[image_id].append([float(row[0]), float(row[1]), float(row[2]), float(row[3]), int(row[4])])
    except pymysql.InternalError as e:
        print (e)

    return {'labels':labels,
            'image_labels':image_labels}



def iou(ele1, ele2):
    return (min(ele1[0], ele2[0]) * min(ele1[1], ele2[1])) / ((max(ele1[0], ele2[0]) * max(ele1[1], ele2[1])))

def convert_label(label):
    ret = [int(label[4]),
     (label[0]+label[1])/2,
     (label[2] + label[3])/2,
     label[1]-label[0],
     label[3]-label[2]]
    return ret

def convert_labels(labels): #convert labels into YOLOv2 format
    return list(map(convert_label, labels))

def write_dataset(image, dataset):
    data_file = 'public/' + dataset + ".txt"

    try:
        file = open(data_file, 'a')
    except IOError:
        file = open(data_file, 'w+')

    sharc_output = True

    if sharc_output:
        file.write('/data/acp15tdw/data/images/' +str(image)+".png\n")
    else:
        file.write('/home/thomas/work/gui_image_identification/public/images/' +str(image)+".png\n")
    file.close()

def write_csv(image, dataset, labels):
    np.savetxt('public/labels/' + str(image) + '.txt', labels,
               delimiter=' ', fmt='%i %f %f %f %f')

    write_dataset(image, dataset)



if __name__ == '__main__':
    data = load_sql_data()

    sql = "SELECT ImageId, Subset, File, Source FROM images WHERE Dataset != 'web'" # this needs to only use verified labels when we have more data

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

    sql = "SELECT LabelTypeId, LabelName FROM label_types WHERE LabelName!='hyperlink' ORDER BY LabelTypeId" # this needs to only use verified labels when we have more data

    label_names = []
    label_nums = {}
    label_count = 0

    try:
        # Execute the SQL command
        cursor.execute(sql)
        # Fetch all the rows in a list of lists.
        results = cursor.fetchall()
        for row in results:
            label_names.append(row[1])
            label_nums[str(row[0])]=label_count
            label_count = label_count+1
    except pymysql.InternalError as e:
        print (e)

    np.savetxt('public/data.names', label_names,
               delimiter=',', fmt='%s')

    try:
        os.remove('public/train.txt')
        os.remove('public/test.txt')
        os.remove('public/validate.txt')
        os.remove('public/train-balanced.txt')
        os.remove('public/test-balanced.txt')
        os.remove('public/validate-balanced.txt')
    except OSError:
        pass

    for image in data['image_labels']:
        n = 0
        while n < len(data['image_labels'][image]):
            label = data['image_labels'][image][n]
            if str(label[4]) in label_nums and label[0] <= 1 and label[2] <= 1:

                if label[1] > 1.1:
                    label[1] = 1.1
                if label[3] > 1.1:
                    label[3] = 1.1

                label[4] = label_nums[str(label[4])]
                n = n + 1
            else:
                del(data['image_labels'][image][n])

    themes = {}

    for image in data['image_labels']:
        if image in images:
            if os.path.isfile('public/'+images[image][2]):
                if len(data['image_labels'][image]) > 0:
                    img = data['image_labels'][image]
                    img_theme = images[image][3]
                    img_file = images[image][2]

                    if img_theme.find("synthetic ") != -1:
                        theme_elements = img_theme.split("-jframe-")
                        theme = theme_elements[1]

                        if not theme in themes:
                            themes[theme] = []

                        themes[theme].append(image)

    min_theme_files = 0

    for t in themes:

        random.shuffle(themes[t])

        leng = len(themes[t])
        if min_theme_files == 0 or leng < min_theme_files:
            min_theme_files = leng

    print("Balancing around", min_theme_files, "themes (", len(themes), "themes", ")")

    for t in themes:
        for image in themes[t][:min_theme_files]:
            if image in images:
                if os.path.isfile('public/'+images[image][2]):
                    if len(data['image_labels'][image]) > 0:
                        img = data['image_labels'][image]
                        write_dataset(image, images[image][1] + "-balanced")



    for image in data['image_labels']:
        if image in images:
            if os.path.isfile('public/'+images[image][2]):
                if len(data['image_labels'][image]) > 0:
                    img = data['image_labels'][image]
                    write_csv(image, images[image][1], convert_labels(img))
                else:
                    print("Removed", images[image][2], "from dataset (zero labels)")
