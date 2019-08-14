from sklearn.ensemble import AdaBoostClassifier
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import roc_auc_score

def run_ml(tbl, name):
    pvt = pd.pivot_table(tbl, index='caseid', values='value', columns='parameter', aggfunc='mean')
    pvt['TCO'] = pvt.apply(lambda x: x['capex_'+name]+33.3333*x['opex_'+name], axis=1)
    tco_avg = sum(pvt['TCO'])/len(pvt['TCO'])
    pvt['TCO'] = pvt['TCO'] > tco_avg
    y = pvt['TCO'].astype(int)
    del pvt['capex_'+name], pvt['opex_'+name], pvt['TCO']
    xparams = pvt
    train_X, test_X, train_y, test_y = train_test_split(xparams, y, random_state=1)
    parameters = {
        'learning_rate': [.1, .5, 1],
        'n_estimators': [10, 200, 500]
    }
    clf = GridSearchCV(AdaBoostClassifier(), parameters, cv=10, n_jobs=-1, scoring='roc_auc')
    clf.fit(train_X, train_y)
    b_estimator = clf.best_estimator_
    predictions = clf.predict(test_X)
    score = roc_auc_score(test_y,predictions)
    importances = b_estimator.feature_importances_
    ftable = pd.DataFrame()
    ftable['params']=xparams.columns
    ftable['importance']=importances
    ftable = ftable.sort_values('importance',ascending=False)
    return ftable,score

