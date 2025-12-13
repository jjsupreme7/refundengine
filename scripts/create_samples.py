"""Create 25-row sample files for testing."""
import pandas as pd
import os

output_dir = 'C:/Users/jacob/Desktop/Files-Refund-Engine/test_samples'
os.makedirs(output_dir, exist_ok=True)

# Use different random_state for new sample (99 instead of 42)
SEED = 99

# 1. Denodo Sales Tax - rows with invoice + no Recon Analysis (KOM comments)
print('=== DENODO SALES TAX 2024 ===')
df = pd.read_excel('C:/Users/jacob/Desktop/Files-Refund-Engine/Final 2024 Denodo Review.xlsb',
                   sheet_name='2024 Sales Tax_WIP', engine='pyxlsb')
has_inv = df['Inv 1 File Name'].notna() & (df['Inv 1 File Name'].astype(str).str.strip() != '')
has_kom = df['Recon Analysis'].notna() & (df['Recon Analysis'].astype(str).str.strip() != '')
df_filtered = df[has_inv & ~has_kom]
print(f'Filtered rows available: {len(df_filtered):,}')

sample = df_filtered.sample(n=min(25, len(df_filtered)), random_state=SEED)
out_path = os.path.join(output_dir, 'Denodo_Sample_25_v3.xlsx')
sample.to_excel(out_path, index=False)
print(f'Saved: {out_path} ({len(sample)} rows)')

# 2. Use Tax 2023 - rows with invoice + INDICATOR contains 'Remit' + no KOM
print()
print('=== USE TAX 2023 ===')
df = pd.read_excel('C:/Users/jacob/Desktop/Files-Refund-Engine/Phase_3_2023_Use Tax_10-17-25.xlsx',
                   sheet_name='2023_WIP')
has_inv = df['Inv-1 File Name'].notna() & (df['Inv-1 File Name'].astype(str).str.strip() != '')
has_kom = df['KOM Analysis & Notes'].notna() & (df['KOM Analysis & Notes'].astype(str).str.strip() != '')
is_remit = df['INDICATOR'].astype(str).str.lower().str.contains('remit', na=False)
df_filtered = df[has_inv & ~has_kom & is_remit]
print(f'Filtered rows available: {len(df_filtered):,}')

sample = df_filtered.sample(n=min(25, len(df_filtered)), random_state=SEED)
out_path = os.path.join(output_dir, 'UseTax_2023_Sample_25_v3.xlsx')
sample.to_excel(out_path, index=False)
print(f'Saved: {out_path} ({len(sample)} rows)')

# 3. Use Tax 2024 - rows with invoice + INDICATOR contains 'Remit' + no KOM
print()
print('=== USE TAX 2024 ===')
df = pd.read_excel('C:/Users/jacob/Desktop/Files-Refund-Engine/Phase_3_2024_Use Tax_10-17-25.xlsx',
                   sheet_name='2024_WIP')
has_inv = df['Inv-1 File Name'].notna() & (df['Inv-1 File Name'].astype(str).str.strip() != '')
has_kom = df['KOM Analysis & Notes'].notna() & (df['KOM Analysis & Notes'].astype(str).str.strip() != '')
is_remit = df['INDICATOR'].astype(str).str.lower().str.contains('remit', na=False)
df_filtered = df[has_inv & ~has_kom & is_remit]
print(f'Filtered rows available: {len(df_filtered):,}')

sample = df_filtered.sample(n=min(25, len(df_filtered)), random_state=SEED)
out_path = os.path.join(output_dir, 'UseTax_2024_Sample_25_v3.xlsx')
sample.to_excel(out_path, index=False)
print(f'Saved: {out_path} ({len(sample)} rows)')

print()
print('Done! Created 3 new sample files (25 rows each, seed=99).')
