import streamlit as st
import pandas as pd
import numpy as np
import json
import altair as alt

# Constants
TEMP_COEF = 234.5
STD_TEMP = 20.0

def normalize_v(v, t):
    return v * ((TEMP_COEF + STD_TEMP) / (TEMP_COEF + t))

st.set_page_config(page_title="Winding Inter-Turn Short Detector", layout="wide")
st.title("Winding Inter-Turn Short Detector")

# --- Built-in Examples ---
BUILT_IN_EXAMPLES = {
    "Custom / Uploaded": None,
    "FEM IMPHEAT 1st coil fail example": {
        "base_temp": 14.0,
        "base_v": [0.023264, 0.025204, 0.026897, 0.028881, 0.03098, 0.032751],
        "test_temp": 17.4,
        "test_v": [0.023538, 0.025338, 0.027343, 0.029283, 0.031117, 0.032772]
    },
    "FEM IMPHEAT 2nd Coil in canning": {
        "base_temp": 14.0,
        "base_v": [0.023264, 0.025204, 0.026897, 0.028881, 0.03098, 0.032751],
        "test_temp": 16.5,
        "test_v": [0.023345, 0.025326, 0.027044, 0.028956, 0.031127, 0.032877]
    },
    "FEM IMPHEAT 1st coil After Fixed": {
        "base_temp": 13.1,
        "base_v": [0.023221, 0.025036, 0.027025, 0.028925, 0.030764, 0.032783],
        "test_temp": 16.5,
        "test_v": [0.023345, 0.025326, 0.027044, 0.028956, 0.031127, 0.032877]
    },
    "FEM IMPHEAT 1st coil fail example 3rd reading": {
        "base_temp": 13.1,
        "base_v": [0.023221, 0.025036, 0.027025, 0.028925, 0.030764, 0.032783],
        "test_temp": 13.8,
        "test_v": [0.023361, 0.025163, 0.027154, 0.029096, 0.030907, 0.032564]
    }
}

# --- Initialize Session State ---
if "app_state" not in st.session_state:
    st.session_state.num_pancakes = 6
    st.session_state.base_temp = 13.1
    st.session_state.test_temp = 17.4
    st.session_state.base_v = [0.023221, 0.025036, 0.027025, 0.028925, 0.030764, 0.032783]
    st.session_state.test_v = [0.023538, 0.025338, 0.027343, 0.029283, 0.031117, 0.032772]
    st.session_state.ui_key = 0
    st.session_state.app_state = True

def adjust_array_length(arr, target_len):
    if len(arr) < target_len:
        return arr + [0.0] * (target_len - len(arr))
    return arr[:target_len]

def load_example():
    selected = st.session_state.example_selector
    if selected != "Custom / Uploaded":
        data = BUILT_IN_EXAMPLES[selected]
        st.session_state.base_temp = data["base_temp"]
        st.session_state.base_v = data["base_v"].copy()
        st.session_state.test_temp = data["test_temp"]
        st.session_state.test_v = data["test_v"].copy()
        st.session_state.num_pancakes = len(data["base_v"])
        st.session_state.ui_key += 1

def update_pancake_count():
    new_count = st.session_state.pancake_counter
    st.session_state.base_v = adjust_array_length(st.session_state.base_v, new_count)
    st.session_state.test_v = adjust_array_length(st.session_state.test_v, new_count)
    st.session_state.num_pancakes = new_count
    st.session_state.ui_key += 1

# --- Sidebar: Data Management & Settings ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.selectbox(
        "Load Built-in Example",
        options=list(BUILT_IN_EXAMPLES.keys()),
        key="example_selector",
        on_change=load_example
    )
    
    st.number_input(
        "Number of Pancakes",
        min_value=1,
        max_value=24,
        value=st.session_state.num_pancakes,
        key="pancake_counter",
        on_change=update_pancake_count
    )
    
    st.divider()
    st.header("💾 File Management")
    
    uploaded_file = st.file_uploader("Load Inputs (JSON)", type=["json"])
    if uploaded_file is not None:
        if st.session_state.get("last_uploaded") != uploaded_file.file_id:
            try:
                loaded_data = json.load(uploaded_file)
                st.session_state.base_temp = loaded_data.get("base_temp", 13.1)
                st.session_state.base_v = loaded_data.get("base_v", st.session_state.base_v)
                st.session_state.test_temp = loaded_data.get("test_temp", 17.4)
                st.session_state.test_v = loaded_data.get("test_v", st.session_state.test_v)
                st.session_state.num_pancakes = len(st.session_state.base_v)
                st.session_state.ui_key += 1
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

