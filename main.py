import streamlit as st
import pandas as pd

# Constants
TEMP_COEF = 234.5
STD_TEMP = 20.0

def normalize_v(v, t):
    return v * ((TEMP_COEF + STD_TEMP) / (TEMP_COEF + t))

st.title("Winding Inter-Turn Short Detector")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Baseline Data")
    base_temp = st.number_input("Baseline Temp (°C)", value=13.1)
    base_v = st.data_editor(pd.DataFrame({"V_drop": [0.023221, 0.025036, 0.027025, 0.028925, 0.030764, 0.032783]}), key="base")

with col2:
    st.subheader("Production Test Data")
    test_temp = st.number_input("Test Temp (°C)", value=17.4)
    test_v = st.data_editor(pd.DataFrame({"V_drop": [0.023538, 0.025338, 0.027343, 0.029283, 0.031117, 0.032772]}), key="test")

if st.button("Analyze Coil"):
    results = []
    for i in range(6):
        b_20 = normalize_v(base_v.iloc[i]['V_drop'], base_temp)
        t_20 = normalize_v(test_v.iloc[i]['V_drop'], test_temp)
        dev = ((t_20 - b_20) / b_20) * 100
        
        # Ratio to previous layer
        t_ratio = (t_20 / normalize_v(test_v.iloc[i-1]['V_drop'], test_temp)) if i > 0 else 1.0
        
        status = "Pass"
        if dev < -0.8: # Configurable sensitivity threshold
            status = "⚠️ Potential Short"
            
        results.append({"Layer": i+1, "Deviation (%)": round(dev, 2), "Status": status})
        
    st.table(pd.DataFrame(results))
