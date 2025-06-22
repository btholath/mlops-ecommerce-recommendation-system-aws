import logging
import shap
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

X, y = load_diabetes(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = RandomForestRegressor()
model.fit(X_train, y_train)
logging.info("Model trained.")

explainer = shap.Explainer(model.predict, X_train)
shap_values = explainer(X_test[:10])
logging.info("SHAP values calculated.")

shap.plots.waterfall(shap_values[0])
plt.savefig("shap_waterfall_plot.png")
logging.info("Saved SHAP waterfall plot as 'shap_waterfall_plot.png'")