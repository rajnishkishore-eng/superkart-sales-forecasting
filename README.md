# SuperKart Sales Forecasting — Model Deployment

SuperKart is a retail chain running supermarkets and food marts in Tier 1, 2 and 3 cities. This project predicts
**`Product_Store_Sales_Total`** (the revenue one product brings in at one store) from product and store attributes, so
the business can plan inventory and regional sales strategy for the next quarter.

The repository contains:

- the full analysis notebook (EDA → preprocessing → model building → hyperparameter tuning → model selection → serialization),
- a **Flask REST API** (backend) that serves the serialized scikit-learn pipeline,
- a **Streamlit web app** (frontend) for single and batch predictions,
- a **Docker Compose** setup that runs both containers in **GitHub Codespaces**.

---

## Directory Structure

```
SuperKart_Project/
├── README.md                          # This file
├── docker-compose.yml                 # Runs the backend + frontend containers together
├── .gitignore
├── SuperKart_Sales_Forecasting.ipynb  # Full analysis & modelling notebook
├── SuperKart_Sales_Forecasting.html   # HTML export of the executed notebook (submission file)
├── model_metrics.json                 # Metrics of every model that was trained
├── backend_files/                     # Flask API (port 7860)
│   ├── app.py                         # API: GET /, POST /v1/predict, POST /v1/predictbatch
│   ├── requirements.txt               # Backend dependencies
│   ├── Dockerfile                     # python:3.11-slim + gunicorn
│   └── superkart_model.joblib         # Serialized best model (Random Forest pipeline, compressed)
└── frontend_files/                    # Streamlit UI (port 8501)
    ├── streamlit_app.py               # Two tabs: Single Prediction, Batch Prediction
    ├── requirements.txt               # Frontend dependencies
    └── Dockerfile                     # python:3.11-slim + streamlit
```

---

## Model File

`backend_files/superkart_model.joblib` is the serialized best pipeline (preprocessing + Random Forest), saved with
joblib compression (~14 MB). It is included in the repo, so the backend container builds without any extra steps.
Re-running the notebook regenerates it.

---

## Model Performance Summary

Main metric: **RMSE** (lower is better). RMSE is in the same unit as revenue and penalizes large errors more heavily,
and large errors are the ones that cause costly over- or under-stocking. R², MAE and MAPE are reported as well.

| Model | Train RMSE | Test RMSE | Test R² | Test MAE | Test MAPE |
|---|---|---|---|---|---|
| **Random Forest (selected)** | 107.54 | **286.83** | **0.928** | 109.69 | 3.9% |
| XGBoost | 131.92 | 302.46 | 0.920 | 134.13 | 5.0% |
| Tuned Random Forest | 113.73 | 305.76 | 0.918 | 149.78 | 5.7% |
| Tuned XGBoost | 180.45 | 288.80 | 0.927 | 118.78 | 4.3% |

The **Random Forest** pipeline had the lowest test RMSE, so it was serialized as `superkart_model.joblib`. Tuned XGBoost
came a close second with a smaller train/test gap. All values come from `model_metrics.json`.

---

## Prerequisites

- **Docker** (pre-installed in GitHub Codespaces)
- **Docker Compose** (pre-installed in GitHub Codespaces as `docker-compose` / `docker compose`)
- A **GitHub account**
- **GitHub Codespaces** access (the free monthly quota is enough)

---

## Deploying on GitHub Codespaces (step by step)

1. **Get the code into a GitHub repository.** You can fork or clone this repository, or create a new GitHub repository
   and push this folder's contents to it.
2. **Open it in Codespaces.** On the repository page, click **Code → Codespaces → Create codespace on main**.
3. **Build and start both containers.** In the Codespace terminal, run:
   ```bash
   docker-compose up --build -d
   # check that both containers are running
   docker-compose ps
   docker-compose logs -f superkart-backend   # Ctrl+C to stop following logs
   ```
4. **Make the ports public.** Open the **Ports** tab (next to Terminal), right-click port **7860** and choose
   **Port Visibility → Public**. Do the same for port **8501**.
5. **Copy the forwarded URL for port 7860** (Flask API), e.g.
   `https://<codespace-name>-7860.app.github.dev`
6. **Copy the forwarded URL for port 8501** (Streamlit UI), e.g.
   `https://<codespace-name>-8501.app.github.dev`. Open it in a browser to use the app.
7. **Update the notebook.** In `SuperKart_Sales_Forecasting.ipynb`, set the API base URL to the port 7860 URL and
   re-run the inference cells:
   ```python
   model_root_url = "https://<codespace-name>-7860.app.github.dev"
   ```

> The frontend container talks to the backend over the internal Docker network (`BACKEND_URL=http://superkart-backend:7860`),
> so the Streamlit app works even when port 7860 is private. Port 7860 only needs to be public for calls from outside the
> Codespace, such as the notebook or `curl`.
>
> Codespaces stop after a period of inactivity. When you restart one, run `docker-compose up -d` again and re-check the
> port visibility. The forwarded URLs stay the same for the same Codespace.

