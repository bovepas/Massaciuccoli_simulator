# test_geogpt.py
from geogpt_client import GeoGPTClient

client = GeoGPTClient()
print(client.chat("Quali dati contiene un CSV ambientale?"))
