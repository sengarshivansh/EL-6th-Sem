import pandas as pd

# 1. Load your messy mixed file
df = pd.read_csv("simulation_ready_data.csv")

print("Original Data Size:", len(df))
print("Columns found:", df.columns.tolist())

# 2. DEFINE THE METER COLUMN NAME
# Look at the print output above. Find the column that has IDs like 'BR02'.
# It is likely named 'meter_id', 'device_id', 'SmartMeterID', or simply 'id'.
# UPDATE THIS VARIABLE TO MATCH YOUR CSV COLUMN NAME:
meter_column_name = 'meter'  # <--- CHANGE THIS IF NEEDED

# 3. Filter for BR02
if meter_column_name in df.columns:
    br02_df = df[df[meter_column_name] == 'BR02'].copy()
    
    # Sort by time just to be safe
    # br02_df = br02_df.sort_values(by='timestamp') 
    
    print(f"Filtered BR02 Data Size: {len(br02_df)}")
    
    if len(br02_df) > 0:
        # Save the clean file
        br02_df.to_csv("BR02_final_data.csv", index=False)
        print("✅ Success! Saved as 'BR02_final_data.csv'")
    else:
        print("❌ Error: No rows found for 'BR02'. Check if the ID is spelled correctly (e.g., 'br02' vs 'BR02').")
else:
    print(f"❌ Error: Column '{meter_column_name}' not found in CSV.")