from models import CoinAPIHandler, Movement, MovementDAOsqlite
import sqlite3
import datetime



criptomoneda_origen = "EUR" 
criptomoneda_salida = "BTC"

coin_api_handler = CoinAPIHandler()

conectar = coin_api_handler.get_exchange_rate(criptomoneda_origen, criptomoneda_salida)

print(conectar)
