import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.svm import LinearSVC
from sklearn.feature_extraction.text import CountVectorizer, \
                                            TfidfTransformer, \
                                            TfidfVectorizer
from modAL.models import ActiveLearner
from sklearn.linear_model import LogisticRegression
from modAL.uncertainty import uncertainty_sampling

seed = 123


# class LinearSVC_proba(LinearSVC):
#
#     def __platt_func(self,x):
#         return 1/(1+np.exp(-x))
#
#     def predict_proba(self, X):
#         f = np.vectorize(self.__platt_func)
#         raw_predictions = self.decision_function(X)
#         platt_predictions = f(raw_predictions)
#         probs = platt_predictions / platt_predictions.sum(axis=1)[:, None]
#         return probs

def get_data(predicate, df):
    X_pos = df.loc[df[predicate] == 1]['tokens'].values
    pos_num = len(X_pos)
#     X_neg = df.loc[df[predicate] == 0]['tokens'].values[:pos_num] # balanced data
    X_neg = df.loc[df[predicate] == 0]['tokens'].values  # imbalanced data
    neg_num = len(X_neg)
    X = np.append(X_pos, X_neg)
    y = np.append(np.ones(pos_num), np.zeros(neg_num))

    return X, y


def do_active_learning(X, y , X_test, y_test, n_queries):
    # initial training data
    train_idx = [1, 2, 3, -1, -2, -3]
    X_train = X[train_idx]
    y_train = y[train_idx]

    # generating the pool
    X_pool = np.delete(X, train_idx, axis=0)
    y_pool = np.delete(y, train_idx)

    # initializing the active learner
    learner = ActiveLearner(
        estimator=LogisticRegression(),
        X_training=X_train, y_training=y_train,
        query_strategy=uncertainty_sampling
    )
    # print('Accuracy before active learning: %f' % learner.score(X_, y_))

    # pool-based sampling
    for idx in range(n_queries):
        query_idx, query_instance = learner.query(X_pool, n_instances=1)
        learner.teach(
            X=X_pool[query_idx].reshape(1, -1),
            y=y_pool[query_idx].reshape(1, )
        )
        # remove queried instance from pool
        X_pool = np.delete(X_pool, query_idx, axis=0)
        y_pool = np.delete(y_pool, query_idx)
        print('Accuracy after query no. %d: %f' % (idx + 1, learner.score(X_, y_)))


if __name__ == '__main__':
    df = pd.read_csv('./data/ohsumed_C14_C23_1grams.csv')
    predicate = 'C14'
    n_queries = 200

    # load data
    X_, y_ = get_data(predicate, df)
    vectorizer = TfidfVectorizer(lowercase=False, max_features=1000, ngram_range=(1, 1))
    X_ = vectorizer.fit_transform(X_).toarray()

    do_active_learning(X_, y_, None, None, n_queries)
