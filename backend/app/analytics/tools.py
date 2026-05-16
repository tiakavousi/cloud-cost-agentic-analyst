import os
import pandas as pd
import matplotlib
# Force matplotlib to use a non-interactive backend suited for server scripts
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, Optional

# Set a premium look for all generated plots
sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (10, 6)

def load_dataset(filepath: str) -> pd.DataFrame:
    """Safely reads the cloud billing dataset into memory."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Target data resource not found at: {filepath}")
    return pd.read_csv(filepath)


def get_data_profile(filepath: str, action_type: str = "summary") -> str:
    """
    Handles Tabular EDA requests like viewing data previews or descriptive statistics.
    Valid action_types: 'summary', 'head', 'tail'
    """
    try:
        df = load_dataset(filepath)
        
        if action_type == "head":
            return df.head(10).to_string()
        elif action_type == "tail":
            return df.tail(10).to_string()
        else:
            # Generate descriptive statistics summary
            summary_stats = df.describe(include='all').to_string()
            info_str = f"Dataset Dimensions: {df.shape[0]} rows, {df.shape[1]} columns\n\n"
            return info_str + summary_stats
            
    except Exception as e:
        return f"Execution Error inside get_data_profile: {str(e)}"


def calculate_aggregates(filepath: str, operation: str, target_column: str, group_by_column: Optional[str] = None) -> str:
    """
    Handles Mathematical & Calculation requests.
    Calculates metrics (sum, mean, max, min) globally or grouped by a dimension.
    """
    try:
        df = load_dataset(filepath)
        
        if target_column not in df.columns:
            return f"Error: Column '{target_column}' does not exist in dataset."
            
        # Clean column values if numeric operation is chosen
        if operation in ["sum", "mean", "max", "min"]:
            df[target_column] = pd.to_numeric(df[target_column], errors='coerce')
        
        # Scenario A: Grouped Aggregation
        if group_by_column:
            if group_by_column not in df.columns:
                return f"Error: Grouping dimension '{group_by_column}' does not exist."
            
            grouped = df.groupby(group_by_column)[target_column].agg(operation).reset_index()
            # Sort for clean presentation
            grouped = grouped.sort_values(by=target_column, ascending=False)
            return grouped.to_string(index=False)
            
        # Scenario B: Global Dataset Calculation
        else:
            result = df[target_column].agg(operation)
            return f"Calculated global {operation} for {target_column}: {result}"
            
    except Exception as e:
        return f"Execution Error inside calculate_aggregates: {str(e)}"


def generate_visualization(filepath: str, chart_type: str, x_col: str, y_col: str, output_dir: str = "data/charts") -> Dict[str, Any]:
    """
    Handles Visual EDA requests.
    Generates a chart using matplotlib/seaborn and stores the static asset to local storage.
    """
    try:
        df = load_dataset(filepath)
        os.makedirs(output_dir, exist_ok=True)
        filename = "generated_chart.png"
        output_path = os.path.join(output_dir, filename)
        
        # Enforce numeric alignment on the Y axis metrics
        df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
        
        # Reset any lingering plotting threads
        plt.close('all')
        fig, ax = plt.subplots()
        
        # Dynamic plot routing engine
        if chart_type == "bar":
            # For clean charts, aggregate and sort before plotting if categories get messy
            summary_df = df.groupby(x_col)[y_col].sum().reset_index().sort_values(by=y_col, ascending=False).head(10)
            sns.barplot(data=summary_df, x=x_col, y=y_col, ax=ax, palette="Blues_d")
            plt.xticks(rotation=45, ha='right')
            
        elif chart_type == "line":
            # Great for tracking chronologically across 'Usage_Date'
            summary_df = df.groupby(x_col)[y_col].sum().reset_index()
            sns.lineplot(data=summary_df, x=x_col, y=y_col, marker="o", ax=ax, color="#1890ff", linewidth=2.5)
            plt.xticks(rotation=45, ha='right')
            
        elif chart_type == "pie":
            summary_df = df.groupby(x_col)[y_col].sum().reset_index().sort_values(by=y_col, ascending=False).head(5)
            ax.pie(summary_df[y_col], labels=summary_df[x_col], autopct='%1.1f%%', colors=sns.color_palette("Pastel1"))
            ax.axis('equal')
            
        else:
            return {"success": False, "error": f"Unsupported chart format configuration: {chart_type}"}
        
        # Beautify layouts programmatically
        ax.set_title(f"{chart_type.capitalize()} Chart: Distribution of {y_col} by {x_col}", fontsize=14, pad=15, weight='bold')
        plt.tight_layout()
        
        # Save output image asset
        plt.savefig(output_path, bbox_inches='tight', dpi=150)
        plt.close('all')
        
        return {"success": True, "filename": filename, "error": None}
        
    except Exception as e:
        plt.close('all')
        return {"success": False, "filename": None, "error": str(e)}