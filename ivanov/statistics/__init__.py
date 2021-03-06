'''
Created on Feb 26, 2016

@author: Ivan Ivanov
'''

from sklearn.metrics import roc_auc_score, precision_score, recall_score, accuracy_score
from sklearn.metrics import roc_curve as sk_roc_curve 
from ivanov.graph import dataset_manager
from collections import Counter
from itertools import imap
import numpy as np
import itertools
import math

def avg(l):
    return sum(l) / len(l)

def F1(precision, recall):
    return (2. * precision * recall) / (precision + recall) if precision and recall else 0.

def predict_target_majority(targets, default_negative_target=0):
    '''Majority election of target.
    :param similar_targets: A list of either integers or lists. Each element may have multiple target values.
    The target label that appears most frequently is the chosen one.
    '''
    if len(targets):
        if type(targets[0]) is list:
            target_counts = Counter(itertools.chain(*targets))
        else:
            target_counts = Counter(targets)
        majority_label = max(target_counts, key=lambda x: target_counts[x])
        return majority_label
    else:
        return default_negative_target

def predict_binary_target_proba(targets, positive_target=1):
    '''Get the probability that the chosen target will be positive given the input targets.
    '''
    if targets:
        if type(targets[0]) is list:
            targets = itertools.chain(*targets)
        target_counts = Counter(targets)
        assert len(target_counts) <= 2
        predict_proba = float(target_counts[positive_target]) / float(len(targets))
        return predict_proba
    else:
        return 0.

def get_multilabel_target_proportions(targets, examples_count):
    '''Get the proportions of each target appearing among the given number of examples.
    '''
    target_counts = Counter(targets)
    return {target: float(target_counts[target]) / examples_count for target in target_counts}

def prepare_target_with_predictions(svm_light_val_file, predictions_file):
    val_data = dataset_manager.read_svm_light_bool_data(svm_light_val_file)
    pred_f = open(predictions_file)
    
    real_targets = imap(lambda x: x[0], val_data)
    pred_targets = imap(float, pred_f.readlines())
    
    return real_targets, pred_targets

def get_probabilities(pred_targets):
    # deprecated
    def sigmoid(x):
        return 1 / (1 + math.exp(-x))

    targets_prob = imap(sigmoid, pred_targets)
    
    return targets_prob

def apply_threshold(pred_targets, threshold):
    min_pred = min(pred_targets)
    thr = ((max(pred_targets) - min_pred) * threshold) + min_pred
    pred_targets_thr = map(lambda x: 1 if x >= thr else -1, pred_targets)
    
    return pred_targets_thr

def all_scores(real_targets, pred_targets, threshold=0.5):
    pred_targets_thr = apply_threshold(pred_targets, threshold)
    
    auc = roc_auc_score(real_targets, pred_targets)
    acc = accuracy_score(real_targets, pred_targets_thr)
    prec = precision_score(real_targets, pred_targets_thr)
    rec = recall_score(real_targets, pred_targets_thr)
    
    return auc, acc, prec, rec, F1(prec, rec)

def all_scores_from_files(svm_light_val_file, predictions_file, threshold=0.5):
    real_targets, pred_targets = prepare_target_with_predictions(svm_light_val_file, predictions_file)
    real_targets = list(real_targets)
    pred_targets = list(pred_targets)
    
    return all_scores(real_targets, pred_targets, threshold)

def roc_curve(svm_light_val_file, predictions_file):
    real_targets, pred_targets = prepare_target_with_predictions(svm_light_val_file, predictions_file)
    return sk_roc_curve(real_targets, pred_targets)

def auc(svm_light_val_file, predictions_file):
    real_targets, pred_targets = prepare_target_with_predictions(svm_light_val_file, predictions_file)
    real_targets = list(real_targets)
    pred_targets = list(pred_targets)
    return roc_auc_score(real_targets, pred_targets)

def accuracy(svm_light_val_file, predictions_file, threshold=0.5):
    real_targets, pred_targets = prepare_target_with_predictions(svm_light_val_file, predictions_file)
    pred_targets_thr = apply_threshold(pred_targets, threshold)
    return accuracy_score(real_targets, pred_targets_thr)

def precision(svm_light_val_file, predictions_file, threshold=0.5):
    real_targets, pred_targets = prepare_target_with_predictions(svm_light_val_file, predictions_file)
    pred_targets_thr = apply_threshold(pred_targets, threshold)
    return precision_score(real_targets, pred_targets_thr)

def recall(svm_light_val_file, predictions_file, threshold=0.5):
    real_targets, pred_targets = prepare_target_with_predictions(svm_light_val_file, predictions_file)
    pred_targets_thr = apply_threshold(pred_targets, threshold)
    return recall_score(real_targets, pred_targets_thr)

def multi_label_scores(y_true, y_pred):
    '''Compute accuracy, precision, recall and F1 score for multi-label predictions.
    '''
    accuracies = []
    precisions = []
    recalls = []
    f1 = []
    for y_t, y_p in itertools.izip(y_true, y_pred):
        y_t_s = set(y_t)
        y_p_s = set(y_p)
        t = float(len(y_t_s))
        p = float(len(y_p_s))
        inter = float(len(y_t_s & y_p_s))
        union = float(len(y_t_s | y_p_s))
        precision = inter / p if p else 1.
        recall = inter / t if t else 1.
        accuracies.append(inter / union)
        precisions.append(precision)
        recalls.append(recall)
        f1.append(F1(precision, recall))
    return avg(accuracies), avg(precisions), avg(recalls), avg(f1)
