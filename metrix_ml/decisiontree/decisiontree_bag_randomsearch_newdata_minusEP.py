###############################################################################
#
#  imports and set up environment
#
###############################################################################
'''Defining the environment for this class'''
import argparse
import pandas as pd
import os

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import subprocess
import seaborn as sns
import scikitplot as skplt
from sklearn import metrics
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import mean_squared_error
from sklearn.externals import joblib
from sklearn.model_selection import RandomizedSearchCV
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score
from sklearn.metrics import precision_recall_curve, roc_curve
from sklearn.tree import export_graphviz
from datetime import datetime
from sklearn.externals import joblib
from scipy.stats import randint
from sklearn.ensemble import BaggingClassifier

###############################################################################
#
#  define command line arguments
#
###############################################################################

def parse_command_line():
  '''defining the command line input to make it runable'''
  parser = argparse.ArgumentParser(description='Random forest randomized search')
  
  parser.add_argument(
    '--input', 
    type=str, 
    dest="input",
    default="",
    help='The input CSV file')
    
  parser.add_argument(
    '--outdir',
    type=str,
    dest='outdir',
    default='',
    help='Specify output directory')

  args = parser.parse_args()
  if args.input == '':
    parser.print_help()
    exit(0)
  return args

###############################################################################
#
#  load the data from CSV file
#
###############################################################################

def load_metrix_data(csv_path):
  '''load the raw data as stored in CSV file'''
  return pd.read_csv(csv_path)
  
def make_output_folder(outdir):
  names = ['newdata_minusEP', 'bbbb']
  result = []
  for name in names:
    name = os.path.join(outdir, 'decisiontree_bag_randomsearch', name)
    os.makedirs(name, exist_ok=True)
    result.append(name)
  return result

###############################################################################
#
#  class for ML using random forest with randomised search
#
###############################################################################

class DecisionTreeBagRandomSearch(object):
  '''This class is the doing the actual work in the following steps:
     * define smaller data frames: database, man_add, transform
     * split the data into training and test set
     * setup and run a randomized search for best paramaters to define a decsion tree
     * create a new tree with best parameters
     * predict on this new tree with test data and cross-validated training data
     * analyse the predisctions with graphs and stats
  '''
  def __init__(self, metrix, newdata_minusEP, bbbb):
    self.metrix=metrix
    self.newdata_minusEP=newdata_minusEP
    self.prepare_metrix_data()
    self.split_data()
    self.rand_search()
    self.tree_best_params()
    self.predict()
    self.analysis()

  ###############################################################################
  #
  #  creating 3 data frames specific to the three development milestones I had
  #  1--> directly from data processing
  #  2--> after adding protein information
  #  3--> carrying out some further column transformations
  #
  ###############################################################################

  def prepare_metrix_data(self):
    '''Function to create smaller dataframes for directly after dataprocessing, after
       adding some protein information and after carrying out some custom solumn
       transformations.
    ******
    Input: large data frame
    Output: smaller dataframes; database, man_add, transform
    '''
    print('*' *80)
    print('*    Preparing input dataframes metrix_database, metrix_man_add, metrix_transform')
    print('*' *80)

    #database plus manually added data
    attr_newdata_initial = ['IoverSigma', 'cchalf', 'RmergediffI', 'RmergeI', 'RmeasI',
                      'RmeasdiffI', 'RpimdiffI', 'RpimI', 'totalobservations',
                      'totalunique', 'multiplicity', 'completeness', 'lowreslimit',
                      'highreslimit', 'wilsonbfactor', 'anomalousslope',
                      'anomalousCC', 'anomalousmulti', 'anomalouscompl', 'diffI',
                      'diffF', 'f','wavelength', 'sg_number', 'cell_a', 'cell_b', 'cell_c',
                      'cell_alpha', 'cell_beta', 'cell_gamma', 'Vcell', 'solvent_content',
                      'Matth_coeff', 'No_atom_chain', 'No_mol_ASU',
                      'MW_chain', 'sites_ASU']

    attr_newdata_transform = ['IoverSigma', 'cchalf', 'RmergediffI', 'RmergeI', 'RmeasI',
                      'RmeasdiffI', 'RpimdiffI', 'RpimI', 'totalobservations',
                      'totalunique', 'multiplicity', 'completeness', 'lowreslimit',
                      'highreslimit', 'wilsonbfactor', 'anomalousslope',
                      'anomalousCC', 'anomalousmulti', 'anomalouscompl', 'diffI',
                      'diffF', 'f','wavelength', 'wavelength**3', 'wavelength**3/Vcell',
                      'sg_number', 'cell_a', 'cell_b', 'cell_c', 'cell_alpha',
                      'cell_beta', 'cell_gamma','Vcell', 'solvent_content',
                      'Vcell/Vm<Ma>', 'Matth_coeff', 'MW_ASU/sites_ASU/solvent_content',
                      'MW_chain', 'No_atom_chain', 'No_mol_ASU', 'MW_ASU', 'sites_ASU',
                      'MW_ASU/sites_ASU', 'MW_chain/No_atom_chain', 'wilson', 'bragg',
                      'volume_wilsonB_highres', 'IoverSigma/MW_ASU']
                      
