# backend/ml_pipeline/vertex_ai_pipeline.py

import pandas as pd
import numpy as np
import logging
import os
import joblib # For saving/loading StandardScaler
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import random # NEW: For simulating historical data/decisions
import asyncio # NEW: For async operations

# Make Keras optional
try:
    import keras # NEW: For Keras model loading
    from keras import Model, layers # NEW: For type hinting and model building
    KERAS_AVAILABLE = True
except ImportError:
    KERAS_AVAILABLE = False
    keras = None
    Model = None
    layers = None
    logger = logging.getLogger(__name__)
    logger.warning("Keras not available. Deep learning features will be disabled.")

from sklearn.preprocessing import StandardScaler # NEW: For loading scaler

# Import components from our ML pipeline
from backend.ml_pipeline.feature_engineer import FeatureEngineer
from backend.ml_pipeline.model_trainer import ModelTrainer
from backend.ml_pipeline.model_predictor import MLModelPredictor

# Import data sourcing components
from backend.data_sourcing.data_loader import get_market_data # For fetching market data
from backend.fundamental_analysis.economic_calendar.manager import EconomicCalendarManager # For economic events
from backend.fundamental_analysis.economic_calendar.defines import EconomicEvent, ImpactLevel, EventType # NEW: for mock events
from backend.fundamental_analysis.news_sourcing.news_api_client import NewsAPIClient # NEW: for mock news history
from backend.fundamental_analysis.news_sentiment_analyzer import NewsSentimentAnalyzer # NEW: for mock news history
from backend.multi_agent.priv_agent_protocol import TradeAction # NEW: for mock trade decisions


logger = logging.getLogger(__name__)

# --- Global Components (Initialize once for the pipeline script) ---
feature_engineer = FeatureEngineer()
model_trainer = ModelTrainer()
# The predictor will load the 'live' model
model_predictor = MLModelPredictor(model_path="models/current_live_model") # Path to the currently deployed model

# Assuming economic_calendar_manager is initialized elsewhere or within pipeline
try:
    from backend.main import economic_calendar_manager as global_economic_calendar_manager
except ImportError:
    logger.warning("WARNING: economic_calendar_manager not found from main. Initializing locally for pipeline testing.")
    ECONOMIC_CALENDAR_URL = "https://www.dailyfx.com/economic-calendar"
    global_economic_calendar_manager = EconomicCalendarManager(calendar_url=ECONOMIC_CALENDAR_URL)

# --- Configuration Constants for the Pipeline ---
MODEL_SAVE_BASE_DIR = "models/trained_models"
LIVE_MODEL_DIR = "models/current_live_model"
TRAINING_DATA_PERIOD_DAYS = 365 * 2 # Fetch 2 years of data for training
PREDICTION_TARGET_COLUMN = 'target_future_direction' # Must match FeatureEngineer's target
MIN_TRAINING_SAMPLES = 500 # Minimum rows in features_df to attempt training
MIN_MODEL_IMPROVEMENT_ACCURACY = 0.01 # Min accuracy % improvement for new model to replace old


