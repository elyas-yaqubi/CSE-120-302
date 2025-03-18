import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import time  # used to simulate a delay
from scipy import stats

st.title("Organoids Gene Expression Filtering & Visualization App")

# -------------------------------------------------------------
# 1. Session State: Store Row Count and Uploaded Data
# -------------------------------------------------------------
if "nrows" not in st.session_state:
    st.session_state["nrows"] = None
if "stored_data" not in st.session_state:
    st.session_state["stored_data"] = pd.DataFrame()

# -------------------------------------------------------------
# 2. Ask the User for Number of Rows to Load (Before Uploading)
# -------------------------------------------------------------
nrows_input = st.sidebar.number_input(
    "Enter number of rows to load from each file", min_value=1, value=1000, step=100
)
if st.sidebar.button("Save row count"):
    st.session_state["nrows"] = int(nrows_input)
    st.sidebar.success(f"Row count set to {st.session_state['nrows']}")

if st.session_state["nrows"] is None:
    st.write("Please set the number of rows to load before uploading files.")
else:
    # -------------------------------------------------------------
    # 3. File Uploader: Upload Excel File(s)
    # -------------------------------------------------------------
    uploaded_files = st.sidebar.file_uploader("Upload Excel file(s)", type=["xlsx"], accept_multiple_files=True)

    if uploaded_files:
        new_dfs = []
        for uploaded_file in uploaded_files:
            try:
                # Load only the specified number of rows
                df_uploaded = pd.read_excel(uploaded_file, nrows=st.session_state["nrows"])
                new_dfs.append(df_uploaded)
                st.sidebar.success(f"Processed {uploaded_file.name}")
            except Exception as e:
                st.sidebar.error(f"Error processing {uploaded_file.name}: {e}")
        if new_dfs:
            new_data = pd.concat(new_dfs, ignore_index=True)
            # Append new data to what is already stored
            if st.session_state["stored_data"].empty:
                st.session_state["stored_data"] = new_data
            else:
                st.session_state["stored_data"] = pd.concat(
                    [st.session_state["stored_data"], new_data], ignore_index=True
                )

    combined_df = st.session_state["stored_data"]

    if combined_df.empty:
        st.write("No data uploaded yet. Please use the sidebar uploader to add Excel files.")
    else:
        # -------------------------------------------------------------
        # 4. Filtering Options
        # -------------------------------------------------------------
        st.sidebar.header("Filter Options")
        
        # Assume the data has a column named "gene_id" and expression columns.
        control_cols = [col for col in combined_df.columns if col.startswith("Control")]
        p250_cols = [col for col in combined_df.columns if col.startswith("P250")]
        p350_cols = [col for col in combined_df.columns if col.startswith("P350")]
        
        selected_gene = st.sidebar.selectbox(
            "Select Gene ID", ["All"] + sorted(combined_df["gene_id"].astype(str).unique())
        )
        
        # Use quantiles to set slider bounds, avoiding outlier extremes.
        def get_slider_bounds(df, cols):
            lower = int(df[cols].quantile(0.01).min())
            upper = int(df[cols].quantile(0.99).max())
            return lower, upper

        control_lower, control_upper = get_slider_bounds(combined_df, control_cols)
        p250_lower, p250_upper = get_slider_bounds(combined_df, p250_cols)
        p350_lower, p350_upper = get_slider_bounds(combined_df, p350_cols)
        
        st.sidebar.subheader("Control Group Filtering")
        control_min, control_max = st.sidebar.slider(
            "Control Expression Range", control_lower, control_upper, (control_lower, control_upper)
        )
        
        st.sidebar.subheader("P250kPa Organoids Filtering")
        p250_min, p250_max = st.sidebar.slider(
            "P250kPa Expression Range", p250_lower, p250_upper, (p250_lower, p250_upper)
        )
        
        st.sidebar.subheader("P350kPa Organoids Filtering")
        p350_min, p350_max = st.sidebar.slider(
            "P350kPa Expression Range", p350_lower, p350_upper, (p350_lower, p350_upper)
        )
        
        st.sidebar.header("Advanced Filters")
        min_mean_expr = st.sidebar.number_input("Minimum Mean Expression", min_value=0, value=10)
        min_variance = st.sidebar.number_input("Minimum Variance", min_value=0.0, value=5.0)
        
        st.sidebar.subheader("Differential Expression Filtering")
        all_conditions = combined_df.columns[1:]  # excluding gene_id
        condition1 = st.sidebar.selectbox(
            "Condition 1 (numerator)",
            all_conditions,
            index=all_conditions.get_loc("P250kPa_Hi1") if "P250kPa_Hi1" in all_conditions else 0,
        )
        condition2 = st.sidebar.selectbox(
            "Condition 2 (denom)",
            all_conditions,
            index=all_conditions.get_loc("Control_1") if "Control_1" in all_conditions else 0,
        )
        fc_threshold = st.sidebar.number_input("Log₂ Fold Change Threshold", min_value=0.0, value=1.0)
        
        st.sidebar.header("Outlier Removal")
        remove_outliers = st.sidebar.checkbox("Remove Outliers (Z-score filtering)", value=False)
        z_threshold = st.sidebar.number_input("Z-score Threshold", min_value=0.0, value=3.0)
        
        # -------------------------------------------------------------
        # 5. Data Filtering Pipeline with Spinner and Minimal Delay
        # -------------------------------------------------------------
        with st.spinner("Filtering data..."):
            # Artificial delay to ensure the spinner is visible (adjust as needed)
            time.sleep(0.5)
            
            filtered_df = combined_df.copy()
            
            # (a) Filter by Gene ID (if a specific gene is selected)
            if selected_gene != "All":
                filtered_df = filtered_df[filtered_df["gene_id"].astype(str) == selected_gene]
            
            # (b) Apply expression range filters for each group using masks
            control_mask = filtered_df[control_cols].applymap(lambda x: control_min <= x <= control_max)
            p250_mask = filtered_df[p250_cols].applymap(lambda x: p250_min <= x <= p250_max)
            p350_mask = filtered_df[p350_cols].applymap(lambda x: p350_min <= x <= p350_max)
            filtered_df = filtered_df[control_mask.any(axis=1) | p250_mask.any(axis=1) | p350_mask.any(axis=1)]
            
            # (c) Remove lowly expressed genes (based on mean expression)
            mean_expr = filtered_df.iloc[:, 1:].mean(axis=1)
            filtered_df = filtered_df[mean_expr >= min_mean_expr]
            
            # (d) Remove genes with low variance
            variance_expr = filtered_df.iloc[:, 1:].var(axis=1)
            filtered_df = filtered_df[variance_expr >= min_variance]
            
            # (e) Differential Expression Filtering: compute log₂ fold change
            epsilon = 1e-6  # to avoid log(0)
            filtered_df["log2FC"] = np.log2(filtered_df[condition1] + epsilon) - np.log2(filtered_df[condition2] + epsilon)
            filtered_df = filtered_df[abs(filtered_df["log2FC"]) >= fc_threshold]
            
            # (f) Outlier Removal (optional)
            if remove_outliers:
                expr_cols = filtered_df.columns.difference(["gene_id", "log2FC"])
                z_scores = np.abs(stats.zscore(filtered_df[expr_cols], nan_policy="omit"))
                filtered_df = filtered_df[(z_scores < z_threshold).all(axis=1)]
        
        st.write(f"### Filtered Data ({len(filtered_df)} results)")
        st.dataframe(filtered_df)
        
        # -------------------------------------------------------------
        # 6. Visualization Section
        # -------------------------------------------------------------
        st.write("## Visualization")
        
        if selected_gene != "All" and not filtered_df.empty:
            # For a specific gene, show its expression as a bar chart
            gene_row = filtered_df.iloc[0]  # Should be a single row when a gene is selected
            gene_data = gene_row.drop(["gene_id", "log2FC"])
            gene_df = gene_data.reset_index()
            gene_df.columns = ["Condition", "Expression"]
        
            st.write(f"### Expression for Gene {selected_gene}")
            bar_chart = alt.Chart(gene_df).mark_bar().encode(
                x=alt.X("Condition:N", sort=None),
                y=alt.Y("Expression:Q"),
                tooltip=["Condition", "Expression"],
            ).properties(width=800, height=400)
            st.altair_chart(bar_chart)
        else:
            if not filtered_df.empty:
                # Overall visualization for all filtered genes
                melted_df = filtered_df.melt(id_vars=["gene_id", "log2FC"], var_name="Condition", value_name="Expression")
                st.write("### Overall Expression Distribution")
                histogram = alt.Chart(melted_df).mark_bar().encode(
                    alt.X("Expression:Q", bin=alt.Bin(maxbins=50)),
                    y="count()",
                    tooltip=["count()"],
                ).properties(width=800, height=400)
                st.altair_chart(histogram)
        
                st.write("### Box Plot by Condition")
                boxplot = alt.Chart(melted_df).mark_boxplot().encode(
                    x="Condition:N",
                    y="Expression:Q",
                    tooltip=["Condition", "Expression"],
                ).properties(width=800, height=400)
                st.altair_chart(boxplot)
            else:
                st.write("No data available after filtering. Adjust your filters.")