pancake_index = pd.Index(range(1, st.session_state.num_pancakes + 1), name="Pancake")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Baseline Data")
    base_temp_in = st.number_input("Baseline Temp (°C)", value=st.session_state.base_temp, key=f"bt_{st.session_state.ui_key}")
    base_df = pd.DataFrame({"V_drop": st.session_state.base_v}, index=pancake_index)
    base_v_out = st.data_editor(base_df, key=f"bv_{st.session_state.ui_key}", column_config=v_drop_config, use_container_width=True)

with col2:
    st.subheader("Production Test Data")
    test_temp_in = st.number_input("Test Temp (°C)", value=st.session_state.test_temp, key=f"tt_{st.session_state.ui_key}")
    test_df = pd.DataFrame({"V_drop": st.session_state.test_v}, index=pancake_index)
    test_v_out = st.data_editor(test_df, key=f"tv_{st.session_state.ui_key}", column_config=v_drop_config, use_container_width=True)

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

# Adjustable threshold and calculation controls
st.divider()
col3, col4 = st.columns(2)
with col3:
    fail_threshold = st.number_input(
        "Failure Threshold (%)", 
        value=-0.80, 
        step=0.10,
        format="%.2f",
        help="Triggers if the corrected voltage drop exceeds this negative percentage."
    )
with col4:
    filter_method = st.radio(
        "Shift Calculation Method:",
        options=["1-Pass (Median)", "2-Pass (Outlier-Filtered Mean)"],
        horizontal=True
    )

if st.button("Analyze Coil", type="primary"):
    raw_devs = []
    
    # Calculate raw deviations
    for i in range(1, st.session_state.num_pancakes + 1):
        b_20 = normalize_v(base_v_out.loc[i, 'V_drop'], base_temp_in)
        t_20 = normalize_v(test_v_out.loc[i, 'V_drop'], test_temp_in)
        
        if b_20 == 0: # Prevent division by zero if default rows aren't filled
            dev = 0
        else:
            dev = ((t_20 - b_20) / b_20) * 100
        raw_devs.append(dev)
        
    # Calculate Systemic Shift
    if filter_method == "1-Pass (Median)":
        systemic_shift = np.median(raw_devs)
    else:
        rough_shift = np.median(raw_devs)
        healthy_raws = [raw for raw in raw_devs if (raw - rough_shift) > -1.0]
        systemic_shift = np.mean(healthy_raws) if healthy_raws else rough_shift
    
    # Apply correction
    results = []
    for i in range(1, st.session_state.num_pancakes + 1):
        corrected_dev = raw_devs[i-1] - systemic_shift 
        
        status = "Pass"
        if corrected_dev < fail_threshold: 
            status = "⚠️ Potential Short"
            
        results.append({
            "Pancake": str(i),
            "Raw Dev (%)": round(raw_devs[i-1], 2),
            "Correct Dev (%)": round(corrected_dev, 2),
            "Status": status
        })
        
    st.write(f"**Calculated Systemic Shift ({filter_method}):** {systemic_shift:.2f}%")
    
    df_results = pd.DataFrame(results)
    df_results.index = range(1, len(df_results) + 1)
    df_results.index.name = "Index"
    
    # Visual Chart
    st.subheader("Visual Analysis")
    bars = alt.Chart(df_results).mark_bar().encode(
        x=alt.X('Pancake:N', title='Pancake Number', axis=alt.Axis(labelAngle=0)),
        y=alt.Y('Correct Dev (%):Q', title='Corrected Deviation (%)'),
        color=alt.condition(
            alt.datum['Correct Dev (%)'] < fail_threshold,
            alt.value('#d62728'),  # Red for failed
            alt.value('#1f77b4')   # Blue for healthy
        ),
        tooltip=['Pancake', 'Correct Dev (%)', 'Status']
    )
    
    threshold_line = alt.Chart(pd.DataFrame({'threshold': [fail_threshold]})).mark_rule(
        color='red', strokeDash=[5, 5]
    ).encode(y='threshold:Q')
    
    st.altair_chart(bars + threshold_line, use_container_width=True)
    st.table(df_results)
    
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
