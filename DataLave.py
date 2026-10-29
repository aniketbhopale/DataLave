import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib as mpl
import validation

mpl.rcParams['figure.dpi'] = 300
mpl.rcParams['savefig.dpi'] = 300

st.set_page_config(page_title="DataLave", layout="wide")


def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


try:
    load_css("assets/style.css")
except FileNotFoundError:
    pass


def clean_data(df, feature, method):
    df1 = df.copy()
    if method == 'dropnulls_method':
        df1 = df1.dropna(subset=[feature])
    elif method in ['mean_method', 'median_method']:
        if pd.api.types.is_numeric_dtype(df1[feature]):
            val = df1[feature].mean() if method == 'mean_method' else df1[feature].median()
            if pd.notna(val):
                df1[feature] = df1[feature].fillna(val)
    elif method == 'min_method':
        val = df1[feature].min()
        if pd.notna(val):
            df1[feature] = df1[feature].fillna(val)
    elif method == 'max_method':
        val = df1[feature].max()
        if pd.notna(val):
            df1[feature] = df1[feature].fillna(val)
    return df1


def Outliers(df, feature, methods1, submethods1, k):
    df2 = df.copy()
    series = df2[feature].dropna()

    if len(series) < 2:
        return df2

    if methods1 == 'Z-score':
        std_val = series.std()
        if std_val == 0 or np.isnan(std_val):
            return df2
        z_score = (df2[feature] - series.mean()) / std_val
        if submethods1 == 'Records Above +3σ and below -3σ':
            df2 = df2[z_score.between(-3, 3) | df2[feature].isna()]
        elif submethods1 == 'Records Above +2σ and below -2σ':
            df2 = df2[z_score.between(-2, 2) | df2[feature].isna()]
        elif submethods1 == 'Records Above +1σ and below -1σ':
            df2 = df2[z_score.between(-1, 1) | df2[feature].isna()]

    elif methods1 == 'IQR score':
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        IQR = q3 - q1
        if IQR == 0:
            return df2
        min_range = q1 - (k * IQR)
        max_range = q3 + (k * IQR)
        df2 = df2[df2[feature].between(min_range, max_range) | df2[feature].isna()]

    return df2


def plot_outlier_distribution(df, feature, is_outlier_mask=None, is_preview=True):
    fig, (ax_box, ax_hist) = plt.subplots(
        2, 1,
        figsize=(8, 4.5),
        dpi=300,
        sharex=True,
        gridspec_kw={'height_ratios': [0.25, 0.75]}
    )
    sns.set_theme(style="whitegrid")

    clean_col = df[feature].dropna()
    if clean_col.empty:
        ax_box.text(0.5, 0.5, "No data available to plot", ha='center', va='center')
        ax_hist.text(0.5, 0.5, "No data available to plot", ha='center', va='center')
        plt.tight_layout()
        return fig

    if is_preview and is_outlier_mask is not None:
        kept_vals = df.loc[~is_outlier_mask, feature].dropna()
        removed_vals = df.loc[is_outlier_mask, feature].dropna()

        sns.boxplot(x=df[feature], ax=ax_box, color="#bbdefb", showfliers=False)
        ax_box.set(xlabel='')
        if len(kept_vals) > 0:
            sns.stripplot(x=kept_vals, ax=ax_box, color="#1976d2", size=3, alpha=0.6, jitter=0.2)
        if len(removed_vals) > 0:
            sns.stripplot(x=removed_vals, ax=ax_box, color="#e53935", size=4, alpha=0.9, jitter=0.2)

        min_v, max_v = clean_col.min(), clean_col.max()
        bins = 10 if min_v == max_v else np.linspace(min_v, max_v, 45)

        if len(kept_vals) > 0:
            sns.histplot(kept_vals, bins=bins, ax=ax_hist, color="#1976d2", label=f'Kept ({len(kept_vals)})',
                         kde=len(kept_vals) > 1)
        if len(removed_vals) > 0:
            sns.histplot(removed_vals, bins=bins, ax=ax_hist, color="#e53935",
                         label=f'Outliers Removed ({len(removed_vals)})', kde=False)

        ax_hist.legend(loc='upper right')
        ax_box.set_title(f"Preview Distribution: '{feature}'", fontsize=11, fontweight='bold')
    else:
        sns.boxplot(x=df[feature], ax=ax_box, color="#a5d6a7", fliersize=4)
        ax_box.set(xlabel='')
        sns.histplot(clean_col, ax=ax_hist, color="#2e7d32", kde=len(clean_col) > 1,
                     label=f'Active Records ({len(df)})')
        ax_hist.legend(loc='upper right')
        ax_box.set_title(f"Current Distribution: '{feature}'", fontsize=11, fontweight='bold')

    plt.tight_layout()
    return fig


