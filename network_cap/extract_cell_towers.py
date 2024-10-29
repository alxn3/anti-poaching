import pyshark
import json
import requests
import pandas as pd

MCC_MNC_TABLE = 'mcc_mnc_lookup.csv'
mcc_mnc_lookup = pd.read_csv("mcc_mnc_lookup.csv", index_col="MCC_MNC")

# Scrape pcap for all cell towers
cell_towers = []  # each element is a 4-tuple: cell identity, tracking area code, MCC, MNC
visited_towers = set()
cap = pyshark.FileCapture('test.pcap')
for packet in cap:
    if 'lte_rrc' in packet:
        rrc_layer = packet.lte_rrc
        print(rrc_layer.field_names)
        exit()

        cellidentity_hex = rrc_layer.lte_rrc_cellidentity
        cellidentity = int(cellidentity_hex.replace(":", ""), 16)
        
        trackingareacode_hex = rrc_layer.lte_rrc_trackingareacode
        trackingareacode = int(trackingareacode_hex.replace(":", ""), 16)

        mcc_mnc_str = "".join([digit.showname_value for digit in rrc_layer.lte_rrc_mcc_mnc_digit.all_fields])

        for i in range(0, len(mcc_mnc_str), 6):
            tower_tuple = (cellidentity, trackingareacode, int(mcc_mnc_str[i:i+3]), int(mcc_mnc_str[i+3:i+6]))
            if tower_tuple not in visited_towers:  # don't count duplicates
                visited_towers.add(tower_tuple)
                cell_towers.append(tower_tuple)

# Get location of one cell tower!
cellid, tac, mcc, mnc = cell_towers[3]
mcc_mnc_key = int(str(mcc) + str(mnc))
print(cell_towers[3])
print(mcc_mnc_lookup.loc[mcc_mnc_key, "CountryName"])
print(mcc_mnc_lookup.loc[mcc_mnc_key, "Network"])

# API_KEY = open('google_maps_api_key.txt', 'r').readline()
# url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={API_KEY}"
payload = {
    "radioType": "lte",
    "cellTowers": [
    {
      "cellId": cellid,
      "locationAreaCode": tac,
      "mobileCountryCode": mcc,
      "mobileNetworkCode": mnc
    }
  ]
}
# res = requests.post(url, json=payload)
# print(res.text)