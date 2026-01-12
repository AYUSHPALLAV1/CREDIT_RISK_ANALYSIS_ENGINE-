import pandas as pd
import os

# List files in your dataset folder
dataset_path = os.path.join(os.getcwd(), "data", "raw")
print("Files in dataset:", os.listdir(dataset_path))

# Load the dataset (adjust filename as needed)
csv_path = os.path.join(dataset_path, "application_record.csv")
df = pd.read_csv(csv_path)  # or .data, .txt
print("\nDataset shape:", df.shape)
print("\nFirst few rows:")
print(df.head())
print("\nColumn names:")
print(df.columns.tolist())
print("\nData types:")
print(df.dtypes)
print("\nBasic statistics:")
print(df.describe())