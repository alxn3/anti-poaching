import requests
from bs4 import BeautifulSoup
import pandas as pd

url = "https://www.vianett.com/en/prices/international-customers/prices-sms-bulk/mccmnc"

response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

tables = pd.read_html(str(soup))
for table in tables:
    if "MCC" in table.columns and "MNC" in table.columns:
        mcc_mnc_lookup = table[['MCC', 'MNC', 'CountryName', 'Network']]
        mcc_mnc_lookup['MCC_MNC'] = mcc_mnc_lookup['MCC'].astype(str) + mcc_mnc_lookup['MNC'].astype(str)
        mcc_mnc_lookup.set_index('MCC_MNC', inplace=True)
        break

print(mcc_mnc_lookup.head())
mcc_mnc_lookup.to_csv("mcc_mnc_lookup.csv")