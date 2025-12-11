import numpy as np
import pandas as pd
import plotext as plt
from rich.console import Console
from rich.panel import Panel
from rich import box
from cli.input_utils import get_input, wait_for_enter

# Global console instance
console = Console()

def _get_camp_df(camp_manager):
    """
    Fetch camp data and prepare DataFrame using Pandas.
    """
    camps = camp_manager.read_all()
    if not camps:
        return pd.DataFrame()
    
    data = []
    for camp in camps:
        current_stock = getattr(camp, 'current_food_stock', 0)
        data.append({
            'Name': camp.name,
            'Location': camp.location,
            'Number of Campers': len(camp.campers),
            'Total Food Stock': current_stock
        })

    return pd.DataFrame(data)

def _setup_plot_theme():
    """Configure plotext to look professional and blend with CLI."""
    plt.clear_figure()
    plt.theme('pro') 
    plt.grid(True, True)

def plot_food_stock(camp_manager): 
    """
    Visualises food stock using a Vertical Bar Chart in the terminal.
    """
    df = _get_camp_df(camp_manager)
    if df.empty:
        console.print(Panel("No data to plot.", style="yellow"))
        return

    # Pandas/Numpy Data Processing
    names = df['Name'].tolist()
    stocks = df['Total Food Stock'].tolist()

    _setup_plot_theme()
    
    plt.bar(names, stocks, color='blue', fill=True)
    plt.title("Total Food Stock per Camp")
    plt.xlabel("Camp Name")
    plt.ylabel("Food Stock")
    
    # Render in terminal
    console.print(Panel.fit("Displaying Food Stock Chart", style="blue"))
    plt.show()
    _wait_for_user()

def plot_campers_per_camp(camp_manager):
    """
    Visualises campers per camp using a Vertical Bar Chart.
    """
    df = _get_camp_df(camp_manager)
    if df.empty:
        console.print(Panel("No data to plot.", style="yellow"))
        return

    # Pandas/Numpy Data Processing
    names = df['Name'].tolist()
    campers = df['Number of Campers'].tolist()

    _setup_plot_theme()

    plt.bar(names, campers, color='green', fill=True)
    plt.title("Number of Campers per Camp")
    plt.xlabel("Camp Name")
    plt.ylabel("Camper Count")
    
    console.print(Panel.fit("Displaying Camper Count Chart", style="green"))
    plt.show()
    _wait_for_user()

def plot_camp_location_distribution(camp_manager):
    """
    Visualises location distribution using a Custom ASCII Horizontal Bar Chart.
    Manual rendering ensures every label is shown and bars are clearly separated.
    """
    df = _get_camp_df(camp_manager)
    if df.empty:
        console.print(Panel("No data to plot.", style="yellow"))
        return

    # NumPy Usage
    locations = np.array(df['Location'])
    unique_locs, counts = np.unique(locations, return_counts=True)
    
    # Sort descending
    sorted_idx = np.argsort(-counts)
    unique_locs = unique_locs[sorted_idx]
    counts = counts[sorted_idx]

    total = np.sum(counts)
    max_count = np.max(counts) if len(counts) > 0 else 1
    
    # Chart Configuration
    max_bar_width = 40
    label_width = max(len(str(loc)) for loc in unique_locs) + 2
    
    chart_lines = []
    chart_lines.append(f"[bold]Distribution by Location (n={total})[/bold]")
    chart_lines.append("─" * (label_width + max_bar_width + 10))

    for loc, count in zip(unique_locs, counts):
        # Calculate bar length
        bar_len = int((count / max_count) * max_bar_width)
        bar_str = "█" * bar_len
        percentage = (count / total) * 100
        
        # Format: Label | Bar Count (Pct)
        # Using rich formatting tags for color
        line = f"{loc:<{label_width}} [magenta]│ {bar_str}[/magenta] [yellow]{count}[/yellow] ({percentage:.1f}%)"
        chart_lines.append(line)
        chart_lines.append(f"{' ':<{label_width}} [magenta]│[/magenta]") # Spacer row with axis line

    chart_lines.append("─" * (label_width + max_bar_width + 10))

    panel = Panel(
        "\n".join(chart_lines),
        title="Location Distribution",
        border_style="magenta",
        box=box.ROUNDED
    )
    console.print(panel)
    _wait_for_user()

def _wait_for_user():
    print() # spacing
    wait_for_enter()