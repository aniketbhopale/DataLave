import pandera as pa
import pandas as pd
import re

EMAIL_REGEX = r'^(?!\.)(?!.*\.\.)[a-zA-Z0-9._%+-]+(?<!\.)@(?!\.)(?!.*\.\.)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'


def is_actual_email_column(series: pd.Series, col_name: str) -> bool:

    col_clean = re.sub(r'[^a-z0-9]+', '_', col_name.lower()).strip('_')

    boolean_prefixes = (
        'has_', 'is_', 'can_', 'opt_', 'allow_', 'send_', 'sent_',
        'enable_', 'enabled_', 'disable_', 'disabled_', 'check_',
        'valid_', 'validated_', 'verified_', 'require_', 'required_',
        'needs_', 'need_', 'accept_', 'accepted_',
        'no_of_', 'num_', 'count_', 'total_'
    )

    boolean_suffixes = (
        '_flag', '_status', '_state', '_opt_in', '_opt_out', '_sent',
        '_verified', '_validated', '_valid', '_check', '_enabled',
        '_disabled', '_required', '_require', '_confirmed', '_bounced',
        '_opened', '_clicked', '_unsubscribed', '_count', '_num', '_total',
        '_at', '_date', '_time', '_timestamp', '_id', '_code', '_type', '_mode'
    )

    if col_clean.startswith(boolean_prefixes) or col_clean.endswith(boolean_suffixes):
        return False

    clean_samples = series.dropna().astype(str).str.strip()
    missing_tokens = {'', 'nan', 'none', 'null', 'na', 'n/a', '<na>'}
    clean_samples = clean_samples[~clean_samples.str.lower().isin(missing_tokens)].head(25)

    if clean_samples.empty:
        return False

    binary_tokens = {'0', '1', 't', 'f', 'true', 'false', 'y', 'n', 'yes', 'no'}
    unique_tokens = set(clean_samples.str.lower().unique())
    if unique_tokens.issubset(binary_tokens):
        return False

    match_ratio = clean_samples.str.contains(EMAIL_REGEX, regex=True).mean()
    return match_ratio >= 0.3


def build_schema_from_df(df: pd.DataFrame) -> pa.DataFrameSchema:
    columns = {}
    seen_cols = set()

    for col in df.columns:
        col_str = str(col)
        if col_str in seen_cols:
            continue
        seen_cols.add(col_str)

        series = df[col]

        if pd.api.types.is_numeric_dtype(series):
            columns[col] = pa.Column(
                dtype=float,
                nullable=True,
                coerce=True,
                required=False
            )
        elif pd.api.types.is_string_dtype(series) or series.dtype == 'object':
            if 'email' in col_str.lower() and is_actual_email_column(series, col_str):
                columns[col] = pa.Column(
                    dtype=str,
                    checks=pa.Check.str_matches(EMAIL_REGEX),
                    nullable=True,
                    coerce=True,
                    required=False
                )
            else:
                columns[col] = pa.Column(
                    nullable=True,
                    required=False
                )
        else:
            columns[col] = pa.Column(
                nullable=True,
                required=False
            )

    return pa.DataFrameSchema(columns, strict=False)


def validate_df(df: pd.DataFrame, schema: pa.DataFrameSchema):
    if df is None or df.empty:
        return True, None
    try:
        schema.validate(df, lazy=True)
        return True, None
    except pa.errors.SchemaErrors as err:
        return False, err.failure_cases