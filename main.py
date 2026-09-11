import streamlit as st
import pandas as pd

# Constants
TEMP_COEF = 234.5
STD_TEMP = 20.0

def normalize_v(v, t):
    return v * ((TEMP_COEF + STD_TEMP) / (TEMP_COEF + t))

st.title("Winding Inter-Turn Short Detector")

# Configuration to enforce 6 decimal places
v_drop_config = {
    "V_drop": st.column_config.NumberColumn(
        "Voltage Drop (V)",
        format="%.6f",
        step=0.000001
    )
}

# Define the index starting from 1 instead of 0
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

if st.button("Analyze Coil"):
    results = []
    
    # Loop from 1 to 6 to match the pancake numbering
    for i in range(1, 7):
        b_20 = normalize_v(base_v.loc[i, 'V_drop'], base_temp)
        t_20 = normalize_v(test_v.loc[i, 'V_drop'], test_temp)
        dev = ((t_20 - b_20) / b_20) * 100
        
        status = "Pass"
        if dev < -0.8: # Configurable sensitivity threshold
            status = "⚠️ Potential Short"
            
        results.append({
            "Pancake": i, 
            "Deviation (%)": round(dev, 2), 
            "Status": status
        })
        
    # Set the Pancake column as the index for a cleaner results table
    st.table(pd.DataFrame(results).set_index("Pancake"))
