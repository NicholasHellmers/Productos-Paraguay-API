import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Convert csv file to excel file
df = pd.read_csv('./output/data/products_arete.csv')
df.to_excel('./output/data/products_arete.xlsx', index=False, header=True)

# Convert csv file to excel file
df = pd.read_csv('./output/data/products_casarica_con.csv')
df.to_excel('./output/data/products_casarica.xlsx', index=False, header=True)

# Convert csv file to excel file
df = pd.read_csv('./output/data/products_stock.csv')
df.to_excel('./output/data/products_stock.xlsx', index=False, header=True)

# Convert csv file to excel file
df = pd.read_csv('./output/data/products_superseis.csv')
df.to_excel('./output/data/products_superseis.xlsx', index=False, header=True)
