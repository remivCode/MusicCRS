import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn import svm
from sklearn.metrics import classification_report
import re
import joblib

df = pd.read_csv('models/queries_intent.csv')
X_train, X_test, y_train, y_test = train_test_split(df['query'], df['label'], test_size=0.01, random_state=42)

vectorizer = CountVectorizer()
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

clf = svm.SVC(kernel='linear')
clf.fit(X_train_vec, y_train)

y_pred = clf.predict(X_test_vec)
print(classification_report(y_test, y_pred))

joblib.dump(clf, 'models/svm_model.joblib')
joblib.dump(vectorizer, 'models/vectorizer.joblib') 