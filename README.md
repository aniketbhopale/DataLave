# DataLave — Tabular Data Cleaning & Preprocessing Suite

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Pandas](https://img.shields.io/badge/pandas-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![NumPy](https://img.shields.io/badge/NumPy-013243?logo=numpy&logoColor=white)](https://numpy.org/)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-11557C?logo=python&logoColor=white)](https://matplotlib.org/)
[![Seaborn](https://img.shields.io/badge/Seaborn-4C72B0?logo=python&logoColor=white)](https://seaborn.pydata.org/)

DataLave is an interactive preprocessing interface for tabular datasets. Instead of writing one-off scripts for standard exploratory cleaning, DataLave provides a dedicated UI to audit distributions, impute missing values, filter statistical outliers, and map categorical features with live row-diff feedback before committing changes and more.

## Data Flow

```mermaid

flowchart TD
    A["Raw CSV"] --> B["File Uploader"]
    B --> C[("Current Dataset<br/>Version")]
    C --> D{"Cleaning Step"}

    D -->|Main Menu| E["Dataset Info<br/>and Charts"]
    D -->|Nulls & Formatting| M1["1. Fill and<br/>Clean Nulls"]
    M1 --> F["Fill or Drop<br/>Missing Values"]
    M1 --> F2["Check Email<br/>Formatting"]
    D -->|Outliers| G["Z-Score<br/>or IQR"]
    D -->|Encoding| H["Automatic or<br/>Manual Mapping"]

    F --> I["Live Row Difference<br/>and Preview"]
    F2 --> I2["Flagged Emails<br/>and Their Rows"]
    G --> I
    H --> I

    I -->|Apply Changes| J["Update Current<br/>Version"]
    J --> C

```

## Core Capabilities

| Feature | What it handles | Technical details |
| --- | --- | --- |
| Dataset overview | Summarizes dataset structure | Computes total dimensions, missing cell percentage, duplicate rows, and in-memory footprint. |
| Visual inspection | Plots distributions and correlations | Generates 300 DPI charts for missing values, numeric spread (boxplot + KDE), Pearson correlation, and top categories. |
| Missing values | Drops dirty rows or fills them | Runs `dropna(subset=[col])` or imputes via column `mean`, `median`, `min`, or `max`. |
| Parametric outliers | Filters normal distributions | Standard cutoffs at $\pm 1\sigma, \pm 2\sigma,$ or $\pm 3\sigma$ using column mean and standard deviation. |
| Non-parametric outliers | Handles skewed numeric features | Dynamic IQR fences ($Q_1 - k \cdot \text{IQR}$ to $Q_3 + k \cdot \text{IQR}$) controlled with a $0.0$ to $5.0$ multiplier slider. |
| Row diff preview | Sanity-checks filters before saving | Shows exact row drop counts (`len(old) - len(new)`) without mutating the active working data. |
| Category breakdown | Summarizes discrete values | Calls `value_counts(dropna=False)` so missing rows show up as their own category rather than vanishing. |
| Integer encoding | Preps categories for models | Supports automatic indexing ($0$ to $n-1$) or a 2-column manual input grid for custom ordinal hierarchies. |

## Technology Stack

| Area | Tools |
| --- | --- |
| Web interface | [![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/) Wide layout, reactive state, column widgets |
| Data manipulation | [![Pandas](https://img.shields.io/badge/pandas-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/) Series transformations, quantiles, mapping dictionaries |
| Calculations | [![NumPy](https://img.shields.io/badge/NumPy-013243?logo=numpy&logoColor=white)](https://numpy.org/) Vectorized filtering and boolean masking |
| Visualization | [![Matplotlib](https://img.shields.io/badge/Matplotlib-3.7%2B-11557C?logo=python&logoColor=white)](https://matplotlib.org/) [![Seaborn](https://img.shields.io/badge/Seaborn-0.12%2B-4C72B0?logo=python&logoColor=white)](https://seaborn.pydata.org/) High-resolution 300 DPI distribution & correlation plots |

## Repository Structure

```text
DataLave/
├── DataLave.py          # Streamlit app and pipeline logic
├── requirements.txt     # Locked project dependencies
└── README.md            # Architecture specs and setup instructions
```

## Workflow

```mermaid

flowchart TD
    A["Upload CSV File"] --> B["Initialize Current<br/>Dataset Version"]
    B --> C["Choose Task<br/>from Sidebar"]

    C --> D["Main Menu"]
    C --> E["1. Fill and<br/>Clean Nulls"]
    C --> F["2. Outlier<br/>Management"]
    C --> G["3. Categorical<br/>Encoding"]

    D --> D1["Inspect Dataset Info<br/>and Column Cardinality"]
    D1 --> D2["Inspect Missing Values,<br/>Distributions, Correlations<br/>and Category Plots"]

    E --> E1["Select Column and<br/>Imputation or<br/>Drop Strategy"]
    E1 --> E2["Apply Changes"]

    E --> E3["Check Email<br/>Formatting"]
    E3 --> E4["Scan for Invalid<br/>Emails<br/>(Using Rules RFC 5321,<br/>5322, 1035, 1123)"]
    E4 --> E5["Display Flagged<br/>Row Indices and<br/>Improper Values"]

    F --> F1["Choose Z-Score<br/>or IQR"]
    F1 --> F2["Inspect Live<br/>Distribution: Kept<br/>Rows vs Outliers"]
    F2 --> F3["Review Rows<br/>Kept vs Removed"]
    F3 --> F4["Apply Changes"]

    G --> G1["Select Categorical<br/>Column"]
    G1 --> G2["Inspect Frequencies<br/>Including Missing<br/>Values"]
    G2 --> G3{"Encoding Type"}
    G3 -->|Automatic| G4["Assign Integer<br/>Indices from<br/>0 to n-1"]
    G3 -->|Manual Order| G5["Assign Integers<br/>Manually"]
    G4 --> G6["Apply Changes"]
    G5 --> G6

    E2 --> H[("Update Current<br/>Dataset Version")]
    F4 --> H
    G6 --> H
    H --> I["Re-render Live Shape<br/>and Data Table"]

```

### Transformation Module Breakdown

- **Main Menu:**
  - **Dataset Info:** Displays dimensions, missing cell percentage, exact duplicate rows, and memory footprint in MB.
  - **Column Description & Cardinality:** Audits each column for inferred data type, missing counts, unique counts, cardinality ratio, and sample values.
  - **Visualizations:** Renders 300 DPI charts for missing value percentages, numeric distribution & spread (boxplot + KDE), Pearson correlation heatmaps, and top categorical frequencies.
- **1. Fill and Clean Nulls:** Target a specific column to drop null records (`dropna(subset=[col])`) or fill missing positions using standard column metrics (`mean`, `median`, `min`, `max`).
- **2. Outlier Management:** 
  - **Z-Score:** Fast standard deviation cutoffs ($\pm 1\sigma, \pm 2\sigma, \pm 3\sigma$) for bell-curved features.
  - **IQR Score:** Multiplier slider ($k \in [0.0, 5.0]$) to set fences past $Q_1$ and $Q_3$.
  - **Live Distribution Plot:** Dynamically updates a dual boxplot/stripplot and shared-bin histogram showing kept records in blue and removed outliers in red alongside exact row counts before committing.
- **3. Encoding:** Renders category frequencies via `value_counts(dropna=False)`.
  - **Encode randomly:** Loops through unique items and assigns auto-incremented integers from $0$ to $n-1$.
  - **Encode in manual Order:** Builds an alternating two-column widget layout (`idx % 2`) with distinct keys (`manual_enc_{feature}_{idx}`) to assign ordinal values without UI ID collisions.

## State Management & Function Contract

The **Current Dataset Version** represents the single active source of truth. Modular transformation functions receive copies of the data, compute modifications, and return a clean DataFrame only when the user commits an action.

| Function | Signature | Notes |
| --- | --- | --- |
| `clean_data()` | `(df, feature, method)` | Returns DataFrame copy with selected feature imputed or pruned. |
| `Outliers()` | `(df, feature, methods1, submethods1, k)` | Slices DataFrame within numeric boundaries; returns filtered copy. |
| `plot_outlier_distribution()` | `(df, feature, is_outlier_mask, is_preview)` | Renders 300 DPI figure comparing kept records to removed outliers. |
| `Encode()` | `(df, feature, mapping_dict)` | Runs `.map(mapping_dict)` across selected column; returns encoded copy. |

## Local Setup & Installation

1. Set up a virtual environment:

   **Windows (PowerShell):**
   ```powershell
   py -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

   **macOS / Linux:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

## Launching the App

```bash
streamlit run DataLave.py
```

## Notes to be taken

- Transformations run on isolated DataFrame copies (`df.copy()`) inside utility functions so dataset mutations remain predictable.
- Figures render at 300 DPI via `mpl.rcParams` and `st.pyplot(..., dpi=300)` so charts stay sharp when zoomed.
- Missing values in Module 3 are intentionally kept in the frequency view to avoid unhandled float conversion errors during encoding.
- Large CSV uploads may hit default file-size ceilings. Configure `server.maxUploadSize` in `.streamlit/config.toml` if you plan to process files larger than 200MB.
