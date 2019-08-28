import os
import numpy as np
import cv2
import csv
import pickle
import random
from ga import GeneticAlgorithm

bins = 30
grid_size = 13
classes = 11
hist_weight = 1
prob_weight = 1
dim_weight = 1
image_counts = [1, 5, 10000, 25000, 50000]

cache = None

def get_real_images(path):
    if path[-1] != "/":
        path += "/"
    files = []
    labels = []
    for i in range(93, 244):
        f=path+"images/"+str(i)+".png"
        l=path+"labels/"+str(i)+".txt"
        if os.path.exists(f) and os.path.exists(l):
            files.append(f)
            labels.append(l)

    return files, labels

def get_synthetic_images(path):
    if path[-1] != "/":
        path += "/"
    files = []
    labels = []

    with open(path+"train.txt") as fileset:
        for line in fileset:
            f = line.replace("/data/acp15tdw/data/", path).strip()
            l = f.replace("images", "labels").replace(".png", ".txt")
            if os.path.exists(f) and os.path.exists(l):
                files.append(f)
                labels.append(l)

    return files, labels


def get_stats(f, l):
    global cache
    if cache is None:
        if os.path.exists("cache.pkl"):
            with open("cache.pkl", "rb") as p_f:
                cache = pickle.load(p_f)
        else:
            cache = {}

    if not f in cache:
        image = cv2.imread(f, 0)

        hist = np.reshape(cv2.calcHist([image], [0], None, [bins], [0, 256]), [-1])

        hist = hist / np.sum(hist)

        labels = []

        with open(l) as l_file:
            label_file = csv.reader(l_file, delimiter=' ', quoting=csv.QUOTE_NONNUMERIC)
            for line in label_file:
                line[1] = max(0, min(grid_size-1, line[1]*grid_size))
                line[2] = max(0, min(grid_size-1, line[2]*grid_size))
                labels.append(line)

        grid = np.zeros([grid_size, grid_size, classes])
        dims = np.zeros([classes, 2])

        for label in labels:
            grid[int(label[2]),int(label[1]),int(label[0])] += 1
            dims[int(label[0]), 0] += label[3]
            dims[int(label[0]), 1] += label[4]

        grid /= len(labels)

        dims /= len(labels)

        cache[f] = hist, grid, dims

    return cache[f]


def get_image_statistics(dataset):
    images = dataset['images']
    labels = dataset['labels']

    histogram = np.zeros([30])
    probability_grid = np.zeros([grid_size, grid_size, classes])
    dimensions = np.zeros([classes, 2])

    rows = len(images)

    for i in range(rows):
        hist, grid, dims = get_stats(images[i], labels[i])
        histogram += hist
        probability_grid += grid
        dimensions += dims

    histogram /= rows
    probability_grid /= rows
    dimensions /= rows

    return histogram, probability_grid, dimensions

def get_difference(d1, real_stats):
    s1 = get_image_statistics(d1)
    s2 = real_stats

    hist_diff = np.sum(np.square(s1[0]-s2[0]))*hist_weight
    prob_diff = np.sum(np.square(s1[1]-s2[1]))*prob_weight
    dim_diff = np.sum(np.square(s1[2]-s2[2]))*dim_weight

    return (hist_diff + prob_diff + dim_diff) / len(s1)



real_images = {}
real_images['images'], real_images['labels'] = get_real_images("/home/thomas/test_experiments/data")



train_images = {}
train_images['images'], train_images['labels'] = get_synthetic_images("/home/thomas/work/GuiImages/public")

new_training_images = {"images":[],
                       "labels":[]}

real_stats = get_image_statistics(real_images)

for count in image_counts:

    def contract (x):
        return get_difference(x, real_stats)

    def rand():
        l = {}
        indices = random.choices(range(0, len(train_images["images"])-1), k=count)
        l["images"] = [train_images["images"][i] for i in indices]
        l["labels"] = [train_images["labels"][i] for i in indices]

        return l

    def mutate(x):
        candidate = x["images"][0]

        while candidate in x["images"]:
            rnd = random.randint(0, len(train_images["images"])-1)
            candidate = train_images["images"][rnd]
            candidate_labels = train_images["labels"][rnd]

        ind = random.randint(0, len(x["images"])-1)
        x["images"][ind] = candidate
        x["labels"][ind] = candidate_labels

        return x

    def crossover(x, y):
        point = random.randint(1, len(x)-1)
        c1 = {}
        c2 = {}
        c1["images"] = x["images"][:point] + y["images"][point:]
        c1["labels"] = x["labels"][:point] + y["labels"][point:]

        c2["images"] = y["images"][:point] + x["images"][point:]
        c2["labels"] = y["labels"][:point] + x["labels"][point:]

        return c1, c2

    print("Creating GA - Initialising Population.")


    ga = GeneticAlgorithm(100, contract, rand, mutate, crossover)

    print("Evolving Population for count:", count)

    for i in range(1000):
        ga.evolve()

        if (ga.fitnesses[0] == 0):
            break

    print("Final Fitness:", ga.fitnesses[0], ga.population[0]['images'][:5])

    with open("cache.pkl", "wb") as p_f:
        pickle.dump(cache, p_f)
    print("Writing top", count, "images!")

    with open("train-" + str(count) + ".txt", "w+") as output:
        for image in ga.population[0]["images"]:
            output.write(image + "\n")

