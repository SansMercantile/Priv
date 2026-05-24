# backend/ml_pipeline/model_trainer.py

from __future__ import annotations
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Tuple, Optional, List
import os
import json
import asyncio
import joblib
from backend.utils.logging_config import logger
from datetime import datetime
import sklearn



# Import TensorFlow/Keras for model building
try:
    import tensorflow as tf
    from tensorflow import keras
    from keras import layers
    from keras import Model
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report

except ImportError:
    logger.error("TensorFlow or scikit-learn not found. Please install them: pip install tensorflow scikit-learn")
    tf = None
    keras = None
    layers = None
    train_test_split = None
    StandardScaler = None
    accuracy_score = None
    precision_score = None
    recall_score = None
    f1_score = None
    confusion_matrix = None
    classification_report = None

logger = logging.getLogger(__name__)

class ModelTrainer:
    """
    Manages the training, evaluation, and saving of Priv's machine learning models.
    Now supports richer features for "Missed Opportunity Feedback".
    """
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.scaler: Optional[Any] = None # Store the scaler for consistent preprocessing
        logger.info("Priv's ModelTrainer initialized.")

        if tf is None or keras is None:
            logger.warning("Priv: ModelTrainer initialized without TensorFlow/Keras. Deep learning features will be disabled.")
            self.tf_available = False
        else:
            self.tf_available = True

    def _build_model(self, input_shape: int, num_classes: int = 3) -> Model:
        """
        Defines Priv's default neural network model architecture.
        This is a placeholder; more complex architectures (e.g., LSTMs for time series)
        would be defined here based on data characteristics.

        Args:
            input_shape (int): The number of features (columns) in the input data.
            num_classes (int): Number of output classes (e.g., 3 for Buy/Sell/Hold).

        Returns:
            keras.Model: A compiled Keras model.
        """
        model = keras.Sequential([
            layers.Input(shape=(input_shape,)),
            layers.Dense(128, activation='relu'),
            layers.Dropout(0.3),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.3),
            layers.Dense(num_classes, activation='softmax')
        ])

        model.compile(optimizer='adam',
                      loss='sparse_categorical_crossentropy',
                      metrics=['accuracy'])
        logger.info(f"Priv: Model built with input shape: {input_shape}, output classes: {num_classes}.")
        model.summary(print_fn=logger.info)
        return model

    def train_model(
        self,
        features_df: pd.DataFrame,
        primary_target_column: str = 'target_future_direction', # Primary target for classification
        auxiliary_target_columns: Optional[List[str]] = None, # For future multi-task learning or specialized feedback
        epochs: int = 50,
        batch_size: int = 32,
        validation_split: float = 0.2
    ) -> Tuple[Model, Dict[str, Any], sklearn.preprocessing.StandardScaler]:
        """
        Trains Priv's ML model using the provided features and primary target.
        It's designed to accept features that include "missed opportunity" and decision context.

        Args:
            features_df (pd.DataFrame): DataFrame containing engineered features and target(s).
            primary_target_column (str): The main target variable name (e.g., 'target_future_direction').
            auxiliary_target_columns (Optional[List[str]]): Additional columns that describe outcomes
                                                         or missed opportunities (e.g., 'target_missed_buy_opportunity').
                                                         These can be used for analysis or multi-task learning.
            epochs (int): Number of training epochs.
            batch_size (int): Batch size for training.
            validation_split (float): Fraction of data to use for validation during training.

        Returns:
            Tuple[keras.Model, Dict[str, Any], StandardScaler]: The trained Keras model, its evaluation metrics on the test set, and the fitted scaler.
        """
        if features_df.empty or primary_target_column not in features_df.columns:
            logger.error("Priv: Features DataFrame is empty or primary target column not found. Cannot train model.")
            raise ValueError("Invalid input for model training.")

        # Separate features (X) and primary target (y)
        all_target_columns = [primary_target_column]
        if auxiliary_target_columns:
            all_target_columns.extend(auxiliary_target_columns)
            
        X = features_df.drop(columns=all_target_columns, errors='ignore') # Drop all target columns from features
        y = features_df[primary_target_column]

        # Map target labels: -1 (Sell) -> 0, 0 (Hold) -> 1, 1 (Buy) -> 2 for sparse_categorical_crossentropy
        y_mapped = y.map({-1: 0, 0: 1, 1: 2}).fillna(1).astype(int)

        # Handle NaNs in features (FeatureEngineer should handle most, but ensure here)
        initial_X_rows = len(X)
        X = X.dropna()
        y_mapped = y_mapped.loc[X.index] # Align y with X after dropping NaNs from X
        
        if len(X) < initial_X_rows:
            logger.warning(f"Priv: Dropped {initial_X_rows - len(X)} rows from features_df due to NaNs during training preparation.")

        if X.empty or y_mapped.empty:
            logger.warning("Priv: Features or target DataFrame is empty after NaN removal. Cannot train model.")
            raise ValueError("Empty DataFrame after NaN removal for training.")

        # Ensure all feature columns are numeric before scaling
        for col in X.columns:
            if not pd.api.types.is_numeric_dtype(X[col]):
                logger.warning(f"Priv: Non-numeric feature column '{col}' found. Attempting to convert to numeric or dropping.")
                X[col] = pd.to_numeric(X[col], errors='coerce')
        X = X.dropna(axis=1, how='all') # Drop columns that became all NaN from conversion issues
        X = X.dropna(axis=0) # Drop rows that may have introduced NaNs from conversion

        if X.empty or y_mapped.loc[X.index].empty: # Recheck after potential additional drops
            logger.warning("Priv: Features or target DataFrame became empty after final numeric cleaning. Cannot train model.")
            raise ValueError("Empty DataFrame after final numeric cleaning for training.")

        # Re-align y after potential row drops in X
        y_mapped = y_mapped.loc[X.index]

        # Split data into training and test sets first to preserve indices
        X_train_df, X_test_df, y_train, y_test = train_test_split(
            X, y_mapped, test_size=0.2, random_state=self.random_state, stratify=y_mapped
        )
        logger.info(f"Priv: Data split: Train={len(X_train_df)} samples, Test={len(X_test_df)} samples.")

        # Scale features
        self.scaler = StandardScaler()
        X_train = self.scaler.fit_transform(X_train_df)
        X_test = self.scaler.transform(X_test_df)
        logger.info("Priv: Features scaled using StandardScaler.")

        # Build model - number of classes depends on target definition
        num_classes_in_target = len(y_mapped.unique()) # Determine actual number of unique classes
        model = self._build_model(X_train.shape[1], num_classes=num_classes_in_target)

        # Train model
        logger.info("Priv: Starting model training...")
        history = model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=0 # Suppress verbose output during fit for cleaner logs
        )
        logger.info("Priv: Model training completed.")

        # Evaluate model on test set
        eval_metrics = self.evaluate_model(model, X_test, y_test, y_true_raw_labels=y.loc[y_test.index])

        return model, eval_metrics, self.scaler

    def evaluate_model(self, model: Model, X_test: np.ndarray, y_test: pd.Series, y_true_raw_labels: pd.Series) -> Dict[str, Any]:
        """
        Evaluates the trained model on the test set and returns various metrics.
        Now includes a full classification report for detailed performance analysis.
        """
        logger.info("Priv: Evaluating model on test set...")
        loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
        
        y_pred_probs = model.predict(X_test)
        y_pred_labels = np.argmax(y_pred_probs, axis=1)

        # Reverse map labels for classification report: 0 -> -1, 1 -> 0, 2 -> 1
        reverse_map = {0: -1, 1: 0, 2: 1}
        y_pred_original_labels = pd.Series(y_pred_labels).map(reverse_map)

        # Get full classification report
        class_report = classification_report(y_true_raw_labels, y_pred_original_labels, output_dict=True, zero_division=0)
        
        metrics = {
            'loss': float(loss),
            'accuracy': float(accuracy),
            'precision_weighted': class_report['weighted avg']['precision'],
            'recall_weighted': class_report['weighted avg']['recall'],
            'f1_score_weighted': class_report['weighted avg']['f1-score'],
            'classification_report_full': class_report # Include full report for debugging
        }
        
        # Add per-class metrics if needed (e.g., 'buy_f1', 'sell_f1')
        for label_val in [-1, 0, 1]:
            if str(label_val) in class_report: # Check if class exists in report
                metrics[f'class_{label_val}_precision'] = class_report[str(label_val)]['precision']
                metrics[f'class_{label_val}_recall'] = class_report[str(label_val)]['recall']
                metrics[f'class_{label_val}_f1_score'] = class_report[str(label_val)]['f1-score']

        cm = confusion_matrix(y_true_raw_labels, y_pred_original_labels, labels=[-1, 0, 1]) # Ensure labels order
        metrics['confusion_matrix'] = cm.tolist()
        
        logger.info(f"Priv: Model evaluation metrics: Accuracy={metrics['accuracy']:.4f}, F1={metrics['f1_score_weighted']:.4f}")
        logger.debug(f"Priv: Full Classification Report: {json.dumps(class_report, indent=2)}")
        logger.debug(f"Priv: Confusion Matrix:\n{cm}")
        return metrics

    def save_model(self, model: Model, path: str, scaler: Any, metrics: Optional[Dict[str, Any]] = None):
        """
        Saves the trained Keras model, its associated StandardScaler, and evaluation metrics to the specified path.
        """
        os.makedirs(path, exist_ok=True)
        
        model_save_path = os.path.join(path, "model.h5")
        model.save(model_save_path)
        logger.info(f"Priv: Model saved to: {model_save_path}")

        scaler_save_path = os.path.join(path, "scaler.joblib")
        joblib.dump(scaler, scaler_save_path)
        logger.info(f"Priv: Scaler saved to: {scaler_save_path}")

        if metrics and 'classification_report_full' in metrics:
            report_path = os.path.join(path, "classification_report.json")
            with open(report_path, "w") as f:
                json.dump(metrics["classification_report_full"], f, indent=2)
            logger.info(f"Priv: Classification report saved to: {report_path}")