def Encode(df, feature, mapping_dict):
    df3 = df.copy()
    df3[feature] = df3[feature].map(mapping_dict)
    return df3


st.title("DataLave")

if 'df' not in st.session_state:
    st.session_state.df = None
if 'loaded_filename' not in st.session_state:
    st.session_state.loaded_filename = None
if 'ignore_schema_warnings' not in st.session_state:
    st.session_state.ignore_schema_warnings = False

st.sidebar.subheader('Select Work to perform')
work = st.sidebar.radio('Select Work to perform',
                        ["Main Menu", "1.Fill and Clean Nulls", "2.Outlier Management", "3.Encoding"])

methods = ['dropnulls_method', 'mean_method', 'median_method', 'min_method', 'max_method']
methods1 = ['Z-score', 'IQR score']
submethods1 = ['Records Above +3σ and below -3σ', 'Records Above +2σ and below -2σ', 'Records Above +1σ and below -1σ']
methods2 = ['Encode randomly', 'Encode in manual Order']

file = st.file_uploader('Upload your csv file', type='csv')

if file is not None:
    if st.session_state.loaded_filename != file.name:
        try:
            st.session_state.df = pd.read_csv(file, encoding='utf-8')
        except UnicodeDecodeError:
            file.seek(0)
            st.session_state.df = pd.read_csv(file, encoding='latin-1')
        st.session_state.loaded_filename = file.name
        st.session_state.ignore_schema_warnings = False

