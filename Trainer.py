#trainer.py module
# coding: utf-8
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.utils.class_weight import compute_class_weight
import joblib  # Corrected the import for joblib
import shap
import numpy as np
import logging

class MachineLearning:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.best_params = None
        self.metrics_history = []

    def load_training_data(self, projected_winners, actual_winners):
        """Loads training data from provided data."""
        features = [self._extract_features(winner) for winner in projected_winners]
        labels = [1 if winner == actual else 0 for winner, actual in zip(projected_winners, actual_winners)]
        return features, labels

    def _extract_features(self, winner):
        """Extracts necessary features from winner data."""
        return [winner["team_rank"], winner["point_difference"]]

    def preprocess_data(self, data):
        """Preprocesses provided data using a scaler."""
        return self.scaler.transform(data)

    def evaluate_models(self, data, labels):
        """Evaluates different models and selects the best one."""
        models = {
            "Logistic Regression": LogisticRegression(),
            "SVM": SVC(),
            "Neural Network": MLPClassifier()
        }
        best_score = 0
        best_model = None
        for name, model in models.items():
            score = np.mean(cross_val_score(model, data, labels, cv=5))
            if score > best_score:
                best_score = score
                best_model = model
        self.model = best_model

    def tune_hyperparams(self, data, labels):
        """Tunes hyperparameters of the model using GridSearchCV."""
        if isinstance(self.model, SVC):
            param_grid = {"C": [0.1, 1, 10], "kernel": ["linear", "rbf"]}
            grid_search = GridSearchCV(self.model, param_grid, cv=5)
            grid_search.fit(data, labels)
            self.best_params = grid_search.best_params_
            self.model = grid_search.best_estimator_

    def train_model(self, data, labels, validation_split=0.1, epochs=100, early_stopping_rounds=5, handle_class_imbalance=False):
        """Trains the model on provided data."""
        if handle_class_imbalance and hasattr(self.model, 'class_weight'):
            class_weights = compute_class_weight("balanced", classes=np.unique(labels), y=labels)
        else:
            class_weights = None

        X_train, X_val, y_train, y_val = train_test_split(data, labels, test_size=validation_split, random_state=42)
        best_score = float("-inf")
        stopping_rounds = 0

        for epoch in range(epochs):
            if isinstance(self.model, MLPClassifier):
                self.model.set_params(early_stopping=True, n_iter_no_change=early_stopping_rounds)
                self.model.fit(X_train, y_train)
                break
            else:
                self.model.fit(X_train, y_train, class_weight=class_weights)
                val_score = self.model.score(X_val, y_val)
                if val_score > best_score:
                    best_score = val_score
                    stopping_rounds = 0
                else:
                    stopping_rounds += 1
                    if stopping_rounds >= early_stopping_rounds:
                        logging.info("Early stopping triggered")
                        break

    def incremental_fit(self, new_data, new_labels):
        """Incrementally fits the model on new data."""
        self.model.partial_fit(new_data, new_labels)

    def evaluate_model(self, data, labels, retrain_threshold=None):
        """Evaluates the model on provided data."""
        predictions = self.model.predict(data)
        precision, recall, f1, _ = precision_recall_fscore_support(labels, predictions)
        accuracy = accuracy_score(labels, predictions)
        metrics = {
            "accuracy": accuracy,
            "precision_per_class": precision.tolist(),
            "recall_per_class": recall.tolist(),
            "f1_score_per_class": f1.tolist(),
        }
        self.metrics_history.append(metrics)

        return metrics

    def log_metrics_history(self):
        """Logs the metrics history of the model."""
        logging.info(f"Metrics history: {self.metrics_history}")

    def explain_predictions(self, data):
        """Explains predictions using SHAP values."""
        explainer = shap.Explainer(self.model, data)
        shap_values = explainer(data)
        shap.plots.bar(shap_values)

    def save_model(self, path):
        """Saves the model, scaler and metrics history to provided path."""
        joblib.dump((self.model, self.scaler, self.metrics_history), path)

    def load_model(self, path):
        """Loads the model, scaler and metrics history from provided path."""
        self.model, self.scaler, self.metrics_history = joblib.load(path)
