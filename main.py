import streamlit as st
import pandas as pd
import numpy as np
import json

# Constants
TEMP_COEF = 234.5
STD_TEMP = 20.0

def normalize_v(v, t):
    return v * ((TEMP_COEF + STD_TEMP) / (TEMP_COEF + t))

st.set_page_config(page_title="Winding Inter-Turn Short Detector")
st.title("Winding Inter-Turn Short Detector")

# --- Initialize Session State ---
# This ensures data persists and widgets refresh correctly upon file upload
if "app_state" not in st.session_state:
    st.session_state.base_temp = 13.1
    st.session_state.test_temp = 17.4
    st.session_state.base_v = [0.023221, 0.025036, 0.027025, 0.028925, 0.030764, 0.032783]
    st.session_state.test_v = [0.023538, 0.025338, 0.027343, 0.029283, 0.031117, 0.032772]
    st.session_state.ui_key = 0
    st.session_state.app_state = True

# --- Sidebar: Local Save / Load ---
with st.sidebar:
    st.header("💾 Data Management")
    
    # Uploader
    uploaded_file = st.file_uploader("Load Inputs (JSON)", type=["json"])
    if uploaded_file is not None:
        # Prevent infinite loops by verifying file ID
        if st.session_state.get("last_uploaded") != uploaded_file.file_id:
            try:
                loaded_data = json.load(uploaded_file)
                st.session_state.base_temp = loaded_data.get("base_temp", 13.1)
                st.session_state.base_v = loaded_data.get("base_v", st.session_state.base_v)
                st.session_state.test_temp = loaded_data.get("test_temp", 17.4)
                st.session_state.test_v = loaded_data.get("test_v", st.session_state.test_v)
                st.session_state.ui_key += 1 # Force widgets to refresh with new data
                st.session_state.last_uploaded = uploaded_file.file_id
                st.rerun()
            except Exception:
                st.error("Error reading JSON format.")

# Configuration to enforce 6 decimal places
v_drop_config = {
    "V_drop": st.column_config.NumberColumn(
        "Voltage Drop (V)",
        format="%.6f",
        step=0.000001
    )
}

pancake_index = pd.Index([1, 2, 3, 4, 5, 6], name="Pancake")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Baseline Data")
    base_temp_in = st.number_input("Baseline Temp (°C)", value=st.session_state.base_temp, key=f"bt_{st.session_state.ui_key}")
    base_df = pd.DataFrame({"V_drop": st.session_state.base_v}, index=pancake_index)
    base_v_out = st.data_editor(base_df, key=f"bv_{st.session_state.ui_key}", column_config=v_drop_config)

with col2:
    st.subheader("Production Test Data")
    test_temp_in = st.number_input("Test Temp (°C)", value=st.session_state.test_temp, key=f"tt_{st.session_state.ui_key}")
    test_df = pd.DataFrame({"V_drop": st.session_state.test_v}, index=pancake_index)
    test_v_out = st.data_editor(test_df, key=f"tv_{st.session_state.ui_key}", column_config=v_drop_config)

# Package current UI state for exporting
current_data = {
    "base_temp": base_temp_in,
    "base_v": base_v_out["V_drop"].tolist(),
    "test_temp": test_temp_in,
    "test_v": test_v_out["V_drop"].tolist()
}

with st.sidebar:
    st.download_button(
        label="⬇️ Save Current Inputs",
        data=json.dumps(current_data, indent=4),
        file_name="winding_test_inputs.json",
        mime="application/json"
    )

st.divider()
fail_threshold = st.number_input(
    "Failure Threshold (%) - Triggers if drop exceeds this value:", 
    value=-0.80, 
    step=0.10,
    format="%.2f"
)

if st.button("Analyze Coil"):
    raw_devs = []
    
    for i in range(1, 7):
        b_20 = normalize_v(base_v_out.loc[i, 'V_drop'], base_temp_in)
        t_20 = normalize_v(test_v_out.loc[i, 'V_drop'], test_temp_in)
        dev = ((t_20 - b_20) / b_20) * 100
        raw_devs.append(dev)
        
    systemic_shift = np.median(raw_devs)
    
    results = []
    for i in range(1, 7):
        corrected_dev = raw_devs[i-1] - systemic_shift 
        
        status = "Pass"
        if corrected_dev < fail_threshold: 
            status = "⚠️ Potential Short"
            
        results.append({
            "Pancake": i, 
            "Raw Dev (%)": round(raw_devs[i-1], 2),
            "Correct Dev (%)": round(corrected_dev, 2),
            "Status": status
        })
        
    st.write(f"**Calculated Systemic Shift (Temperature/Setup Offset):** {systemic_shift:.2f}%")
    
    df_results = pd.DataFrame(results)
    df_results.index = range(1, len(df_results) + 1)
    df_results.index.name = "Index"
    
    st.table(df_results)
    
    # Export calculated results to CSV for record keeping
    csv = df_results.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📄 Download Result Report (CSV)",
        data=csv,
        file_name="winding_results_report.csv",
        mime="text/csv"
    )

# Signature Block
st.divider()
st.markdown(
    """
    <div style='text-align: right; color: gray;'>
        <small>Developed by <b>Bimo Adhi Prastya</b><br>
        Coil Shop Technician & NT Production Engineer<br>
        Buckley Systems</small>
    </div>
    """,
    unsafe_allow_html=True
)