async def run_training_pipeline( # Make async
    symbol: str = "EURUSD",
    timeframe: str = "daily",
    dry_run: bool = False # If true, runs logic but doesn't save/deploy
) -> Dict[str, Any]:
    """
    Executes Priv's end-to-end machine learning training pipeline.
    This function represents the logic that would be orchestrated by Vertex AI.
    It now incorporates "Missed Opportunity Feedback" data.

    Args:
        symbol (str): The trading symbol to train the model for.
        timeframe (str): The timeframe of the market data (e.g., "daily", "H4").
        dry_run (bool): If True, runs logic but doesn't save/deploy models.

    Returns:
        Dict[str, Any]: A summary of the pipeline run, including new model metrics.
    """
    logger.info(f"--- Priv's ML Training Pipeline Started for {symbol} ({timeframe}) ---")
    pipeline_summary = {
        "status": "started",
        "symbol": symbol,
        "timeframe": timeframe,
        "run_datetime": datetime.now().isoformat(),
        "data_fetched": False,
        "features_generated": False,
        "model_trained": False,
        "model_evaluated": False,
        "model_deployed": False,
        "current_live_model_accuracy": None,
        "new_model_accuracy": None,
        "new_model_metrics": {}
    }

    # --- Step 1: Fetch Latest Historical Market Data ---
    logger.info(f"Step 1: Fetching {TRAINING_DATA_PERIOD_DAYS} days of historical data for {symbol}...")
    try:
        start_date_data = datetime.now() - timedelta(days=TRAINING_DATA_PERIOD_DAYS)
        market_data_df = get_market_data(symbol=symbol, timeframe=timeframe, start_date=start_date_data)
        if market_data_df.empty:
            raise ValueError("Fetched market data is empty.")
        pipeline_summary["data_fetched"] = True
        logger.info(f"Fetched {len(market_data_df)} bars of market data.")
    except Exception as e:
        logger.error(f"Priv: Failed to fetch market data: {e}", exc_info=True)
        pipeline_summary["status"] = "failed_data_fetch"
        return pipeline_summary

    # --- Step 2: Fetch Historical Economic Events ---
    logger.info("Step 2: Fetching historical economic events...")
    try:
        economic_events_list = global_economic_calendar_manager.get_events(
            start_time=start_date_data, # Use data start date
            end_time=datetime.now(),
            refresh_if_stale=True
        )
        economic_events_dicts = [event.model_dump() if hasattr(event, 'model_dump') else event for event in economic_events_list]
        logger.info(f"Fetched {len(economic_events_dicts)} economic events.")
    except Exception as e:
        logger.warning(f"Priv: Could not fetch historical economic events: {e}. Proceeding without them.", exc_info=True)
        economic_events_dicts = []

    # --- Step 3: Simulate Historical News Analysis Results & Trade Decisions ---
    logger.info("Step 3: Simulating historical news analysis results and trade decisions (for missed opportunity feedback)...")
    
    historical_news_analysis_results_for_fe = {}
    historical_trade_decisions_for_fe = {}
    
    # Iterate through the market data DataFrame's index (timestamps) to simulate historical contexts
    for i, timestamp in enumerate(market_data_df.index):
        # Mock news analysis results
        mock_news_analysis_for_bar = {
            "sentiment": random.choice(["positive", "negative", "neutral"]),
            "market_impact": "high" if random.random() < 0.1 else "none", # 10% chance of high impact
            "title": f"Mock News at {timestamp.isoformat()}",
            "reasoning": "Simulated news analysis for training."
        }
        historical_news_analysis_results_for_fe[timestamp] = mock_news_analysis_for_bar

        # Mock trade decisions (executed, rejected, held, etc.)
        # This is crucial for 'missed opportunity' features.
        # Assume Priv had a signal; this logic should match _make_autonomous_trade_decision
        # For simplicity, if fuzzy strength > 70, it's a signal.
        mock_fuzzy_signal_strength = random.uniform(0, 100) # Simplified signal
        mock_fuzzy_recommendation = "HOLD"
        if mock_fuzzy_signal_strength > 70: mock_fuzzy_recommendation = "BUY"
        elif mock_fuzzy_signal_strength < -70: mock_fuzzy_recommendation = "SELL"

        # Simulate execution/rejection based on some probability
        if mock_fuzzy_recommendation in ["BUY", "SELL"] and random.random() < 0.8: # 80% of strong signals were executed
            historical_trade_decisions_for_fe[timestamp] = {"action": mock_fuzzy_recommendation, "trade_id": f"sim_trade_{i}", "regulatory_check": "compliant", "ethical_check": "compliant", "arbitration_outcome": mock_fuzzy_recommendation}
        elif mock_fuzzy_recommendation in ["BUY", "SELL"] and random.random() < 0.1: # 10% chance it was rejected by governance
             historical_trade_decisions_for_fe[timestamp] = {"action": mock_fuzzy_recommendation, "reason": "Regulatory rejected", "regulatory_check": "non_compliant", "ethical_check": "compliant", "arbitration_outcome": "REJECTED"}
        else: # The rest are 'missed' opportunities or holds, due to other filters
             historical_trade_decisions_for_fe[timestamp] = {"action": "HOLD", "reason": "Simulated hold/missed", "regulatory_check": "compliant", "ethical_check": "compliant", "arbitration_outcome": "HOLD"}
        
    logger.info(f"Simulated {len(historical_news_analysis_results_for_fe)} historical news analyses and {len(historical_trade_decisions_for_fe)} trade decisions.")


    # --- Step 4: Generate Features ---
    logger.info("Step 4: Generating features for model training, including missed opportunity context...")
    try:
        # AnalyticsEngine.calculate_indicators needs to be run on the full historical_data_df to produce
        # comprehensive analysis_results for FeatureEngineer.
        from backend.support_ai.analytics_engine import AnalyticsEngine
        analytics_engine_instance = AnalyticsEngine()
        
        # Run full analysis on the entire historical dataset once.
        # The FE then extracts specific series or looks up by timestamp.
        historical_analysis_full_output = analytics_engine_instance.calculate_indicators(market_data_df)
        
        # FeatureEngineer needs `analysis_results_history` keyed by timestamp.
        # Our `analytics_engine_instance.calculate_indicators` returns a single dict with full series, not indexed by bar.
        # This is a conceptual bridge for training data.
        # For this pipeline, we will pass the results for the primary symbol.
        
        # For `generate_features`, `analysis_results_history` is expected to be `Dict[datetime, Dict[str, Any]]`.
        # This requires `calculate_indicators` to return results *per bar* for historical data.
        # Or, we manually construct `analysis_results_history` from `market_data_df`
        # and `historical_analysis_full_output` (which contains series).
        
        # Simplified mock for `analysis_results_history` to satisfy `feature_engineer` signature
        # This requires `analytics_engine.py` to be enhanced to yield per-bar analysis for training data generation.
        mock_analysis_results_history_for_fe_input = {}
        for index, row in market_data_df.iterrows():
            # Reconstruct per-bar analysis info for FE input based on the full series output
            # This is a conceptual step.
            if symbol in historical_analysis_full_output:
                bar_analysis = {}
                for key, val_series in historical_analysis_full_output[symbol].items():
                    if isinstance(val_series, np.ndarray) and len(val_series) == len(market_data_df):
                        # Get value at this specific timestamp (or corresponding index)
                        bar_analysis[key] = val_series[market_data_df.index.get_loc(timestamp)]
                    elif isinstance(val_series, dict): # For nested dicts like wso_wro_levels
                        bar_analysis[key] = val_series # For simplicity, take the whole dict. Needs refinement.
                    else:
                         bar_analysis[key] = val_series # Direct value if not a series

                mock_analysis_results_history_for_fe_input[timestamp] = {symbol: bar_analysis}

        features_df = feature_engineer.generate_features(
            market_data_df=market_data_df,
            analysis_results_history=mock_analysis_results_history_for_fe_input, # Pass the mock historical analysis for FE
            economic_events=economic_events_dicts,
            news_analysis_results_history=historical_news_analysis_results_for_fe, # Pass simulated historical news
            trade_decisions_history=historical_trade_decisions_for_fe, # Pass simulated historical decisions
            primary_symbol=symbol
        )
        if features_df.empty or PREDICTION_TARGET_COLUMN not in features_df.columns:
            raise ValueError("Generated features DataFrame is empty or missing target column.")
        if len(features_df) < MIN_TRAINING_SAMPLES:
            raise ValueError(f"Not enough valid samples ({len(features_df)}) for training. Minimum: {MIN_TRAINING_SAMPLES}")

        pipeline_summary["features_generated"] = True
        logger.info(f"Priv: Generated {len(features_df)} feature rows for training.")
    except Exception as e:
        logger.error(f"Priv: Failed to generate features: {e}", exc_info=True)
        pipeline_summary["status"] = "failed_feature_generation"
        return pipeline_summary

    # --- Step 5: Train New Model ---
    logger.info("Step 5: Training new model...")
    new_model_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_model_dir = os.path.join(MODEL_SAVE_BASE_DIR, new_model_timestamp) # Corrected new_model_path to a directory
    try:
        new_model, new_model_metrics, scaler = model_trainer.train_model(features_df, target_column=PREDICTION_TARGET_COLUMN) # Get scaler too
        pipeline_summary["model_trained"] = True
        pipeline_summary["new_model_metrics"] = new_model_metrics
        pipeline_summary["new_model_accuracy"] = new_model_metrics.get('accuracy', 0.0)
        logger.info(f"Priv: New model trained. Accuracy: {pipeline_summary['new_model_accuracy']:.4f}")
    except ValueError as e:
        logger.error(f"Priv: Model training failed due to data issues: {e}")
        pipeline_summary["status"] = "failed_training_data_issue"
        return pipeline_summary
    except Exception as e:
        logger.error(f"Priv: Model training failed: {e}", exc_info=True)
        pipeline_summary["status"] = "failed_training"
        return pipeline_summary

    # --- Step 6: Evaluate New Model vs. Current Live Model ---
    logger.info("Step 6: Evaluating new model vs. current live model...")
    pipeline_summary["model_evaluated"] = True
    current_live_model_accuracy = 0.0

    if os.path.exists(LIVE_MODEL_DIR) and os.path.exists(os.path.join(LIVE_MODEL_DIR, "model.h5")):
        try:
            # Instantiate MLModelPredictor with the LIVE_MODEL_DIR to load its model and scaler
            live_model_predictor_instance = MLModelPredictor(model_path=LIVE_MODEL_DIR)
            
            # To evaluate current model on the same data, we need X_test, y_test from model_trainer.
            # This means `model_trainer.train_model` should return X_test, y_test.
            # For this pipeline, we will assume a conceptual stored accuracy or re-evaluate on a mock test set.
            
            # For demonstration, we will assume a conceptual method to retrieve the live model's accuracy.
            # A real Vertex AI pipeline would handle this by versioning datasets and models.
            current_live_model_accuracy = live_model_predictor_instance.get_last_known_accuracy_from_metadata() # Conceptual function
            pipeline_summary["current_live_model_accuracy"] = current_live_model_accuracy
            logger.info(f"Priv: Current live model accuracy (conceptual): {current_live_model_accuracy:.4f}")

            if pipeline_summary["new_model_accuracy"] > current_live_model_accuracy + MIN_MODEL_IMPROVEMENT_ACCURACY:
                logger.info(f"Priv: New model ({pipeline_summary['new_model_accuracy']:.4f}) shows significant improvement over live model ({current_live_model_accuracy:.4f}).")
                should_deploy = True
            else:
                logger.info(f"Priv: New model ({pipeline_summary['new_model_accuracy']:.4f}) does not show significant improvement over live model ({current_live_model_accuracy:.4f}).")
                should_deploy = False
        except Exception as e:
            logger.error(f"Priv: Error evaluating current live model: {e}. Skipping new model deployment.", exc_info=True)
            should_deploy = False
            pipeline_summary["current_live_model_accuracy"] = "Error"
    else:
        logger.info("Priv: No live model found. New model will be deployed.")
        should_deploy = True
    
    # --- Step 7: Deploy New Model (if improved or no live model) ---
    if should_deploy and not dry_run:
        logger.info("Step 7: Deploying new model...")
        try:
            # Save the new model and scaler using ModelTrainer's save_model
            await asyncio.to_thread(model_trainer.save_model, new_model, new_model_dir, scaler) # Save to new_model_dir
            
            # Update the symlink/copy for the live model directory
            if os.path.exists(LIVE_MODEL_DIR):
                import shutil
                shutil.rmtree(LIVE_MODEL_DIR)
            
            import shutil
            shutil.copytree(new_model_dir, LIVE_MODEL_DIR) # Copy the new model's directory
            
            pipeline_summary["model_deployed"] = True
            logger.info(f"Priv: New model successfully deployed to {LIVE_MODEL_DIR}.")
        except Exception as e:
            logger.error(f"Priv: Failed to deploy new model: {e}", exc_info=True)
            pipeline_summary["status"] = "failed_deployment"
    elif dry_run:
        logger.info("Priv: Dry run: Skipping model deployment.")
    else:
        logger.info("Priv: New model not deployed as it did not show significant improvement.")
        
    pipeline_summary["status"] = "completed" if pipeline_summary["status"] == "started" else pipeline_summary["status"]
    logger.info(f"--- Priv's ML Training Pipeline Finished ({pipeline_summary['status']}) ---")
    return pipeline_summary

