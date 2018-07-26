import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from modAL.uncertainty import uncertainty_sampling

from src.utils import load_vectorize_data
from src.active_learning import Learner, ScreeningActiveLearner

seed = 123


if __name__ == '__main__':
    predicates = ['C14', 'C23']
    file_name = 'ohsumed_C14_C23_1grams.csv'
    # load and transform data
    X, y_screening, y_predicate = load_vectorize_data(file_name, predicates, seed)

    params = {
        'clf': CalibratedClassifierCV(LinearSVC(class_weight='balanced', random_state=seed)),
        'n_queries': 50,
        'n_instances_query': 50,  # num of instances for labeling for 1 query
        'undersampling_thr': 0.333,
        'seed': seed,
        'init_train_size': 10,
        'sampling_strategy': uncertainty_sampling,
        'p_out': 0.5,
        'lr': 10
    }

    # data_df = []
    k = 10
    skf = StratifiedKFold(n_splits=k, random_state=seed)
    for train_idx, test_idx in skf.split(X, y_screening):
        # split training-test datasets
        X_train, X_test = X[train_idx], X[test_idx]
        y_screening_test = y_screening[test_idx]
        y_predicate_train, y_predicate_test = {}, {}
        for pr in predicates:
            y_predicate_train[pr] = y_predicate[pr][train_idx]
            y_predicate_test[pr] = y_predicate[pr][test_idx]

        # dict of active learners per predicate
        learners = {}
        for pr in predicates:
            learner = Learner(params)
            learner.setup_active_learner(X_train, y_predicate_train[pr], X_test, y_predicate_test[pr])
            learners[pr] = learner

        params['learners'] = learners
        SAL = ScreeningActiveLearner(params)
        n_instances_query = 50
        for i in range(n_instances_query):
            pr = SAL.select_predicate(i)
            query_idx = SAL.query(pr)
            SAL.teach(pr, query_idx)


        # # start active learning
        # df_run = Learner(params).run(X, y, X_test, y_test)
        # data_df.append(df_run)

    # # compute mean and std, and median over k-fold cross validation results
    # df_concat = pd.concat(data_df)
    # by_row_index = df_concat.groupby(df_concat.index)
    # df_means = by_row_index.mean()
    # df_std = by_row_index.std()
    # df_median = by_row_index.median()
    #
    # # form dataframe for printing out in csv
    # df_to_print = df_means
    # df_to_print.columns = ['num_items_queried', 'training_size_mean',
    #                        'proportion_positives_mean', 'precision_mean',
    #                        'recall_mean', 'fbeta_mean', 'loss_mean']
    #
    # df_to_print['training_size_median'] = df_median['training_size']
    # df_to_print['precision_median'] = df_median['precision']
    # df_to_print['recall_median'] = df_median['recall']
    # df_to_print['fbeta_median'] = df_median['fbeta']
    # df_to_print['loss_median'] = df_median['loss']
    #
    # df_to_print['training_size_std'] = df_std['training_size']
    # df_to_print['precision_std'] = df_std['precision']
    # df_to_print['recall_std'] = df_std['recall']
    # df_to_print['fbeta_std'] = df_std['fbeta']
    # df_to_print['loss_std'] = df_std['loss']
    #
    # df_to_print['sampling_strategy'] = params['sampling_strategy'].__name__
    # df_to_print.to_csv('../data/single_classifier_al/screening_al_{}.csv'.format(predicate), index=False)
