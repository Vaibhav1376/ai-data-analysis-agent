import csv
import os
import tempfile
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd


def preprocess_and_save(
    file_source: Union[Any, str]
) -> Tuple[Optional[str], Optional[List[str]], Optional[pd.DataFrame]]:
    """Preprocess an uploaded file or local file path into a sanitized DataFrame,

    and persist it to a temporary CSV file formatted for DuckDB ingestion.

    Args:
        file_source: Streamlit UploadedFile object or a file path string.

    Returns:
        Tuple containing:
            - temp_path (str): Filepath to the temporary sanitized CSV.
            - columns (List[str]): List of column names.
            - df (pd.DataFrame): Sanitized pandas DataFrame.
    """
    try:
        # Determine filename and extension
        if hasattr(file_source, "name"):
            filename = file_source.name
        elif isinstance(file_source, str):
            filename = os.path.basename(file_source)
        else:
            filename = str(file_source)

        filename_lower = filename.lower()

        # Ingest file into pandas DataFrame
        if filename_lower.endswith(".csv"):
            df = pd.read_csv(
                file_source,
                encoding="utf-8",
                na_values=["NA", "N/A", "missing", "nan", "null", ""],
            )
        elif filename_lower.endswith((".xlsx", ".xls")):
            df = pd.read_excel(
                file_source,
                na_values=["NA", "N/A", "missing", "nan", "null", ""],
            )
        else:
            raise ValueError(
                f"Unsupported file format: {filename}. Please provide a .csv or .xlsx file."
            )

        # Standardize and sanitize column names
        df.columns = [str(col).strip() for col in df.columns]

        # Escape quotation marks in string/object columns for SQL and CSV safety
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].astype(str).replace({r'"': '""'}, regex=True)

        # Parse date and numeric columns automatically
        for col in df.columns:
            col_lower = str(col).lower()
            if any(k in col_lower for k in ["date", "time", "timestamp"]):
                try:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                except Exception:
                    pass
            elif df[col].dtype == "object":
                try:
                    # Attempt numeric conversion for numeric columns stored as text
                    converted = pd.to_numeric(df[col], errors="raise")
                    df[col] = converted
                except (ValueError, TypeError):
                    pass

        # Write sanitized DataFrame to an OS-safe temporary CSV file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
            temp_path = temp_file.name

        df.to_csv(temp_path, index=False, quoting=csv.QUOTE_ALL)
        return temp_path, df.columns.tolist(), df

    except Exception as e:
        return None, None, None


def get_dataset_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate structural and statistical metrics for a dataset.

    Args:
        df: Pandas DataFrame to summarize.

    Returns:
        Dictionary containing row count, column count, memory usage,
        column types, and missing value counts.
    """
    total_cells = df.shape[0] * df.shape[1] if df.shape[1] > 0 else 1
    total_missing = int(df.isna().sum().sum())
    missing_pct = round((total_missing / total_cells) * 100, 2)

    return {
        "rows": df.shape[0],
        "columns": df.shape[1],
        "total_missing": total_missing,
        "missing_percentage": missing_pct,
        "numeric_cols": len(df.select_dtypes(include=["number"]).columns),
        "categorical_cols": len(df.select_dtypes(include=["object"]).columns),
        "datetime_cols": len(df.select_dtypes(include=["datetime"]).columns),
        "memory_mb": float(round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)),
    }
