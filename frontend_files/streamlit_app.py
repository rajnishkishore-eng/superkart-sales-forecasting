# SuperKart Sales Forecasting - Streamlit frontend
import os
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SuperKart Sales Predictor", page_icon="🛒", layout="wide")
st.title("SuperKart Sales Predictor")
st.write("Forecast the total sales revenue of a product in a SuperKart store.")

# Backend URL: environment variable, overridable from the sidebar
default_url = os.getenv("BACKEND_URL", "http://superkart-backend:7860")
BACKEND_URL = st.sidebar.text_input("Backend API URL", value=default_url).rstrip("/")
st.sidebar.caption("Inside the Codespace Docker network use http://superkart-backend:7860; "
                   "from outside use the forwarded port-7860 URL.")

tab_single, tab_batch = st.tabs(["Single Prediction", "Batch Prediction"])

# ---------------- Single prediction ----------------
with tab_single:
    st.subheader("Product details")
    c1, c2 = st.columns(2)
    with c1:
        product_weight = st.number_input("Product Weight", min_value=0.0, max_value=50.0, value=12.66, step=0.01)
        product_sugar = st.selectbox("Product Sugar Content", ["Low Sugar", "Regular", "No Sugar"])
        product_area = st.number_input("Product Allocated Area (ratio)", min_value=0.0, max_value=1.0,
                                       value=0.027, step=0.001, format="%.3f")
        product_mrp = st.number_input("Product MRP", min_value=0.0, max_value=1000.0, value=117.08, step=0.01)
        product_id_char = st.selectbox("Product Id prefix", ["FD", "DR", "NC"],
                                       help="FD = Food, DR = Drinks, NC = Non-Consumables")
    with c2:
        product_category = st.selectbox("Product Type Category", ["Perishables", "Non Perishables"])
        store_size = st.selectbox("Store Size", ["Small", "Medium", "High"], index=1)
        store_city = st.selectbox("Store Location City Type", ["Tier 1", "Tier 2", "Tier 3"], index=1)
        store_type = st.selectbox("Store Type", ["Departmental Store", "Supermarket Type1",
                                                 "Supermarket Type2", "Food Mart"], index=2)
        store_age = st.number_input("Store Age (years)", min_value=0, max_value=100, value=16, step=1)

    payload = {
        "Product_Weight": product_weight,
        "Product_Sugar_Content": product_sugar,
        "Product_Allocated_Area": product_area,
        "Product_MRP": product_mrp,
        "Store_Size": store_size,
        "Store_Location_City_Type": store_city,
        "Store_Type": store_type,
        "Product_Id_char": product_id_char,
        "Store_Age_Years": int(store_age),
        "Product_Type_Category": product_category,
    }

    if st.button("Predict Sales", type="primary"):
        try:
            resp = requests.post(f"{BACKEND_URL}/v1/predict", json=payload, timeout=30)
            if resp.status_code == 200:
                st.success(f"Predicted Product Store Sales Total: **{resp.json()['prediction']:,.2f}**")
            else:
                st.error(f"API error ({resp.status_code}): {resp.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Could not reach the backend at {BACKEND_URL}: {e}")

# ---------------- Batch prediction ----------------
with tab_batch:
    st.subheader("Upload a CSV file")
    st.caption("Required columns: Product_Weight, Product_Sugar_Content, Product_Allocated_Area, Product_MRP, "
               "Store_Size, Store_Location_City_Type, Store_Type, Product_Id_char, Store_Age_Years, "
               "Product_Type_Category")
    uploaded = st.file_uploader("Choose a CSV file", type=["csv"])
    if uploaded is not None:
        batch_df = pd.read_csv(uploaded)
        st.write("Preview:", batch_df.head())
        if st.button("Predict Batch", type="primary"):
            try:
                files = {"file": ("batch.csv", batch_df.to_csv(index=False).encode("utf-8"), "text/csv")}
                resp = requests.post(f"{BACKEND_URL}/v1/predictbatch", files=files, timeout=120)
                if resp.status_code == 200:
                    preds = resp.json()
                    result = batch_df.copy()
                    result["Predicted_Sales"] = [preds[str(i)] for i in range(len(batch_df))]
                    st.success(f"Predicted {len(result)} rows.")
                    st.dataframe(result)
                    st.download_button("Download predictions", result.to_csv(index=False).encode("utf-8"),
                                       "superkart_predictions.csv", "text/csv")
                else:
                    st.error(f"API error ({resp.status_code}): {resp.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Could not reach the backend at {BACKEND_URL}: {e}")