if work == 'Main Menu':
    if st.session_state.df is None:
        st.info("Please upload a CSV file.")
    else:
        current_df = st.session_state.df

        if not st.session_state.ignore_schema_warnings:
            schema = validation.build_schema_from_df(current_df)
            is_valid, failures = validation.validate_df(current_df, schema)

            if not is_valid and failures is not None:
                st.error(f"Found {len(failures)} data quality issues")
                st.dataframe(failures, use_container_width=True)
                if st.checkbox("Ignore / Don't remind again for this dataset", key="ignore_warnings_checkbox"):
                    st.session_state.ignore_schema_warnings = True
                    st.rerun()

        total_rows, total_cols = current_df.shape
        total_cells = total_rows * total_cols
        total_nulls = int(current_df.isna().sum().sum())
        null_percentage = (total_nulls / total_cells * 100) if total_cells > 0 else 0.0
        total_duplicates = int(current_df.duplicated().sum())
        numeric_count = len(current_df.select_dtypes(include=np.number).columns)

        st.subheader("Dataset Info")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Dimensions", f"{total_rows:,} × {total_cols:,}", help="Total Rows × Total Columns")
        kpi2.metric("Missing Cells", f"{null_percentage:.2f}%", f"{total_nulls:,} nulls", delta_color="inverse")
        kpi3.metric("Duplicate Rows", f"{total_duplicates:,}", help="Exact identical rows")
        kpi4.metric("Numeric Columns", f"{numeric_count:,}", help="Total features available for stats & outliers")

        st.markdown("---")

        st.subheader("Column Description & Cardinality")
        audit_rows = []
        for col in current_df.columns:
            col_series = current_df[col]
            n_null = int(col_series.isna().sum())
            null_pct = (n_null / total_rows * 100) if total_rows > 0 else 0.0
            n_unique = int(col_series.nunique(dropna=True))
            cardinality_ratio = (n_unique / total_rows) if total_rows > 0 else 0.0
            samples = col_series.dropna().head(3).tolist()
            sample_preview = ", ".join(map(str, samples)) if samples else "—"

            audit_rows.append({
                "Column": col,
                "Inferred Type": str(col_series.dtype),
                "Missing Count": f"{n_null:,} ({null_pct:.1f}%)",
                "Unique Values": f"{n_unique:,}",
                "Cardinality Ratio": round(cardinality_ratio, 4),
                "Sample Values": sample_preview
            })

        audit_df = pd.DataFrame(audit_rows)
        st.dataframe(audit_df, use_container_width=True)

        st.markdown("---")

        null_counts = current_df.isna().sum()
        cols_with_nulls = null_counts[null_counts > 0].sort_values(ascending=True)

        if not cols_with_nulls.empty:
            st.subheader("Missing Values Breakdown")
            fig_null, ax_null = plt.subplots(figsize=(8, max(2.5, len(cols_with_nulls) * 0.45)))
            y_positions = range(len(cols_with_nulls))
            percentages = (cols_with_nulls / total_rows) * 100

            bars = ax_null.barh(y_positions, percentages, color="#e74c3c", edgecolor="none", height=0.6)
            ax_null.set_yticks(y_positions)
            ax_null.set_yticklabels(cols_with_nulls.index)
            ax_null.set_xlabel("Missing Percentage (%)")
            ax_null.set_xlim(0, max(100, float(percentages.max()) * 1.15))

            for bar, pct, count in zip(bars, percentages, cols_with_nulls):
                ax_null.text(pct + 1, bar.get_y() + bar.get_height() / 2, f"{pct:.1f}% ({count:,})",
                             va='center', fontsize=9, color="#333333")

            st.pyplot(fig_null, use_container_width=True, dpi=300)
            plt.close(fig_null)

        numeric_cols = current_df.select_dtypes(include=np.number).columns.tolist()
        if numeric_cols:
            st.subheader("Numeric Distribution & Outliers")
            col_to_plot = st.selectbox("Select numeric feature to inspect:", numeric_cols, key="main_menu_num_select")
            clean_series = current_df[col_to_plot].dropna()
            if len(clean_series) > 1:
                fig_dist, (ax_box, ax_hist) = plt.subplots(
                    2, 1, figsize=(9, 4.5), sharex=True, gridspec_kw={'height_ratios': [0.25, 0.75]}
                )
                sns.boxplot(x=clean_series, ax=ax_box, color="#3498db", fliersize=3)
                ax_box.set(xlabel="")
                ax_box.set_title(f"Distribution & Spread: {col_to_plot}", fontsize=11, fontweight="bold")

                sns.histplot(clean_series, kde=True, ax=ax_hist, color="#2980b9", stat="density", bins=30)
                ax_hist.set_xlabel(col_to_plot)
                ax_hist.set_ylabel("Density")

                st.pyplot(fig_dist, use_container_width=True, dpi=300)
                plt.close(fig_dist)

        if len(numeric_cols) > 1:
            st.subheader("Feature Collinearity (Pearson Correlation)")
            corr_matrix = current_df[numeric_cols].corr()

            if not corr_matrix.isna().all().all():
                fig_corr, ax_corr = plt.subplots(
                    figsize=(min(10, len(numeric_cols) * 1.2), min(8, len(numeric_cols) * 0.9)))
                sns.heatmap(
                    corr_matrix,
                    annot=True,
                    fmt=".2f",
                    cmap="coolwarm",
                    cbar=True,
                    ax=ax_corr,
                    linewidths=0.5,
                    vmin=-1, vmax=1
                )
                plt.xticks(rotation=45, ha='right')
                st.pyplot(fig_corr, use_container_width=True, dpi=300)
                plt.close(fig_corr)

        cat_cols = current_df.select_dtypes(include=['object', 'category']).columns.tolist()
        if cat_cols:
            st.subheader("Categorical Feature Balancer")
            selected_cat = st.selectbox("Select categorical feature:", cat_cols, key="main_menu_cat_select")
            top_n = current_df[selected_cat].value_counts(dropna=False).head(10)

            if not top_n.empty:
                fig_cat, ax_cat = plt.subplots(figsize=(8, max(2.5, len(top_n) * 0.4)))
                labels = [str(idx)[:25] + '...' if len(str(idx)) > 25 else str(idx) for idx in top_n.index]
                sns.barplot(x=top_n.values, y=labels, ax=ax_cat, palette="viridis")
                ax_cat.set_title(f"Top Categories: {selected_cat} (Up to 10)", fontsize=10)
                ax_cat.set_xlabel("Frequency Count")

                st.pyplot(fig_cat, use_container_width=True, dpi=300)
                plt.close(fig_cat)

        st.markdown("---")
        st.caption('Current Dataset Version:')
        st.dataframe(current_df, use_container_width=True)
        st.caption(f"Shape: {current_df.shape}")