To stop everything: `docker-compose down`.

---

## API Documentation

Base URL: `http://localhost:7860` (inside the Codespace) or the public forwarded URL for port 7860.

### `GET /` — Health check

Returns a plain-text welcome message: `Welcome to the SuperKart Sales Prediction API!`

### `POST /v1/predict` — Single prediction

**Body:** JSON with all model features. The API expects the **engineered** features used during training:

| Field | Type | Allowed values / notes |
|---|---|---|
| `Product_Weight` | float | e.g. `12.66` |
| `Product_Sugar_Content` | string | `Low Sugar`, `Regular`, `No Sugar` |
| `Product_Allocated_Area` | float | ratio, e.g. `0.027` |
| `Product_MRP` | float | e.g. `117.08` |
| `Store_Size` | string | `High`, `Medium`, `Small` |
| `Store_Location_City_Type` | string | `Tier 1`, `Tier 2`, `Tier 3` |
| `Store_Type` | string | `Departmental Store`, `Food Mart`, `Supermarket Type1`, `Supermarket Type2` |
| `Product_Id_char` | string | first two letters of `Product_Id`: `FD`, `NC`, `DR` |
| `Store_Age_Years` | int | `2024 − Store_Establishment_Year` |
| `Product_Type_Category` | string | `Perishables` or `Non Perishables` |

**Example payload**

```json
{
  "Product_Weight": 12.66,
  "Product_Sugar_Content": "Low Sugar",
  "Product_Allocated_Area": 0.027,
  "Product_MRP": 117.08,
  "Store_Size": "Medium",
  "Store_Location_City_Type": "Tier 2",
  "Store_Type": "Supermarket Type2",
  "Product_Id_char": "FD",
  "Store_Age_Years": 15,
  "Product_Type_Category": "Perishables"
}
```

**Response:** `{"prediction": 2906.4}`. If a category value was not seen during training, a `"warning"` key is added.
Invalid input returns HTTP 400 with `{"error": "..."}`.

### `POST /v1/predictbatch` — Batch prediction

**Body:** `multipart/form-data` with the CSV file under the form field name **`file`**.

**Response:** JSON that maps each row index to its predicted sales, e.g. `{"0": 2906.4, "1": 3518.07, ...}`.

---

## Example `curl` Commands

```bash
API=http://localhost:7860          # or https://<codespace-name>-7860.app.github.dev

# Health check
curl $API/

# Single prediction
curl -X POST $API/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"Product_Weight": 12.66, "Product_Sugar_Content": "Low Sugar", "Product_Allocated_Area": 0.027,
       "Product_MRP": 117.08, "Store_Size": "Medium", "Store_Location_City_Type": "Tier 2",
       "Store_Type": "Supermarket Type2", "Product_Id_char": "FD", "Store_Age_Years": 15,
       "Product_Type_Category": "Perishables"}'

# Batch prediction (CSV upload, field name "file")
curl -X POST $API/v1/predictbatch -F "file=@batch_input.csv"
```

---

## Using the Streamlit UI

Open the forwarded URL for port **8501**. The app has two tabs:

1. **Single Prediction:** fill in the product and store details with the inputs and dropdowns, then click **Predict Sales**.
   The app sends the record to `/v1/predict` and shows the forecast revenue.
2. **Batch Prediction:** upload a CSV file and click **Predict Batch**. The file is sent to `/v1/predictbatch`, the
   predictions appear in a table, and you can save them with **Download predictions**.

### Batch CSV — required columns

The CSV must contain these columns. Extra columns are ignored.

```
Product_Weight, Product_Sugar_Content, Product_Allocated_Area, Product_MRP,
Store_Size, Store_Location_City_Type, Store_Type, Product_Id_char,
Store_Age_Years, Product_Type_Category
```

If you start from raw SuperKart data, derive the engineered columns the same way the notebook does:

```python
df["Product_Id_char"] = df["Product_Id"].str[:2]
df["Store_Age_Years"] = 2024 - df["Store_Establishment_Year"]
perishables = ["Dairy", "Meat", "Seafood", "Fruits and Vegetables", "Breakfast",
               "Frozen Foods", "Baking Goods", "Breads"]
df["Product_Type_Category"] = df["Product_Type"].apply(
    lambda t: "Perishables" if t in perishables else "Non Perishables")
```

---

## Tech Stack

- **Python 3.11** (`python:3.11-slim` Docker images)
- **scikit-learn 1.6.1:** preprocessing pipeline (ColumnTransformer + OneHotEncoder) and Random Forest
- **XGBoost 2.1.4:** alternative boosting model
- **Flask 3.1** + **Gunicorn 23:** REST API backend
- **Streamlit 1.41:** web frontend
- **pandas / NumPy / joblib:** data handling and model serialization
- **Docker** + **Docker Compose:** containerization, run on **GitHub Codespaces**
