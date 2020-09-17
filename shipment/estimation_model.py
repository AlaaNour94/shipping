import pickle
import numpy as np
import pandas as pd

from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

np.random.seed(0)

FILE_NAME = 'finalized_model.sav'


def generate_random_dataset(n_samples):
    X, y = make_regression(n_samples=n_samples, n_features=2, n_informative=2, noise=80, random_state=0)
    # Scale X (distance km) to 0..100 range
    X[:, 0] = np.interp(X[:, 0], (X[:, 0].min(), X[:, 0].max()), (0, 100))
    # Scale X (load) to 0..1 range
    X[:, 1] = np.interp(X[:, 1], (X[:, 1].min(), X[:, 1].max()), (0, 1))
    # Scale y (days) to 1..20 range
    y = np.interp(y, (y.min(), y.max()), (1, 20))
    # To dataframe
    return pd.DataFrame({'distance': X[:, 0], 'load': X[:, 1], 'days': y})


def create_save_model():
    data = generate_random_dataset(1000)
    y = data['days']
    X = data[['distance', 'load']]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.2)
    reg = LinearRegression()
    reg.fit(X_train, y_train)
    pickle.dump(reg, open(FILE_NAME, 'wb'))


def predict(distance, system_load):
    model = pickle.load(open(FILE_NAME, 'rb'))
    return model.predict([[distance, system_load]])[0]
