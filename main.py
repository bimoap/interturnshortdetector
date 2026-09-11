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
