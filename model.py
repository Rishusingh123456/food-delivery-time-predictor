import pandas as pd
from sklearn.linear_model import LinearRegression
import pickle

data = pd.read_csv('dataset.csv')

x = data[['distance', 'prep_time', 'traffic']]
y = data['delivery_time']

model = LinearRegression()
model.fit(x, y)

pickle.dump(model, open('model.pkl', 'wb'))

print("Model trained and saved successfully.")