#    attr_newdata_transform = ['IoverSigma', 'cchalf', 'RmergediffI', 'RmergeI', 'RmeasI',
#                      'RmeasdiffI', 'RpimdiffI', 'RpimI', 'totalobservations',
#                      'totalunique', 'multiplicity', 'completeness', 'lowreslimit',
#                      'highreslimit', 'wilsonbfactor', 'anomalousslope',
#                      'anomalousCC', 'anomalousmulti', 'anomalouscompl', 'diffI',
#                      'diffF', 'f', 'wavelength',
#                      'sg_number', 'cell_a', 'cell_b', 'cell_c', 'cell_alpha',
#                      'cell_beta', 'cell_gamma','Vcell', 'solvent_content',
#                      'Vcell/Vm<Ma>', 'Matth_coeff', 'MW_ASU/sites_ASU/solvent_content',
#                      'MW_chain', 'No_atom_chain', 'No_mol_ASU', 'MW_ASU', 'sites_ASU',
#                      'MW_ASU/sites_ASU', 'MW_chain/No_atom_chain', 'bragg',
#                      'volume_wilsonB_highres', 'IoverSigma/MW_ASU']

    metrix_newdata_initial = self.metrix[attr_newdata_initial]
    self.X_newdata_initial = metrix_newdata_initial

    metrix_newdata_transform = metrix_newdata_initial.copy()

    with open(os.path.join(self.newdata_minusEP, 'decisiontree_bag_randomsearch.txt'), 'a') as text_file:
      text_file.write('Preparing input data as metrix_transform with following attributes %s \n' %(attr_newdata_initial))

    #column transformation
    #MW_ASU
    metrix_newdata_transform['MW_ASU'] = metrix_newdata_transform['MW_chain'] * metrix_newdata_transform['No_mol_ASU']

    #MW_ASU/sites_ASU
    metrix_newdata_transform['MW_ASU/sites_ASU'] = metrix_newdata_transform['MW_ASU'] / metrix_newdata_transform['sites_ASU']
    
    #IoverSigma/MW_ASU
    metrix_newdata_transform['IoverSigma/MW_ASU'] = metrix_newdata_transform['IoverSigma'] / metrix_newdata_transform['MW_ASU']

    #MW_chain/No_atom_chain
    metrix_newdata_transform['MW_chain/No_atom_chain'] = metrix_newdata_transform['MW_chain'] / metrix_newdata_transform['No_atom_chain']

    #MW_ASU/sites_ASU/solvent_content
    metrix_newdata_transform['MW_ASU/sites_ASU/solvent_content'] = metrix_newdata_transform['MW_ASU/sites_ASU'] / metrix_newdata_transform['solvent_content']

#    #wavelength**3
#    metrix_newdata_transform['wavelength**3'] = metrix_newdata_transform['wavelength'] ** 3

#    #wavelenght**3/Vcell
#    metrix_newdata_transform['wavelength**3/Vcell'] = metrix_newdata_transform['wavelength**3'] / metrix_newdata_transform['Vcell']

    #Vcell/Vm<Ma>
    metrix_newdata_transform['Vcell/Vm<Ma>'] = metrix_newdata_transform['Vcell'] / (metrix_newdata_transform['Matth_coeff'] * metrix_newdata_transform['MW_chain/No_atom_chain'])

    #wilson
    metrix_newdata_transform['wilson'] = -2 * metrix_newdata_transform['wilsonbfactor']

    #bragg
    metrix_newdata_transform['bragg'] = (1 / metrix_newdata_transform['highreslimit'])**2

    #use np.exp to work with series object
    metrix_newdata_transform['volume_wilsonB_highres'] = metrix_newdata_transform['Vcell/Vm<Ma>'] * np.exp(metrix_newdata_transform['wilson'] * metrix_newdata_transform['bragg'])
    
    self.X_newdata_transform = metrix_newdata_transform
    
    #np.isnan(self.X_newdata_transform)
    #print(np.where(np.isnan(self.X_newdata_transform)))
    #self.X_newdata_transform = np.nan_to_num(self.X_newdata_transform)
    self.X_newdata_transform = self.X_newdata_transform.fillna(0)
    
    self.X_newdata_transform = self.X_newdata_transform[['IoverSigma', 'cchalf', 'RmergediffI', 'RmergeI', 'RmeasI',
                      'RmeasdiffI', 'RpimdiffI', 'RpimI', 'totalobservations',
                      'totalunique', 'multiplicity', 'completeness', 'lowreslimit',
                      'highreslimit', 'wilsonbfactor', 'anomalousslope',
                      'anomalousCC', 'anomalousmulti', 'anomalouscompl', 'diffI',
                      'diffF', 'f','wavelength', 'wavelength**3', 'wavelength**3/Vcell',
                      'sg_number', 'cell_a', 'cell_b', 'cell_c', 'cell_alpha',
                      'cell_beta', 'cell_gamma','Vcell', 'solvent_content',
                      'Vcell/Vm<Ma>', 'Matth_coeff', 'MW_ASU/sites_ASU/solvent_content',
                      'MW_chain', 'No_atom_chain', 'No_mol_ASU', 'MW_ASU', 'sites_ASU',
                      'MW_ASU/sites_ASU', 'MW_chain/No_atom_chain', 'wilson', 'bragg',
                      'volume_wilsonB_highres', 'IoverSigma/MW_ASU']]


    with open(os.path.join(self.newdata_minusEP, 'decisiontree_bag_randomsearch.txt'), 'a') as text_file:
      text_file.write('Created the following dataframes: metrix_transform \n')
      text_file.write(str(self.X_newdata_transform.columns)+'\n')

    ###############################################################################
    #
    #  creating training and test set for each of the 3 dataframes
    #
    ###############################################################################

  def split_data(self):
    '''Function which splits the input data into training set and test set.
    ******
    Input: a dataframe that contains the features and labels in columns and the samples
          in rows
    Output: sets of training and test data with an 80/20 split; X_train, X_test, y_train,
            y_test
    '''
    print('*' *80)
    print('*    Splitting data into test and training set with test=20%')
    print('*' *80)
    
    y = self.metrix['EP_success']