if work == '1.Fill and Clean Nulls':
    if st.session_state.df is not None:
        st.subheader("Fill and Clean Nulls")
        feature = st.selectbox('Select your feature', st.session_state.df.columns)

        if pd.api.types.is_numeric_dtype(st.session_state.df[feature]):
            valid_methods = methods
        else:
            valid_methods = ['dropnulls_method', 'min_method', 'max_method']

        method = st.selectbox('Select your method', valid_methods)

        if st.button('Apply Changes'):
            st.session_state.df = clean_data(st.session_state.df, feature, method)
            st.success('Your changes have been saved.')

            if not st.session_state.ignore_schema_warnings:
                schema = validation.build_schema_from_df(st.session_state.df)
                is_valid, failures = validation.validate_df(st.session_state.df, schema)
                if not is_valid and failures is not None:
                    st.warning(f"Post-cleaning validation: {len(failures)} issues found")
                    st.dataframe(failures, use_container_width=True)

        st.caption('Current Dataset:')
        st.dataframe(st.session_state.df, use_container_width=True)
        st.caption(st.session_state.df.shape)

        st.markdown("---")

        # Check If Emails are formatted (placed below the dataset display)
        st.subheader("Check If Emails are formatted")
        email_col = st.selectbox(
            'Select Column having Emails reocrds to Check Email If in format',
            st.session_state.df.columns,
            key='email_inspector_select'
        )

        col_series = st.session_state.df[email_col]
        non_null_series = col_series.dropna()

        if non_null_series.empty:
            st.info("The selected column has no non-empty values to inspect.")
        else:
            raw_str_series = non_null_series.astype(str)
            missing_tokens = {'', 'nan', 'none', 'null', 'na', 'n/a', '<na>'}
            active_entries = raw_str_series[~raw_str_series.str.strip().str.lower().isin(missing_tokens)]

            if active_entries.empty:
                st.info("No text entries found to check.")
            else:
                invalid_mask = ~active_entries.str.match(validation.EMAIL_REGEX, na=False)
                invalid_entries = active_entries[invalid_mask]

                if not invalid_entries.empty:
                    st.warning(f"Found {len(invalid_entries):,} non-standard or improper email values:")
                    improper_df = pd.DataFrame({
                        "Row Number (Dataset Index)": invalid_entries.index,
                        "Improper Email Value": invalid_entries.values
                    })
                    st.dataframe(improper_df, use_container_width=True)
                else:
                    st.info("All inspected values match standard email formatting.")
    else:
        st.info("Please upload a CSV file.")

