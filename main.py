import streamlit as st
import pandas as pd
import numpy as np

# Constants
TEMP_COEF = 234.5
STD_TEMP = 20.0

def normalize_v(v, t):
    return v * ((TEMP_COEF + STD_TEMP) / (TEMP_COEF + t))

st.set_page_config(page_title="Winding Inter-Turn Short Detector")

st.title("Winding Inter-Turn Short Detector")

# Configuration to enforce 6 decimal places
v_drop_config = {
    "V_drop": st.column_config.NumberColumn(
        "Voltage Drop (V)",
        format="%.6f",
        step=0.000001
    )
}

# Define the index starting from 1
pancake_index = pd.Index([1, 2, 3, 4, 5, 6], name="Pancake")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Baseline Data")
    base_temp = st.number_input("Baseline Temp (°C)", value=13.1)
    base_v = st.data_editor(
        pd.DataFrame(
            {"V_drop": [0.023221, 0.025036, 0.027025, 0.028925, 0.030764, 0.032783]}, 
            index=pancake_index
        ), 
        key="base",
        column_config=v_drop_config
    )

with col2:
    st.subheader("Production Test Data")
    test_temp = st.number_input("Test Temp (°C)", value=17.4)
    test_v = st.data_editor(
        pd.DataFrame(
            {"V_drop": [0.023538, 0.025338, 0.027343, 0.029283, 0.031117, 0.032772]}, 
            index=pancake_index
        ), 
        key="test",
        column_config=v_drop_config
    )

# Adjustable threshold control
st.divider()
fail_threshold = st.number_input(
    "Failure Threshold (%) - Triggers if drop exceeds this value:", 
    value=-0.80, 
    step=0.10,
    format="%.2f"
)

if st.button("Analyze Coil"):
    raw_devs = []
    
    # Step 1: Calculate raw deviations for all pancakes
    for i in range(1, 7):
        b_20 = normalize_v(base_v.loc[i, 'V_drop'], base_temp)
        t_20 = normalize_v(test_v.loc[i, 'V_drop'], test_temp)
        dev = ((t_20 - b_20) / b_20) * 100
        raw_devs.append(dev)
        
    # Step 2: Find the systemic shift (median of raw deviations)
    systemic_shift = np.median(raw_devs)
    
    # Step 3: Apply correction and evaluate status
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
    
    # Create the DataFrame and explicitly set the row index to start from 1 to 6
    df_results = pd.DataFrame(results)
    df_results.index = range(1, len(df_results) + 1)
    df_results.index.name = "Index"
    
    st.table(df_results)

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
