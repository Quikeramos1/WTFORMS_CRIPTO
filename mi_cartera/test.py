from models import CoinAPIHandler, Movement
import sqlite3
import datetime
'''
criptomoneda_origen = "EUR" 
criptomoneda_salida = "BTC"

coin_api_handler = CoinAPIHandler()

conectar = coin_api_handler.get_exchange_rate(criptomoneda_origen, criptomoneda_salida)

print(conectar)
'''

def get_all_purchases():
        query = """
        SELECT  fecha_actual, hora_actual, tipo_operacion, criptomoneda_origen,
            cantidad_origen, criptomoneda_salida, cantidad_salida, id
        FROM movements
        WHERE tipo_operacion = 'Compra';
        """
        conn = sqlite3.connect('data/movements.db')
        cur = conn.cursor()
        cur.execute(query)
        res = cur.fetchall()
        conn.close()

        purchases = []

        for row in res:
            fecha_actual_str, hora_actual_str, tipo_operacion, criptomoneda_origen, \
                cantidad_origen, criptomoneda_salida, cantidad_salida, id = row

            fecha_actual = fecha_actual_str
            hora_actual = hora_actual_str

            purchase = Movement(fecha_actual, tipo_operacion, criptomoneda_origen,
                                cantidad_origen, criptomoneda_salida, cantidad_salida, id)
            purchases.append(purchase)

        return purchases

prueba = get_all_purchases()

print(prueba)