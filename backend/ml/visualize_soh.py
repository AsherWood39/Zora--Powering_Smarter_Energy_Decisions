import pandas as pd
import matplotlib.pyplot as plt
import os

# Use absolute paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEATS_PATH = os.path.join(BASE_DIR, "ml/results/final_features.csv")

def visualize_soh():
    if not os.path.exists(FEATS_PATH):
        print(f"Error: {FEATS_PATH} not found.")
        return
        
    df = pd.read_csv(FEATS_PATH)
    
    plt.figure(figsize=(12, 8))
    
    # Identify unique batteries
    batteries = df['battery_id'].unique()
    
    # Highlight specific "worst" batteries if they exist
    highlight = ['B0036', 'B0038', 'B0041', 'B0045']
    
    for bid in batteries:
        subset = df[df['battery_id'] == bid]
        linestyle = '-'
        linewidth = 1
        alpha = 0.5
        
        if bid in highlight:
            linestyle = '--'
            linewidth = 3
            alpha = 1
            plt.plot(subset['cycle_number'], subset['SoH_Global'], label=f"{bid} (Outlier)", linestyle=linestyle, linewidth=linewidth, alpha=alpha)
        else:
            plt.plot(subset['cycle_number'], subset['SoH_Global'], alpha=alpha)

    plt.title('Zora SOH Fleet Analysis — Capacity Degradation Trends')
    plt.xlabel('Cycle Number')
    plt.ylabel('SoH (%)')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    output_img = os.path.join(BASE_DIR, 'ml/results/soh_fleet_degradation.png')
    plt.savefig(output_img, dpi=150)
    print(f"[DONE] Fleet visualization saved to {output_img}")

if __name__ == "__main__":
    visualize_soh()