# Example Usage (to run the pipeline script)
async def main_vertex_ai_pipeline_test():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("\nStarting Priv's ML Training Pipeline example...")
    
    temp_files_to_clean = [
        "temp_reputation_ledger_test.jsonl",
        "backend/governance/ethical_principles.json",
        "backend/governance/compliance_rules.json",
        "temp_reputation_ledger_sim_test.jsonl",
        "backend/governance/simulation/experiment_configs.json",
        "temp_reputation_ledger_trust_test.jsonl",
        "temp_reputation_ledger_sim_test_orchestrator.jsonl"
    ]
    for f_path in temp_files_to_clean:
        if os.path.exists(f_path):
            os.remove(f_path)
            logging.info(f"Priv: Cleaned up temporary file: {f_path}")
    
    # Clean up model directories before running
    if os.path.exists(LIVE_MODEL_DIR):
        import shutil
        shutil.rmtree(LIVE_MODEL_DIR)
        logger.info(f"Priv: Cleaned up old live model from {LIVE_MODEL_DIR}.")
    if os.path.exists(MODEL_SAVE_BASE_DIR):
        import shutil
        shutil.rmtree(MODEL_SAVE_BASE_DIR)
        logger.info(f"Priv: Cleaned up trained models from {MODEL_SAVE_BASE_DIR}.")

    # Mock data source for the pipeline
    data_length = 500
    dates = pd.date_range(start='2023-01-01', periods=data_length, freq='D')
    mock_closes = 100 + np.cumsum(np.random.normal(0, 0.5, data_length))
    mock_opens = mock_closes - np.random.uniform(-0.1, 0.1, data_length)
    mock_highs = np.maximum(mock_opens, mock_closes) + np.random.uniform(0, 0.2, data_length)
    mock_lows = np.minimum(mock_opens, mock_closes) - np.random.uniform(0, 0.2, data_length)
    mock_volumes = np.random.randint(1000, 5000, data_length)
    mock_df = pd.DataFrame({
        'open': mock_opens, 'high': mock_highs, 'low': mock_lows, 'close': mock_closes, 'volume': mock_volumes
    }, index=dates)
    mock_df.index.name = 'timestamp'

    # Patch get_market_data to return our mock_df
    from unittest.mock import patch
    with patch('backend.data_sourcing.data_loader.get_market_data', return_value=mock_df):
        print("\n--- Running a Dry Run of the Pipeline ---")
        results = await run_training_pipeline(symbol="MOCK_SYMBOL", dry_run=True)
        print("\nPipeline Dry Run Summary:")
        for k, v in results.items():
            if k != "new_model_metrics": print(f"  {k}: {v}")
        
        # Ensure a dummy live model exists for comparison in the actual run
        os.makedirs(LIVE_MODEL_DIR, exist_ok=True)
        # Create a dummy model.h5 and scaler.joblib
        if not os.path.exists(os.path.join(LIVE_MODEL_DIR, "model.h5")):
            # Get an example input shape from feature engineer
            example_features_df = feature_engineer.generate_features(mock_df, {}, {}, {}, {}, primary_symbol="MOCK_SYMBOL") # Temporarily pass empty dicts for history
            input_shape = example_features_df.drop(columns=[PREDICTION_TARGET_COLUMN]).shape[1]

            dummy_model = keras.Sequential([layers.Input(shape=(input_shape,)), layers.Dense(3, activation='softmax')])
            dummy_model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
            dummy_model.save(os.path.join(LIVE_MODEL_DIR, "model.h5"))
            
            dummy_scaler = StandardScaler()
            dummy_scaler.fit(np.random.rand(10, input_shape)) 
            joblib.dump(dummy_scaler, os.path.join(LIVE_MODEL_DIR, "scaler.joblib"))
            logger.info(f"Priv: Created dummy live model at {LIVE_MODEL_DIR}.")
        
        # Mock MLModelPredictor.get_last_known_accuracy_from_metadata for predictable tests
        class MockMLPredictorForPipeline(MLModelPredictor):
                        def get_last_known_accuracy_from_metadata(self) -> float:
                                        return 0.5 # Always return 0.5 for test comparison
                                
        # Patch the global model_predictor instance
        global model_predictor
        model_predictor = MockMLPredictorForPipeline(model_path=LIVE_MODEL_DIR)

        print("\n--- Running an Actual Pipeline Run (will attempt to save/deploy) ---")
        results_actual = await run_training_pipeline(symbol="MOCK_SYMBOL", dry_run=False)
        print("\nPipeline Actual Run Summary:")
        for k, v in results_actual.items():
            if k != "new_model_metrics": print(f"  {k}: {v}")

    # Clean up model directories after running
    if os.path.exists(LIVE_MODEL_DIR):
        import shutil
        shutil.rmtree(LIVE_MODEL_DIR)
        logger.info(f"Priv: Cleaned up live model from {LIVE_MODEL_DIR}.")
    if os.path.exists(MODEL_SAVE_BASE_DIR):
        import shutil
        shutil.rmtree(MODEL_SAVE_BASE_DIR)
        logger.info(f"Priv: Cleaned up trained models from {MODEL_SAVE_BASE_DIR}.")
    
    temp_ledger_file = "temp_reputation_ledger_test.jsonl"
    if os.path.exists(temp_ledger_file):
        os.remove(temp_ledger_file)
        logger.info(f"Priv: Cleaned up temporary ledger file: {temp_ledger_file}")