import subprocess
import sys

def check_dependencies():
    required = {'numpy', 'pandas', 'matplotlib'}
    for p in required:
        try:
            __import__(p)
        except ImportError:
            print(f"Installing missing dependency: {p}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", p])
            print(f"{p} installed successfully.")

def _camp_to_df(camp_manager):
    check_dependencies()
    import pandas as pd

    camps = camp_manager.read_all()
    if not camps:
        return pd.DataFrame()
    
    data = []
    for camp in camps:
        total_campers = len(camp.campers)
        current_stock = camp.current_food_stock

        data.append({
            'Name': camp.name,
            'Location': camp.location,
            'Number of Campers': total_campers,
            'Total Food Stock': current_stock
        })

    return pd.DataFrame(data)

def check_if_empty(camp_manager):
    df = _camp_to_df(camp_manager)
    if df.empty:
        print("No data to plot")
        return
    return df

def plot_food_stock(camp_manager): 
    check_dependencies()
    import matplotlib.pyplot as plt

    df = check_if_empty(camp_manager)
    if df is None: return

    plt.figure(figsize=(10, 6))
    plt.bar(df['Name'], df['Total Food Stock'], color = 'skyblue')
    plt.xlabel('Camp Name')
    plt.ylabel('Total Food Stock')
    plt.title('Total Food Stock per Camp')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def plot_campers_per_camp(camp_manager):
    check_dependencies()
    import matplotlib.pyplot as plt

    df = check_if_empty(camp_manager)
    if df is None: return

    plt.figure(figsize=(10, 6))
    plt.bar(df['Name'], df['Number of Campers'], color='lightgreen')
    plt.xlabel('Camp Name')
    plt.ylabel('Number of Campers')
    plt.title('Number of Campers per Camp')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    
def plot_camp_location_distribution(camp_manager):
    check_dependencies()
    import matplotlib.pyplot as plt

    df = check_if_empty(camp_manager)
    if df is None: return

    location_counts = df['Location'].value_counts()
    plt.figure(figsize=(8, 8))
    plt.pie(location_counts, labels=location_counts.index, autopct='%1.1f%%', startangle=140)
    plt.title('Distribution of Camps by Geographical Area')
    plt.show()