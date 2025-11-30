import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import joblib
import json
sys.path.insert(0, str(Path(__file__).parent.parent))
import db
from model_loader import model_status, load_model

def get_category_name(category_value):
    category_mapping = {'0': 'Marks Mismatch', '1': 'Absentee Error', '2': 'Missing Grade', '3': 'Calculation Discrepancy', 'Marks Mismatch': 'Marks Mismatch', 'Absentee Error': 'Absentee Error', 'Missing Grade': 'Missing Grade', 'Calculation Discrepancy': 'Calculation Discrepancy'}
    category_str = str(category_value) if category_value else 'Calculation Discrepancy'
    return category_mapping.get(category_str, 'Calculation Discrepancy')

def load_datasets():
    MODEL_DIR = Path(__file__).parent.parent / 'models'
    DATA_DIR = MODEL_DIR / 'data'
    complaints_df = None
    resolved_df = None
    try:
        complaints_path = DATA_DIR / 'complaints.csv'
        if complaints_path.exists():
            complaints_df = pd.read_csv(complaints_path)
    except Exception as e:
        st.warning(f'Could not load complaints.csv: {e}')
    try:
        resolved_path = DATA_DIR / 'resolved_complaints.csv'
        if resolved_path.exists():
            resolved_df = pd.read_csv(resolved_path)
    except Exception as e:
        st.warning(f'Could not load resolved_complaints.csv: {e}')
    return (complaints_df, resolved_df)

def get_sla_coefficients():
    MODEL_DIR = Path(__file__).parent.parent / 'models'
    SURVIVAL_MODEL_PATH = MODEL_DIR / 'sla_survival_model.pkl'
    SLA_FEATURES_PATH = MODEL_DIR / 'sla_features.json'
    try:
        if not SURVIVAL_MODEL_PATH.exists():
            return None
        survival_model = joblib.load(SURVIVAL_MODEL_PATH)
        if hasattr(survival_model, 'hazard_ratios_'):
            coefficients = survival_model.hazard_ratios_
            feature_names = survival_model.summary.index.tolist() if hasattr(survival_model, 'summary') else []
        elif hasattr(survival_model, 'params_'):
            coefficients = survival_model.params_
            feature_names = survival_model.summary.index.tolist() if hasattr(survival_model, 'summary') else []
        else:
            return None
        if SLA_FEATURES_PATH.exists():
            with open(SLA_FEATURES_PATH, 'r') as f:
                sla_features = json.load(f)
            feature_names = sla_features
        if len(coefficients) == len(feature_names):
            importance_df = pd.DataFrame({'Feature': feature_names, 'Coefficient': coefficients, 'Importance': np.abs(coefficients)}).sort_values('Importance', ascending=False)
            return importance_df
        else:
            importance_df = pd.DataFrame({'Feature': [f'Feature_{i}' for i in range(len(coefficients))], 'Coefficient': coefficients, 'Importance': np.abs(coefficients)}).sort_values('Importance', ascending=False)
            return importance_df
    except Exception as e:
        st.warning(f'Could not extract SLA coefficients: {e}')
        return None

def run():
    st.header('🤖 AI Model Insights')
    username = st.session_state.get('username')
    role = st.session_state.get('role')
    if not username or role != 'admin':
        st.error('Admin access required. Please login as an admin.')
        return
    complaints_df, resolved_df = load_datasets()
    load_model()
    api_status = model_status()
    complaints = db.get_all_complaints(limit=1000)
    st.subheader('⏱️ SLA Model Feature Importance (Cox Coefficients)')
    importance_df = get_sla_coefficients()
    if importance_df is not None:
        st.write('**Top 10 Most Important Features:**')
        st.dataframe(importance_df.head(10), use_container_width=True, hide_index=True)
        top_features = importance_df.head(15)
        fig_importance = px.bar(top_features, x='Importance', y='Feature', orientation='h', title='SLA Model Feature Importance (Cox Coefficients)', labels={'Importance': 'Absolute Coefficient Value', 'Feature': 'Feature Name'})
        fig_importance.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_importance, use_container_width=True)
    else:
        st.info('SLA model coefficients not available. Ensure sla_survival_model.pkl and sla_features.json exist.')
    st.divider()
    st.subheader('📁 Dataset Information')
    col1, col2 = st.columns(2)
    with col1:
        st.write('**complaints.csv:**')
        if complaints_df is not None:
            st.metric('Rows', len(complaints_df))
            st.metric('Columns', len(complaints_df.columns))
            with st.expander('View Column Names'):
                st.write(list(complaints_df.columns))
        else:
            st.warning('Not loaded')
    with col2:
        st.write('**resolved_complaints.csv:**')
        if resolved_df is not None:
            st.metric('Rows', len(resolved_df))
            st.metric('Columns', len(resolved_df.columns))
            with st.expander('View Column Names'):
                st.write(list(resolved_df.columns))
        else:
            st.warning('Not loaded')
    st.divider()
    if complaints:
        st.subheader('📥 Export Prediction Data')
        export_data = []
        for c in complaints:
            export_data.append({'Complaint ID': c.get('complaint_id'), 'Student': c.get('student_username', ''), 'Text': c.get('text', ''), 'Predicted Category': get_category_name(c.get('predicted_category', 'Calculation Discrepancy')), 'Confidence': c.get('confidence', 0), 'Status': c.get('status', 'Pending'), 'Created At': c.get('created_at', '')})
        df_export = pd.DataFrame(export_data)
        csv = df_export.to_csv(index=False)
        st.download_button(label='📥 Download All Predictions as CSV', data=csv, file_name='model_predictions_export.csv', mime='text/csv', use_container_width=True)
run()