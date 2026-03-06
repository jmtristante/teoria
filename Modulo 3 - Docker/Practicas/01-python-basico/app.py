import os
import pandas as pd

output_dir = os.getenv("OUTPUT_DIR", "/data")
os.makedirs(output_dir, exist_ok=True)

records = [
    {"id": 1, "cliente": "ACME", "importe": 1200.50},
    {"id": 2, "cliente": "Globex", "importe": 980.10},
    {"id": 3, "cliente": "Initech", "importe": 1430.00},
]

df = pd.DataFrame(records)
df["importe_con_iva"] = (df["importe"] * 1.21).round(2)

output_path = os.path.join(output_dir, "ventas_transformadas.csv")
df.to_csv(output_path, index=False)

print("Dataset de entrada:")
print(df[["id", "cliente", "importe"]])
print("\nDataset transformado:")
print(df)
print(f"\nArchivo generado en: {output_path}")