#normal split of samples    
#    X_transform_train, X_transform_test, y_train, y_test = train_test_split(self.X_transform, y, test_size=0.2, random_state=42)
 
#stratified split of samples
    X_newdata_transform_train, X_newdata_transform_test, y_train, y_test = train_test_split(self.X_newdata_transform, y, test_size=0.2, random_state=42, stratify=y)
    
    assert self.X_newdata_transform.columns.all() == X_newdata_transform_train.columns.all()

    self.X_newdata_transform_train = X_newdata_transform_train
    self.X_newdata_transform_test = X_newdata_transform_test
    self.y_train = y_train
    self.y_test = y_test

    with open(os.path.join(self.newdata_minusEP, 'decisiontree_bag_randomsearch.txt'), 'a') as text_file:
      text_file.write('Spliting into training and test set 80-20 \n')
      text_file.write('metrix_transform: X_transform_train, X_transform_test \n')
      text_file.write('y(EP_success): y_train, y_test \n')

    ###############################################################################
    #
    #  random search for best parameter combination
    #
    ###############################################################################

  def rand_search(self):
    '''running a randomized search to find the parameter combination for a decision tree
     which gives the best accuracy score'''
    print('*' *80)
    print('*    Running RandomizedSearch for best parameter combination for DecisionTree')
    print('*' *80)

    #create the decision tree
    clf1 = DecisionTreeClassifier(random_state=0, class_weight='balanced')
    tree_clf_rand_bag = BaggingClassifier(base_estimator=clf1, n_jobs=-1, bootstrap=True, random_state=100)#use default base estimator decision tree

    with open(os.path.join(self.newdata_minusEP, 'decisiontree_bag_randomsearch.txt'), 'a') as text_file:
      text_file.write('Created decision tree: tree_clf_rand \n')

    #set up random search
    param_rand = {"base_estimator__criterion": ["gini", "entropy"],#metric to judge reduction of impurity
                  'base_estimator__class_weight': ['balanced', None],
                  'n_estimators': randint(100, 10000),#number of base estimators to use
                  'base_estimator__max_features': randint(2, 48),#max number of features when splitting
                  "base_estimator__min_samples_split": randint(2, 20),#min samples per node to induce split
                  "base_estimator__max_depth": randint(5, 10),#max number of splits to do
                  "base_estimator__min_samples_leaf": randint(1, 20),#min number of samples in a leaf
                  "base_estimator__max_leaf_nodes": randint(10, 20)}#max number of leaves

    with open(os.path.join(self.newdata_minusEP, 'decisiontree_bag_randomsearch.txt'), 'a') as text_file:
      text_file.write('Running random search for the following parameters: %s \n' %param_rand)
      text_file.write('use cv=3, scoring=accuracy \n')

    #building and running the random search
    rand_search = RandomizedSearchCV(tree_clf_rand_bag, param_rand, random_state=5,
                              cv=3, n_iter=500, scoring='accuracy', n_jobs=-1)

    rand_search_transform = rand_search.fit(self.X_newdata_transform_train, self.y_train)
    with open(os.path.join(self.newdata_minusEP, 'decisiontree_bag_randomsearch.txt'), 'a') as text_file:
      text_file.write('Best parameters: ' +str(rand_search_transform.best_params_)+'\n')
      text_file.write('Best score: ' +str(rand_search_transform.best_score_)+'\n')

    base_estimator_dict = rand_search_transform.best_params_.copy()
    base_estimator_dict.pop('n_estimators', None)

    base_estimator_dict["criterion"] = base_estimator_dict.pop('base_estimator__criterion')
    base_estimator_dict['class_weight'] = base_estimator_dict.pop('base_estimator__class_weight')
    base_estimator_dict["min_samples_split"] = base_estimator_dict.pop('base_estimator__min_samples_split')
    base_estimator_dict["max_depth"] = base_estimator_dict.pop('base_estimator__max_depth')
    base_estimator_dict["min_samples_leaf"] = base_estimator_dict.pop('base_estimator__min_samples_leaf')
    base_estimator_dict["max_leaf_nodes"] = base_estimator_dict.pop('base_estimator__max_leaf_nodes')
    base_estimator_dict['max_features'] = base_estimator_dict.pop('base_estimator__max_features')
      
    bag_dict = rand_search_transform.best_params_.copy()
    keysToRemove2 = ("base_estimator__criterion",
                    'base_estimator__class_weight',
                    'base_estimator__max_features',
                    "base_estimator__min_samples_split",
                    "base_estimator__max_depth",
                    "base_estimator__min_samples_leaf",
                    "base_estimator__max_leaf_nodes")
    for key in keysToRemove2:
      bag_dict.pop(key, None)
    
    self.best_params_base_estimator = base_estimator_dict
    self.best_params_bag = bag_dict


    ###############################################################################
    #
    #  creating new tree with best parameter combination and applying bagging
    #
    ###############################################################################

  def tree_best_params(self):
    '''create a new decision tree using the best parameter combination found above'''
    print('*' *80)
    print('*    Building new tree based on best parameter combination and save as pickle')
    print('*' *80)
    
    clf2 = DecisionTreeClassifier(**self.best_params_base_estimator, random_state= 0)
    self.tree_clf_rand_bag_new_transform = BaggingClassifier(clf2, **self.best_params_bag, n_jobs=-1, bootstrap=True, random_state=100)
    self.tree_clf_rand_bag_new_transform.fit(self.X_newdata_transform_train, self.y_train)
    
    attr_newdata_transform = ['IoverSigma', 'cchalf', 'RmergediffI', 'RmergeI', 'RmeasI',
                      'RmeasdiffI', 'RpimdiffI', 'RpimI', 'totalobservations',
                      'totalunique', 'multiplicity', 'completeness', 'lowreslimit',
                      'highreslimit', 'wilsonbfactor', 'anomalousslope',
                      'anomalousCC', 'anomalousmulti', 'anomalouscompl', 'diffI',
                      'diffF', 'f','wavelength', 'wavelength**3', 'wavelength**3/Vcell',
                      'sg_number', 'cell_a', 'cell_b', 'cell_c', 'cell_alpha',
                      'cell_beta', 'cell_gamma','Vcell', 'solvent_content',
                      'Vcell/Vm<Ma>', 'Matth_coeff', 'MW_ASU/sites_ASU/solvent_content',
                      'MW_chain', 'No_atom_chain', 'No_mol_ASU', 'MW_ASU', 'sites_ASU',
                      'MW_ASU/sites_ASU', 'MW_chain/No_atom_chain', 'wilson', 'bragg',
                      'volume_wilsonB_highres', 'IoverSigma/MW_ASU']
    
    
    def feature_importances_pandas(clf, X_train, name, directory):   
      datestring = datetime.strftime(datetime.now(), '%Y%m%d_%H%M')      
      feature_list = []
      for tree in clf.estimators_:
        feature_importances_ls = tree.feature_importances_
        feature_list.append(feature_importances_ls)
        
      df = pd.DataFrame(feature_list, columns=X_train.columns)
      df_mean = df[X_train.columns].mean(axis=0)
      df_std = df[X_train.columns].std(axis=0)
      df_mean.plot(kind='bar', color='b', yerr=[df_std], align="center", figsize=(20,10), rot=90)
      plt.title('Histogram of Feature Importances over all BaggingClassifiers using features %s ' %name)
      plt.xlabel('Features')
      plt.tight_layout()
      plt.savefig(os.path.join(directory, 'feature_importances_overall_bar_plot_rand_bag_'+name+datestring+'.png'))
      plt.close()
      
    feature_importances_pandas(self.tree_clf_rand_bag_new_transform, self.X_newdata_transform_train, 'newdata_minusEP', self.newdata_minusEP)

    def write_pickle(tree, directory, name):
      datestring = datetime.strftime(datetime.now(), '%Y%m%d_%H%M')
      joblib.dump(tree, os.path.join(directory,'best_tree_rand_bag_'+name+datestring+'.pkl'))
      with open(os.path.join(directory, 'decisiontree_bag_randomsearch.txt'), 'a') as text_file:
        text_file.write('Created new decision tree "tree_clf_rand_bag_new_%s" using best parameters \n' %name)
        text_file.write('Creating pickle file for best tree as best_tree_rand_bag_%s.pkl \n' %name)
    
    write_pickle(self.tree_clf_rand_bag_new_transform, self.newdata_minusEP, 'newdata_minusEP')

    def visualise_tree(tree_bag, directory, columns, name):
      datestring = datetime.strftime(datetime.now(), '%Y%m%d_%H%M')
      trees = tree_bag.estimators_
      i_tree = 0
      for tree in trees:
        with open(os.path.join(directory,'tree_clf_rand_bag_new_'+name+datestring+str(i_tree)+'.dot'), 'w') as f:
          export_graphviz(tree, out_file=f, feature_names=columns, rounded=True, filled=True)
          f.close()
        dotfile = os.path.join(directory, 'tree_clf_rand_bag_new_'+name+datestring+str(i_tree)+'.dot')
        pngfile = os.path.join(directory, 'tree_clf_rand_bag_new_'+name+datestring+str(i_tree)+'.png')
        command = ["dot", "-Tpng", dotfile, "-o", pngfile]
        subprocess.check_call(command)
        i_tree = i_tree + 1

      with open(os.path.join(directory, 'decisiontree_bag_randomsearch.txt'), 'a') as text_file:
        text_file.write('Writing DOTfile and convert to PNG for "tree_clf_rand_bag_new_%s" \n' %name)
        text_file.write('DOT filename: tree_clf_rand_bag_new_%s.dot \n' %name)
        text_file.write('PNG filename: tree_clf_rand_bag_new_%s.png \n' %name)
   
    visualise_tree(self.tree_clf_rand_bag_new_transform, self.newdata_minusEP, self.X_newdata_transform_train.columns, 'newdata_minusEP')

    print('*' *80)
    print('*    Getting basic stats for new tree')
    print('*' *80)

    def basic_stats(tree, X_train, directory):
      #distribution --> accuracy
      accuracy_each_cv = cross_val_score(tree, X_train, self.y_train, cv=3, scoring='accuracy')
      accuracy_mean_cv = cross_val_score(tree, X_train, self.y_train, cv=3, scoring='accuracy').mean()
      # calculate cross_val_scoring with different scoring functions for CV train set
      train_roc_auc = cross_val_score(tree, X_train, self.y_train, cv=3, scoring='roc_auc').mean()
      train_accuracy = cross_val_score(tree, X_train, self.y_train, cv=3, scoring='accuracy').mean()
      train_recall = cross_val_score(tree, X_train, self.y_train, cv=3, scoring='recall').mean()
      train_precision = cross_val_score(tree, X_train, self.y_train, cv=3, scoring='precision').mean()
      train_f1 = cross_val_score(tree, X_train, self.y_train, cv=3, scoring='f1').mean()

      with open(os.path.join(directory, 'decisiontree_bag_randomsearch.txt'), 'a') as text_file:
        text_file.write('Get various cross_val_scores to evaluate clf performance for best parameters \n')      
        text_file.write('Accuracy for each of 3 CV folds: %s \n' %accuracy_each_cv)
        text_file.write('Mean accuracy over all 3 CV folds: %s \n' %accuracy_mean_cv)
        text_file.write('ROC_AUC mean for 3-fold CV: %s \n' %train_roc_auc)
        text_file.write('Accuracy mean for 3-fold CV: %s \n' %train_accuracy)
        text_file.write('Recall mean for 3-fold CV: %s \n' %train_recall)
        text_file.write('Precision mean for 3-fold CV: %s \n' %train_precision)
        text_file.write('F1 score mean for 3-fold CV: %s \n' %train_f1)
    
    basic_stats(self.tree_clf_rand_bag_new_transform, self.X_newdata_transform_train, self.newdata_minusEP)

    ###############################################################################
    #
    #  Predicting with test set and cross-validation set using the bets forest
    #
    ###############################################################################

  def predict(self):
    '''do predictions using the best tree an the test set as well as training set with
       10 cross-validation folds and doing some initial analysis on the output'''
    print('*' *80)
    print('*    Predict using new tree and test/train_CV set')
    print('*' *80)

    #try out how well the classifier works to predict from the test set
    #self.y_pred_transform = self.tree_clf_rand_bag_new_transform.predict(self.X_transform_test)
    self.y_pred_transform = self.tree_clf_rand_bag_new_transform.predict(self.X_newdata_transform_test)
    self.y_pred_proba_transform = self.tree_clf_rand_bag_new_transform.predict_proba(self.X_newdata_transform_test)
    with open(os.path.join(self.newdata_minusEP, 'decisiontree_bag_randomsearch.txt'), 'a') as text_file:
      text_file.write('Saving predictions and probabilities for X_transform_test in y_pred_transform and probabilities y_pred_proba_transform\n')

    #alternative way to not have to use the test set
    self.y_train_CV_pred_transform = cross_val_predict(self.tree_clf_rand_bag_new_transform, self.X_newdata_transform_train, self.y_train, cv=3)
    self.y_train_CV_pred_proba_transform = cross_val_predict(self.tree_clf_rand_bag_new_transform, self.X_newdata_transform_train, self.y_train, cv=3, method='predict_proba')
    with open(os.path.join(self.newdata_minusEP, 'decisiontree_bag_randomsearch.txt'), 'a') as text_file:
      text_file.write('Saving predictions and probabilities for X_transform_train with 3-fold CV in y_train_pred_transform \n')

    print('*' *80)
    print('*    Calculate prediction stats')
    print('*' *80)

    def prediction_stats(y_test, y_pred, directory):
      # calculate accuracy
      y_accuracy = metrics.accuracy_score(self.y_test, y_pred)

      # examine the class distribution of the testing set (using a Pandas Series method)
      class_dist = self.y_test.value_counts()

      # calculate the percentage of ones
      # because y_test only contains ones and zeros, we can simply calculate the mean = percentage of ones
      ones = self.y_test.mean()

      # calculate the percentage of zeros
      zeros = 1 - self.y_test.mean()

      # calculate null accuracy in a single line of code
      # only for binary classification problems coded as 0/1
      null_acc = max(self.y_test.mean(), 1 - self.y_test.mean())

      with open(os.path.join(directory, 'decisiontree_bag_randomsearch.txt'), 'a') as text_file:
        text_file.write('Accuracy score or agreement between y_test and y_pred_class: %s \n' %y_accuracy)
        text_file.write('Class distribution for y_test: %s \n' %class_dist)
        text_file.write('Percent 1s in y_test: %s \n' %ones)
        text_file.write('Percent 0s in y_test: %s \n' %zeros)
        text_file.write('Null accuracy in y_test: %s \n' %null_acc)
    
    prediction_stats(self.y_test, self.y_pred_transform, self.newdata_minusEP)

    ###############################################################################
    #
    #  detailed analysis and stats
    #
    ###############################################################################

  def analysis(self):
    '''detailed analysis of the output:
       * create a confusion matrix
       * split the data into TP, TN, FP, FN for test and train_CV
       * determine accuracy score
       * determine classification error
       * determine sensitivity
       * determine specificity
       * determine false-positive rate
       * determine precision
       * determine F1 score
       calculate prediction probabilities and draw plots
       * histogram for probability to be class 1
       * precision-recall curve
       * look for adjustments in classification thresholds
       * ROC curve
       * determine ROC_AUC
       * try different scoring functions for comparison'''
    print('*' *80)
    print('*    Detailed analysis and plotting')
    print('*' *80)

    def conf_mat(y_test, y_train, y_pred, y_train_pred, directory):
      # IMPORTANT: first argument is true values, second argument is predicted values
      # this produces a 2x2 numpy array (matrix)
      conf_mat_test = metrics.confusion_matrix(y_test, y_pred)
      conf_mat_10CV = metrics.confusion_matrix(y_train, y_train_pred)
      def draw_conf_mat(matrix, directory, name):
        datestring = datetime.strftime(datetime.now(), '%Y%m%d_%H%M')
        labels = ['0', '1']      
        ax = plt.subplot()
        sns.heatmap(matrix, annot=True, ax=ax)
        plt.title('Confusion matrix of the classifier')
        ax.set_xticklabels(labels)
        ax.set_yticklabels(labels)
        plt.xlabel('Predicted')
        plt.ylabel('True')
        plt.savefig(os.path.join(directory, 'confusion_matrix_tree_rand_bag_'+name+datestring+'.png'))
        plt.close()

      draw_conf_mat(conf_mat_test, directory, 'test_')
      draw_conf_mat(conf_mat_10CV, directory, 'train_CV_')
      
      TP = conf_mat_test[1, 1]
      TN = conf_mat_test[0, 0]
      FP = conf_mat_test[0, 1]
      FN = conf_mat_test[1, 0]
      
      TP_CV = conf_mat_10CV[1, 1]
      TN_CV = conf_mat_10CV[0, 0]
      FP_CV = conf_mat_10CV[0, 1]
      FN_CV = conf_mat_10CV[1, 0]

      with open(os.path.join(directory, 'decisiontree_bag_randomsearch.txt'), 'a') as text_file:
        text_file.write('confusion matrix using test set: %s \n' %conf_mat_test)
        text_file.write('confusion matrix using 3-fold CV: %s \n' %conf_mat_10CV)
        text_file.write('Slicing confusion matrix for test set into: TP, TN, FP, FN \n')
        text_file.write('Slicing confusion matrix for 3-fold CV into: TP_CV, TN_CV, FP_CV, FN_CV \n')
      
      #calculate accuracy
      acc_score_man_test = (TP + TN) / float(TP + TN + FP + FN)
      acc_score_sklearn_test = metrics.accuracy_score(y_test, y_pred)
      acc_score_man_CV = (TP_CV + TN_CV) / float(TP_CV + TN_CV + FP_CV + FN_CV)
      acc_score_sklearn_CV = metrics.accuracy_score(y_train, y_train_pred)  
      with open(os.path.join(directory, 'decisiontree_bag_randomsearch.txt'), 'a') as text_file:
        text_file.write('Accuracy score: \n')
        text_file.write('accuracy score manual test: %s \n' %acc_score_man_test)
        text_file.write('accuracy score sklearn test: %s \n' %acc_score_sklearn_test)
        text_file.write('accuracy score manual CV: %s \n' %acc_score_man_CV)
        text_file.write('accuracy score sklearn CV: %s \n' %acc_score_sklearn_CV)
        
      #classification error
      class_err_man_test = (FP + FN) / float(TP + TN + FP + FN)
      class_err_sklearn_test = 1 - metrics.accuracy_score(y_test, y_pred)
      class_err_man_CV = (FP_CV + FN_CV) / float(TP_CV + TN_CV + FP_CV + FN_CV)
      class_err_sklearn_CV = 1 - metrics.accuracy_score(y_train, y_train_pred)
      with open(os.path.join(directory, 'decisiontree_bag_randomsearch.txt'), 'a') as text_file:
        text_file.write('Classification error: \n')  
        text_file.write('classification error manual test: %s \n' %class_err_man_test)
        text_file.write('classification error sklearn test: %s \n' %class_err_sklearn_test)
        text_file.write('classification error manual CV: %s \n' %class_err_man_CV)
        text_file.write('classification error sklearn CV: %s \n' %class_err_sklearn_CV)
        
      #sensitivity/recall/true positive rate; correctly placed positive cases  
      sensitivity_man_test = TP / float(FN + TP)
      sensitivity_sklearn_test = metrics.recall_score(y_test, y_pred)
      sensitivity_man_CV = TP_CV / float(FN_CV + TP_CV)
      sensitivity_sklearn_CV = metrics.recall_score(y_train, y_train_pred)
      with open(os.path.join(directory, 'decisiontree_bag_randomsearch.txt'), 'a') as text_file:
        text_file.write('Sensitivity/Recall/True positives: \n')
        text_file.write('sensitivity manual test: %s \n' %sensitivity_man_test)
        text_file.write('sensitivity sklearn test: %s \n' %sensitivity_sklearn_test)
        text_file.write('sensitivity manual CV: %s \n' %sensitivity_man_CV)
        text_file.write('sensitivity sklearn CV: %s \n' %sensitivity_sklearn_CV)
      
      #specificity  
      specificity_man_test = TN / (TN + FP)
      specificity_man_CV = TN_CV / (TN_CV + FP_CV)
      with open(os.path.join(directory, 'decisiontree_bag_randomsearch.txt'), 'a') as text_file:
        text_file.write('Specificity: \n')
        text_file.write('specificity manual test: %s \n' %specificity_man_test)
        text_file.write('specificity manual CV: %s \n' %specificity_man_CV)
      
      #false positive rate  
      false_positive_rate_man_test = FP / float(TN + FP)
      false_positive_rate_man_CV = FP_CV / float(TN_CV + FP_CV)
      with open(os.path.join(directory, 'decisiontree_bag_randomsearch.txt'), 'a') as text_file:
        text_file.write('False positive rate or 1-specificity: \n')
        text_file.write('false positive rate manual test: %s \n' %false_positive_rate_man_test)
        text_file.write('1 - specificity test: %s \n' %(1 - specificity_man_test))
        text_file.write('false positive rate manual CV: %s \n' %false_positive_rate_man_CV)
        text_file.write('1 - specificity CV: %s \n' %(1 - specificity_man_CV))
      
      #precision/confidence of placement  
      precision_man_test = TP / float(TP + FP)
      precision_sklearn_test = metrics.precision_score(y_test, y_pred)
      precision_man_CV = TP_CV / float(TP_CV + FP_CV)
      precision_sklearn_CV = metrics.precision_score(y_train, y_train_pred)
      with open(os.path.join(directory, 'decisiontree_bag_randomsearch.txt'), 'a') as text_file:
        text_file.write('Precision or confidence of classification: \n')
        text_file.write('precision manual: %s \n' %precision_man_test)
        text_file.write('precision sklearn: %s \n' %precision_sklearn_test)
        text_file.write('precision manual CV: %s \n' %precision_man_CV)
        text_file.write('precision sklearn CV: %s \n' %precision_sklearn_CV)
      
      #F1 score; uses precision and recall  
      f1_score_sklearn_test = f1_score(y_test, y_pred)
      f1_score_sklearn_CV = f1_score(y_train, y_train_pred)
      with open(os.path.join(directory, 'decisiontree_bag_randomsearch.txt'), 'a') as text_file:
        text_file.write('F1 score: \n')
        text_file.write('F1 score sklearn test: %s \n' %f1_score_sklearn_test)
        text_file.write('F1 score sklearn CV: %s \n' %f1_score_sklearn_CV)
        
    conf_mat(self.y_test, self.y_train, self.y_pred_transform, self.y_train_CV_pred_transform, self.newdata_minusEP)

    def prediction_probas(tree, X_train, y_train, X_test, y_test, y_pred_proba, y_train_CV_pred_proba, directory, kind): 
      datestring = datetime.strftime(datetime.now(), '%Y%m%d_%H%M')      
      with open(os.path.join(directory, 'decisiontree_bag_randomsearch.txt'), 'a') as text_file:
        text_file.write('Plotting histogram for y_pred_proba_train_CV \n')
        text_file.write('Plotting histogram for y_pred_proba_test \n')
   
      #plot histograms of probabilities  
      def plot_hist_pred_proba(y_pred_proba, name, directory):
        plt.hist(y_pred_proba, bins=20)
        plt.xlim(0,1)
        plt.title('Histogram of predicted probabilities for y_pred_proba_%s to be class 1' %name)
        plt.xlabel('Predicted probability of EP_success')
        plt.ylabel('Frequency')
        plt.savefig(os.path.join(directory, 'hist_pred_proba_tree_rand_bag_'+name+datestring+'.png'))
        plt.close()

      plot_hist_pred_proba(y_train_CV_pred_proba[:, 1], 'train_CV_', directory)
      plot_hist_pred_proba(y_pred_proba[:, 1], 'test_', directory)
      
      with open(os.path.join(directory, 'decisiontree_bag_randomsearch.txt'), 'a') as text_file:
        text_file.write('Getting y_scores for y_pred_proba_train_CV and y_pred_proba_test as y_scores_train_CV and y_scores_test for class 0 and 1\n')

      self.y_scores_ones = y_pred_proba[:, 1]#test data to be class 1
      self.y_scores_CV_ones = y_train_CV_pred_proba[:, 1]#training data to be class 1

      with open(os.path.join(directory, 'decisiontree_bag_randomsearch.txt'), 'a') as text_file:
        text_file.write('Plotting Precision-Recall for y_test and y_scores_test \n')
        text_file.write('Plotting Precision-Recall for y_train and y_scores_train_CV \n')
      
      #plot precision and recall curve
      def plot_precision_recall_vs_threshold(precisions, recalls, thresholds_tree, name, classes, directory):
        plt.plot(thresholds_tree, precisions[:-1], "b--", label="Precision")
        plt.plot(thresholds_tree, recalls[:-1], "g--", label="Recall")
        plt.title('Precsion-Recall plot for for EP_success classifier using %s set to be class %s' %(name, classes))
        plt.xlabel("Threshold")
        plt.legend(loc="upper left")
        plt.ylim([0,1])
        plt.savefig(os.path.join(directory, 'Precision_Recall_tree_rand_bag_'+name+datestring+classes+'.png'))
        plt.close()

     #plot Precision Recall Threshold curve for test set        
      precisions, recalls, thresholds_tree = precision_recall_curve(self.y_test, self.y_scores_ones)
      plot_precision_recall_vs_threshold(precisions, recalls, thresholds_tree, 'test_', '1', directory)
      #plot Precision Recall Threshold curve for CV train set       
      precisions, recalls, thresholds_tree = precision_recall_curve(self.y_train, self.y_scores_CV_ones)
      plot_precision_recall_vs_threshold(precisions, recalls, thresholds_tree, 'train_CV_', '1', directory)
      
      with open(os.path.join(directory, 'decisiontree_bag_randomsearch.txt'), 'a') as text_file:
        text_file.write('Plotting ROC curve for y_test and y_scores_test \n')
        text_file.write('Plotting ROC curve for y_train and y_scores_train_CV \n')

      #IMPORTANT: first argument is true values, second argument is predicted probabilities
      #we pass y_test and y_pred_prob
      #we do not use y_pred_class, because it will give incorrect results without generating an error
      #roc_curve returns 3 objects fpr, tpr, thresholds
      #fpr: false positive rate
      #tpr: true positive rate
    
      #plot ROC curves
      def plot_roc_curve(y_test, y_proba, name, directory):
        skplt.metrics.plot_roc(y_test, y_proba, title='ROC curve %s' %name)
        plt.savefig(os.path.join(directory, 'ROC_curve_skplt_tree_rand_bag_'+name+datestring+'.png'))
        plt.close()
        
      plot_roc_curve(self.y_train, y_train_CV_pred_proba, 'train_CV_', directory)  
      plot_roc_curve(self.y_test, y_pred_proba, 'test_', directory)  
    
      def plot_roc_curve(fpr, tpr, name, classes, directory):
        plt.plot(fpr, tpr, linewidth=2)
        plt.plot([0, 1], [0, 1], 'k--')
        plt.axis([0, 1, 0, 1])
        plt.title('ROC curve for EP_success classifier using %s set for class %s' %(name, classes)) 
        plt.xlabel('False Positive Rate (1 - Specificity)')
        plt.ylabel('True Positive Rate (Sensitivity)')
        plt.grid(True)
        plt.savefig(os.path.join(directory, 'ROC_curve_tree_rand_bag_'+name+datestring+classes+'.png'))
        plt.close()
        
      #ROC curve for test set      
      fpr_1, tpr_1, thresholds_1 = roc_curve(self.y_test, self.y_scores_ones)
      plot_roc_curve(fpr_1, tpr_1, 'test_', '1', directory)
      #ROC curve for 10-fold CV train set      
      fpr_CV_1, tpr_CV_1, thresholds_CV_1 = roc_curve(self.y_train, self.y_scores_CV_ones)
      plot_roc_curve(fpr_CV_1, tpr_CV_1, 'train_CV_', '1', directory)
      
      #calculate the area under the curve to get the performance for a classifier
      # IMPORTANT: first argument is true values, second argument is predicted probabilities
      AUC_test_class1 = metrics.roc_auc_score(self.y_test, self.y_scores_ones)
      AUC_train_class1 = metrics.roc_auc_score(self.y_train, self.y_scores_CV_ones)

      with open(os.path.join(directory, 'decisiontree_bag_randomsearch.txt'), 'a') as text_file:
        text_file.write('AUC for test set class 1: %s \n' %AUC_test_class1)
        text_file.write('AUC for CV train set class 1: %s \n' %AUC_train_class1)
    
    prediction_probas(self.tree_clf_rand_bag_new_transform, self.X_newdata_transform_train, self.y_train, self.X_newdata_transform_test, self.y_test, self.y_pred_proba_transform, self.y_train_CV_pred_proba_transform, self.newdata_minusEP, 'newdata_minusEP')    
    
        
def run():
  args = parse_command_line()
  
  
  ###############################################################################

  #look at the imported data to get an idea what we are working with
  metrix = load_metrix_data(args.input)
  
  newdata_minusEP, bbbb= make_output_folder(args.outdir)

  ###############################################################################

  decision_tree_bag_rand_search = DecisionTreeBagRandomSearch(metrix, newdata_minusEP, bbbb)

