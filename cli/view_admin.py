# views/admin.py

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
import pandas as pd
from typing import List, Dict, Any

console = Console()

def _get_user_display_data(user_list: List[Dict[str, Any]]):
    """
    Internal helper to process a list of user objects into a Pandas DataFrame to dsplay.
    """
    if not user_list:
        return pd.DataFrame()
    
    data = []
    for user in user_list:
        data.append({
            'Username': user.get('username', 'N/A'),
            'Role': user.get('role', 'N/A'),
            'Status': 'Active' if user.get('enabled', True) else 'Inactive'
        })
    return pd.DataFrame(data)

def display_user_table(user_list: List[Dict[str, Any]]):
    df = _get_user_display_data(user_list)
    if df.empty:
        console.print(Panel("No user data available.", style="yellow"))
        return

    table = Table(
        title="User Directory",
        show_header=True,
        header_style="bold magenta",
        border_style="blue",
        box=box.DOUBLE
    )

    for col in df.columns:
        table.add_column(col, style="cyan", justify="left")

    for row in df.itertuples(index=False):
        row_list = list(row)
        
        status = row_list[-1]
        if status == 'Inactive':
            row_list[-1] = f"[red]{status}[/red]"
        elif status == 'Active':
            row_list[-1] = f"[green]{status}[/green]"
            
        table.add_row(*[str(item) for item in row_list])

    console.print(Panel.fit(
        "Displaying User Directory Table", 
        style="blue"
    ))
    console.print(table)
    return