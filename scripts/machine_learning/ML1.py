#!/usr/bin/env python

import sys
import logging
import time
import string
import datetime
import getopt
import random
import subprocess
import os

# Import Machine Leaning Libraries
import scipy
import numpy
import matplotlib
import pandas
import sklearn
import pickle

from pandas import read_csv
from pandas.plotting import scatter_matrix
from matplotlib import pyplot
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC

import log_utils

model_directory = '/home/saqib/jenkins/data/ML_models/'

class ML1:
    def __init__(self, i_instruction_map, i_model_directory=model_directory):
        self.names = ['opcode0', 'opcode1', 'opcode2', 'opcode3', 'opcode4', 'opcode5', 'opcode6', 'opcode7', 'opcode8', 'opcode9',
                      'opcode10', 'opcode11', 'opcode12', 'opcode13', 'opcode14', 'opcode15', 'opcode16', 'opcode17', 'opcode18', 'opcode19',
                      'opcode20', 'opcode21', 'opcode22', 'opcode23', 'opcode24', 'opcode25', 'opcode26', 'opcode27', 'opcode28', 'opcode29',
                      'opcode30', 'opcode31', 'opcode32', 'opcode33', 'opcode34', 'opcode35', 'opcode36', 'opcode37', 'opcode38', 'opcode39',
                      'opcode40', 'opcode41', 'opcode42', 'opcode43', 'opcode44', 'opcode45', 'opcode46', 'opcode47', 'opcode48', 'opcode49',
                      'opcode50', 'opcode51', 'opcode52', 'opcode53', 'opcode54', 'opcode55', 'opcode56', 'opcode57', 'opcode58', 'opcode59',
                      'opcode60', 'opcode61', 'opcode62', 'opcode63', 'instruction']

        # Define all models here
        self.models = []
        self.models.append(('LR', LogisticRegression(solver='liblinear', multi_class='ovr')))
        self.models.append(('LDA', LinearDiscriminantAnalysis()))
        self.models.append(('KNN', KNeighborsClassifier()))
        self.models.append(('CART', DecisionTreeClassifier()))
        self.models.append(('NB', GaussianNB()))
        self.models.append(('SVM', SVC(gamma='auto')))

        # A list of all models that are stored on drive
        self.model_files = []
        self.loaded_models = [None] * len(self.models)
        for i in range(len(self.models)):
            i_model_file = i_model_directory + self.models[i][0] + '_opcode_model.sav'
            self.model_files.append(i_model_file)

            # If model exists, then load the model
            if os.path.exists(i_model_file):
                loaded_model = pickle.load(open(i_model_file, 'rb'))
                self.loaded_models[i] = loaded_model

        # Delete useless variables
        del loaded_model, i_model_file, i, i_model_directory

        # Start processing the input data
        X = numpy.array(i_instruction_map.opcode)
        y = numpy.array(i_instruction_map.instruction)

        X_train, X_validation, Y_train, Y_validation = train_test_split(X, y, test_size=0.20, random_state=1)

        ############################################################################################
        # Make predictions
        l_accuracy_scores = [None] * len(self.models)
        l_confusion_matrix = [None] * len(self.models)
        l_classification_report = [None] * len(self.models)
        for i in range(len(self.models)):

            try:
                if self.loaded_models[i] is None:
                    model = self.models[i][1]
                else:
                    model = self.loaded_models[i]

                model.fit(X_train, Y_train)
                predictions = model.predict(X_validation)
            except Exception as e:
                print("Unable to process the model " + self.models[i][0])
                continue

            l_accuracy_scores[i] = accuracy_score(Y_validation, predictions)
            l_confusion_matrix[i] = confusion_matrix(Y_validation, predictions)
            l_classification_report[i] = classification_report(Y_validation, predictions)

            # Save the models
            pickle.dump(model, open(self.model_files[i], 'wb'))

        # Print Results:
        sys.stdout.flush()
        print("\n\nHere are the accuracy scores: ")
        for i in range(len(self.models)):
            print(self.models[i][0] + ":" + str(l_accuracy_scores[i]))
        sys.stdout.flush()
