# SuperKart Sales Forecasting - Flask backend API
import joblib
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify

# Initialise the Flask application
superkart_api = Flask("SuperKart Sales Predictor")

# Load the serialized pipeline (preprocessing + model) once at start-up
model = joblib.load("superkart_model.joblib")

# Category levels seen during training (used to flag unsupported inputs)
_cat = model.named_steps["preprocessor"].named_transformers_["cat"]
_cat_cols = model.named_steps["preprocessor"].transformers_[1][2]
KNOWN_LEVELS = {c: set(map(str, lv)) for c, lv in zip(_cat_cols, _cat.named_steps["encoder"].categories_)}

# Features expected by the model, in training order
FEATURES = [
    "Product_Weight", "Product_Sugar_Content", "Product_Allocated_Area", "Product_MRP",
    "Store_Size", "Store_Location_City_Type", "Store_Type", "Product_Id_char",
    "Store_Age_Years", "Product_Type_Category",
]
NUMERIC = ["Product_Weight", "Product_Allocated_Area", "Product_MRP", "Store_Age_Years"]


def prepare(df):
    """Validate columns and coerce types before prediction."""
    missing = [c for c in FEATURES if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required feature(s): {missing}")
    df = df[FEATURES].copy()
    for c in NUMERIC:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


@superkart_api.get("/")
def home():
    """Health check endpoint."""
    return "Welcome to the SuperKart Sales Prediction API!"


@superkart_api.post("/v1/predict")
def predict_sales():
    """Online inference: predict sales for a single product-store record sent as JSON."""
    try:
        data = request.get_json(force=True)
        sample = prepare(pd.DataFrame([data]))
        prediction = float(model.predict(sample)[0])
        result = {"prediction": round(prediction, 2)}
        # Flag categories not seen in training: the model still scores them, but they are unreliable
        unseen = {c: str(sample[c].iloc[0]) for c in KNOWN_LEVELS if str(sample[c].iloc[0]) not in KNOWN_LEVELS[c]}
        if unseen:
            result["warning"] = f"Unseen category value(s) {unseen}; prediction may be unreliable"
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@superkart_api.post("/v1/predictbatch")
def predict_sales_batch():
    """Batch inference: predict sales for every row of an uploaded CSV file."""
    try:
        file = request.files.get("file")
        if file is None:
            return jsonify({"error": "No CSV file uploaded under form field 'file'"}), 400
        batch = prepare(pd.read_csv(file))
        predictions = np.round(model.predict(batch).astype(float), 2)
        # {row_index: predicted_sales}
        return jsonify({str(i): float(p) for i, p in zip(batch.index, predictions)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    superkart_api.run(host="0.0.0.0", port=7860, debug=False)
