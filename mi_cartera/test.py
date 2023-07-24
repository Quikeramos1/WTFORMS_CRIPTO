from models import CoinAPIHandler, get_rate

criptomoneda_origen = "EUR" 
criptomoneda_salida = "BTC"

coin_api_handler = CoinAPIHandler()

conectar = coin_api_handler.get_exchange_rate(criptomoneda_origen, criptomoneda_salida)
conectar1 = get_rate(criptomoneda_origen, criptomoneda_salida)
print(conectar)
print("otro")
print(conectar1)