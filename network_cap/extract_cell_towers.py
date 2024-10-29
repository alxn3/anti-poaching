import pyshark
import requests

# Scrape pcap for all cell towers
cell_towers = []  # each element is a 4-tuple: cell identity, tracking area code, MCC, MNC
visited_towers = set()
cap = pyshark.FileCapture('test.pcap')
for packet in cap:
    if 'lte_rrc' in packet:
        rrc_layer = packet.lte_rrc
        
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

# Get cell tower's location
cellid, tac, mcc, mnc = cell_towers[0]
print(cell_towers[0])

# API_KEY = open('opencellid_api_key.txt', 'r').readline()
# payload = f"key={API_KEY}&mcc={mcc}&mnc={mnc}&lac={tac}&cellid={cellid}"
# url = f"https://opencellid.org/cell/get?{payload}"

# print(url)
# res = requests.post(url)
# print(res.text)