elif work == '2.Outlier Management':
    if st.session_state.df is not None:
        numeric_cols = st.session_state.df.select_dtypes(include=np.number).columns.tolist()

        if not numeric_cols:
            st.warning("No numeric columns found in this dataset to perform outlier operations.")
        else:
            feature = st.selectbox('Select your feature', numeric_cols)
            selected_method = st.selectbox('Select your method', methods1)

            selected_submethod = None
            k = 1.5

            if selected_method == 'Z-score':
                selected_submethod = st.selectbox('Select your Z-score method: ', submethods1)
            elif selected_method == 'IQR score':
                k = st.slider('Select your IQR multiplier: ', 0.0, 5.0, value=1.5, step=0.01, format='%.2f')

            col_series = st.session_state.df[feature]
            clean_series = col_series.dropna()

            if len(clean_series) < 2:
                st.warning("Not enough data points to detect outliers.")
                outlier_mask = pd.Series(False, index=st.session_state.df.index)
            elif selected_method == 'Z-score':
                std_dev = clean_series.std()
                if std_dev == 0 or np.isnan(std_dev):
                    st.warning("All numeric values in this column are identical. Outlier detection cannot be applied.")
                    outlier_mask = pd.Series(False, index=st.session_state.df.index)
                else:
                    z_score = (col_series - clean_series.mean()) / std_dev
                    if selected_submethod == 'Records Above +3σ and below -3σ':
                        outlier_mask = ~z_score.between(-3, 3)
                    elif selected_submethod == 'Records Above +2σ and below -2σ':
                        outlier_mask = ~z_score.between(-2, 2)
                    elif selected_submethod == 'Records Above +1σ and below -1σ':
                        outlier_mask = ~z_score.between(-1, 1)
                    else:
                        outlier_mask = pd.Series(False, index=st.session_state.df.index)
            elif selected_method == 'IQR score':
                q1 = clean_series.quantile(0.25)
                q3 = clean_series.quantile(0.75)
                iqr = q3 - q1
                if iqr == 0:
                    st.warning(
                        "The spread (IQR) is zero because the middle values are identical. Try using Z-score instead.")
                    outlier_mask = pd.Series(False, index=st.session_state.df.index)
                else:
                    min_range = q1 - (k * iqr)
                    max_range = q3 + (k * iqr)
                    outlier_mask = ~col_series.between(min_range, max_range)
            else:
                outlier_mask = pd.Series(False, index=st.session_state.df.index)

            outlier_mask = outlier_mask & col_series.notna()

            fig = plot_outlier_distribution(
                st.session_state.df,
                feature,
                is_outlier_mask=outlier_mask,
                is_preview=True
            )
            st.pyplot(fig, use_container_width=True, dpi=300)
            plt.close(fig)

            original_rows = len(st.session_state.df)
            removed_count = int(outlier_mask.sum())
            kept_count = original_rows - removed_count

            st.info(
                f"Keeping **{kept_count:,}** out of **{original_rows:,}** records (Filtered **{removed_count:,}** outliers).")

            if st.button('Apply Changes'):
                filtered_df = st.session_state.df[~outlier_mask].copy()
                st.session_state.df = filtered_df
                st.success('Outliers successfully filtered.')

                if not st.session_state.ignore_schema_warnings:
                    schema = validation.build_schema_from_df(st.session_state.df)
                    is_valid, failures = validation.validate_df(st.session_state.df, schema)
                    if not is_valid and failures is not None:
                        st.warning(f"Post-cleaning validation: {len(failures)} issues found")
                        st.dataframe(failures, use_container_width=True)
                st.rerun()

            st.markdown("---")
            st.caption('Current Dataset Version:')
            st.dataframe(st.session_state.df, use_container_width=True)
            st.caption(f"Shape: {st.session_state.df.shape}")
    else:
        st.info("Please upload a CSV file.")

if work == '3.Encoding':
    if st.session_state.df is not None:
        feature = st.selectbox('Select your feature', st.session_state.df.columns)
        val_counts = st.session_state.df[feature].value_counts(dropna=False)
        unique_count = len(val_counts)
        total_records = len(st.session_state.df)
        st.write(f'Category breakdown for **{feature}**')
        st.dataframe(st.session_state.df[feature].value_counts(dropna=False))
        st.write(f'There are **{unique_count}** unique values in **{feature}** having **{total_records}** records.')
        methods2 = st.selectbox('Select how you want to encode', methods2)

        mapping_dict = {}
        unique_categories = val_counts.index.tolist()

        if methods2 == 'Encode randomly':
            for idx, cat in enumerate(unique_categories):
                mapping_dict[cat] = idx

            mapping_display = pd.DataFrame(list(mapping_dict.items()), columns=['Categories', 'Assigned_Values'])
            st.write('Data has been Encoded')
            st.dataframe(mapping_display)

            if st.button('Apply Changes'):
                st.session_state.df = Encode(st.session_state.df, feature, mapping_dict)
                st.success(f'Feature {feature} has been encoded.')
                st.rerun()

        elif methods2 == 'Encode in manual Order':
            if unique_count > 60:
                st.warning(
                    f"**{feature}** contains {unique_count} unique categories (> 60). Too many unique values for manual mapping. Please use 'Encode randomly'.")
            else:
                grid_cols = st.columns(2)
                for idx, cat in enumerate(unique_categories):
                    col_target = grid_cols[idx % 2]
                    cat_label = 'NaN (missing values)' if pd.isnull(cat) else str(cat)
                    assigned_val = col_target.number_input(
                        f'{cat_label}',
                        value=idx,
                        min_value=0,
                        max_value=max(0, unique_count - 1),
                        key=f'manual_enc_{feature}_{idx}'
                    )
                    mapping_dict[cat] = assigned_val

                if st.button('Apply Changes'):
                    st.session_state.df = Encode(st.session_state.df, feature, mapping_dict)
                    st.success(f'Feature {feature} has been encoded.')
                    st.rerun()

        st.caption('Current Dataset Version:')
        st.dataframe(st.session_state.df)
        st.caption(st.session_state.df.shape)
    else:
        st.info("Please upload a CSV file.")