import numpy as np
import random


class GeneticAlgorithm ():

    population = []
    contract = None
    mutation_rate = 0.2
    crossover_rate = 0.2
    fitnesses = []
    results = []
    random_individual = None
    mutate_individual = None
    crossover_individuals = None

    def __init__(self, population_size, contract, random_individual, mutate_individual, crossover_individuals):
        #self.population = np.random.random(size=population_shape)
        self.population = []

        self.random_individual = random_individual
        self.mutate_individual = mutate_individual
        self.crossover_individuals = crossover_individuals
        for i in range(population_size):
            self.population.append(self.random_individual())

        self.contract = contract

    def crossover(self, x, y):
        return self.crossover_individuals(x, y)

    def mutate(self, x):
        return self.mutate_individual(x)

    def evolve(self):
        pop_size = len(self.population)

        parents = {}

        for i in range(pop_size):
            individual = self.population[i]

            self.population.append(individual)

            if random.random() < self.crossover_rate:
                ind = random.randint(0, pop_size-1)
                partner = self.population[ind]
                c1, c2 = self.crossover(individual, partner)
                parents[i] = []
                parents[i].append(len(self.population))
                parents[i].append(len(self.population)+1)
                parents[i].append(ind)

                self.population.append(self.mutate(c1))
                self.population.append(self.mutate(c2))

        fitnesses = []

        for i in range(len(self.population)):
            fitnesses.append(self.contract(self.population[i]))

        removals = set()

        for i in parents.keys():
            indices = parents[i]
            c_fit = [i, indices[0], indices[1], indices[2]]

            sorted(c_fit, key=lambda x: fitnesses[x])

            removals.add(c_fit[-1])
            removals.add(c_fit[-2])

        removals = sorted(removals, reverse=True)

        for r in removals:
            self.population.pop(r)
            fitnesses.pop(r)

        sorted_indices = np.argsort(fitnesses, axis=0).tolist()

        pop = []
        fit = []

        for i in sorted_indices:
            pop.append(self.population[i])
            fit.append(fitnesses[i])


        self.population = pop
        self.population = self.population[:pop_size]
        self.fitnesses = self.fitnesses[:pop_size]


        self.fitnesses = fit


if __name__ == '__main__':

    def contract (value):
        t = 0
        for i in range(len(value)):
            t += 1-value[i]
        return t

    def rand():
        l = []
        for i in range(100):
            l.append(random.randint(0, 1))
        return l

    def mutate(x):
        x[random.randint(0, len(x)-1)] = random.randint(0, 1)
        return x

    def crossover(x, y):
        point = random.randint(1, len(x)-1)
        c1 = x[:point] + y[point:]
        c2 = x[point:] + y[:point]

        return c1, c2


    ga = GeneticAlgorithm(100, contract, rand, mutate, crossover)

    print("Running GA")

    for i in range(10000):
        print("Generation", i)
        ga.evolve()

        print(ga.fitnesses[0], ga.population[0])

        if (ga.fitnesses[0] == 0):
            break