# Example Usage (for testing ModelTrainer in isolation)
async def main_model_trainer_test():
    logging.basicConfig(level=logging.INFO)

    # Mock features_df (as would be produced by FeatureEngineer)
    data_length = 1000
    num_features = 20
    mock_features = np.random.rand(data_length, num_features) * 10
    # Create a mock target variable for 3 classes: -1 (Sell), 0 (Hold), 1 (Buy)
    mock_targets = np.random.choice([-1, 0, 1], data_length, p=[0.25, 0.5, 0.25]) # More balanced distribution
    
    mock_features_df = pd.DataFrame(mock_features, columns=[f'feature_{i}' for i in range(num_features)])
    mock_features_df['target_future_direction'] = mock_targets # Primary target
    
    # Add mock auxiliary targets/decision features (as FE now provides)
    aux_cols = [
        'target_missed_buy_opportunity',
        'target_missed_sell_opportunity',
        'decision_executed_trade',
        'decision_rejected_by_governance',
        'decision_rejected_by_arbitration'
    ]
    mock_features_df['target_missed_buy_opportunity'] = np.random.choice([0, 1], data_length, p=[0.9, 0.1])
    mock_features_df['target_missed_sell_opportunity'] = np.random.choice([0, 1], data_length, p=[0.9, 0.1])
    mock_features_df['decision_executed_trade'] = np.random.choice([0, 1], data_length, p=[0.8, 0.2])
    mock_features_df['decision_rejected_by_governance'] = np.random.choice([0, 1], data_length, p=[0.95, 0.05])
    mock_features_df['decision_rejected_by_arbitration'] = np.random.choice([0, 1], data_length, p=[0.9, 0.1])

    trainer = ModelTrainer()

    # Train the model
    try:
        trained_model, metrics, scaler = trainer.train_model(
            mock_features_df, 
            epochs=5, 
            validation_split=0.1,
            auxiliary_target_columns=aux_cols
        )
        print("\n--- Model Training & Evaluation Complete ---")
        print(f"Final Accuracy: {metrics['accuracy']:.4f}")
        print(f"Final F1-Score (Weighted): {metrics['f1_score_weighted']:.4f}")
        print(f"Confusion Matrix:\n{np.array(metrics['confusion_matrix'])}")

        # Example of saving the model
        save_dir = "temp_saved_model_trainer"
        await asyncio.to_thread(trainer.save_model, trained_model, save_dir, scaler, metrics) # Use to_thread for sync save in async context
        
        # Clean up
        import shutil
        if os.path.exists(save_dir):
            shutil.rmtree(save_dir)
            logger.info(f"Priv: Cleaned up {save_dir}")

    except ValueError as e:
        logger.error(f"Priv: Training failed: {e}")
    except ImportError:
        logger.error("Priv: Skipping ModelTrainer example due to missing TensorFlow/scikit-learn installation.")

if __name__ == '__main__':
    import asyncio
    asyncio.run(main_model_trainer_test())

