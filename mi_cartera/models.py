import sqlite3, os, requests
from dotenv import load_dotenv
from flask import flash, abort
load_dotenv()

#lo uso en la funcion get_all_coins y lo dejo accesible para añadir o quitar en el futuro
CURRENCIES = [ "ETH", "BNB", "ADA", "DOT", "BTC", "USDT", "XRP", "SOL", "MATIC"]



def crea_db_si_no_existe():
    db_path = os.environ.get('FLASK_PATH_SQLITE')

    if not os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()


            with open('data/create.sql', 'r') as create_file:
                create_query = create_file.read()

            cur.executescript(create_query)

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error al crear la base de datos: {str(e)}")    
            return False    
    else:
        return True 
    
def try_db():
    db_path = os.environ.get('FLASK_PATH_SQLITE')

    if not os.path.exists(db_path):
        print("La base de datos no existe en la ruta especificada.")
        abort(500)

    try:
        # Intenta abrir la base de datos para comprobar si es accesible
        with open(db_path, 'r') as f:
            pass
    except Exception as e:
        print("Error al acceder a la base de datos:", str(e))
        print("La aplicación no puede continuar debido a un problema con la base de datos.")
        abort(500)

class Movement:
    def __init__(self, fecha_actual, hora_actual, tipo_operacion, criptomoneda_origen, cantidad_origen, criptomoneda_salida, cantidad_salida):
        self.fecha_actual = fecha_actual
        self.hora_actual = hora_actual
        self.tipo_operacion = tipo_operacion
        self.criptomoneda_origen = criptomoneda_origen
        self.cantidad_origen = float(cantidad_origen)
        self.criptomoneda_salida = criptomoneda_salida
        self.cantidad_salida = float(cantidad_salida) if cantidad_salida is not None else None
        
    @property
    def date(self):
        return self._date

    def to_dict(self):
        return {
            "date": self._date.strftime("%Y-%m-%d"),
            "fecha_actual": self.fecha_actual,
            "hora_actual": self.hora_actual,
            "tipo_operacion": self.tipo_operacion,
            "criptomoneda_origen": self.criptomoneda_origen,
            "cantidad_origen": self.cantidad_origen,
            "criptomoneda_salida": self.criptomoneda_salida,
            "cantidad_salida": self.cantidad_salida,
        }

    def validate(self):
        errores = []
    
        if self.cantidad_origen <= 0:
            errores.append("Debe introducir una cantidad positiva.")  
        if self.tipo_operacion == "Intercambio" and self.criptomoneda_origen == "EUR":
            errores.append("Solo puede realizar intercambios entre cryptomonedas.") 
        if self.tipo_operacion == "Intercambio" and self.criptomoneda_salida == "EUR":
            errores.append("Solo puede realizar intercambios entre cryptomonedas.")    
        if self.tipo_operacion == "Compra" and self.criptomoneda_salida == "EUR":
            errores.append("No puedes comprar Euros. ")
        if self.tipo_operacion == "Venta" and self.criptomoneda_origen == "EUR":
            errores.append("La moneda 'EUR' no puede ser vendida.")
        if self.tipo_operacion == "Compra" and self.criptomoneda_origen != "EUR":
            errores.append("Solo puedes realizar compras con Euros")

        
        return errores
        

    def __repr__(self):
        return f"Movement: {self._date}- {self.hora_actual} - {self.tipo_operacion} - {self.criptomoneda_origen} - {self.cantidad_origen} - {self.criptomoneda_salida} - {self.cantidad_salida}"

class MovementDAOsqlite:
    def __init__(self, db_path):
        self.path = db_path
        self.coin_api_handler = CoinAPIHandler()
     

    def insert(self, movement):#almaceno operaciones con exito con esta funcion
        query = """
        INSERT INTO movements
               (fecha_actual, hora_actual, tipo_operacion, criptomoneda_origen,
                cantidad_origen, criptomoneda_salida, cantidad_salida)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        conn = sqlite3.connect(self.path)
        cur = conn.cursor()

        # Convertir fecha_actual y hora_actual en cadenas de texto en formato adecuado
        fecha_actual_str = movement.fecha_actual
        hora_actual_str = movement.hora_actual

        try:
            cur.execute(query, (fecha_actual_str, hora_actual_str,
                                movement.tipo_operacion, movement.criptomoneda_origen,
                                movement.cantidad_origen, movement.criptomoneda_salida,
                                movement.cantidad_salida))
            conn.commit()
            conn.close()
            return None 
        except sqlite3.Error as e:

            error_msg = f"Error al insertar el movimiento en la base de datos: {str(e)}"
            return error_msg
    
    def get_all(self, tipo_operacion=None):#Devuelve listado de todos los movimientos
        if tipo_operacion is None:
            query = """
            SELECT fecha_actual, hora_actual, tipo_operacion, criptomoneda_origen,
                   cantidad_origen, criptomoneda_salida, cantidad_salida
            FROM movements
            ORDER by fecha_actual;
            """
        else:
            query = """
            SELECT fecha_actual, hora_actual, tipo_operacion, criptomoneda_origen,
                   cantidad_origen, criptomoneda_salida, cantidad_salida
            FROM movements
            WHERE tipo_operacion = ?;
            """

        conn = sqlite3.connect(self.path)
        cur = conn.cursor()

        if tipo_operacion is None:
            cur.execute(query)
        else:
            cur.execute(query, (tipo_operacion,))

        res = cur.fetchall()

        lista = [Movement(*reg) for reg in res]

        conn.close()
        return lista
    
    def get_all_purchases(self): #obtengo listado de todas las compras (cripto + importe)
        return self.get_all("Compra")

    def get_all_sales(self): #obtengo listado de todas las ventas (cripto + importe)
        return self.get_all("Venta")

    def get_all_trading(self):#obtengo listado de todos los intercambios
        return self.get_all("Intercambio") 

    def get_total_por_operacion(self, tipo_operacion):
            try:
                if tipo_operacion not in ("Compra", "Venta", "Intercambio"):
                    raise ValueError("Tipo de operación no válido")

                query = f"""
                SELECT SUM(cantidad_origen) AS total
                FROM movements
                WHERE tipo_operacion = '{tipo_operacion}';
                """ if tipo_operacion != "Venta" else """
                SELECT SUM(cantidad_salida) AS total
                FROM movements
                WHERE tipo_operacion = 'Venta';
                """

                conn = sqlite3.connect(self.path)
                cur = conn.cursor()
                cur.execute(query)
                resultado = cur.fetchone()
                total = resultado[0] if resultado[0] is not None else 0

                cur.close()
                conn.close()

                return total
            except sqlite3.Error as e:
                print("Error al acceder a la base de datos:", e)
                return 0   

    def total_invertido(self):#Calculo el importe total en € que el invertido
        return self.get_total_por_operacion("Compra")

    def total_vendido(self):#Calculo el importe total en € que he vendido
        return self.get_total_por_operacion("Venta")
    
    
    def total_criptomoneda_por_compra(self):
        #aqui busco calcular todas las cryptomonedas compradas y su cantidad
        try:
            query = """
            SELECT criptomoneda_salida, SUM(cantidad_salida) as total_cantidad_salida
            FROM movements
            WHERE tipo_operacion = 'Compra'
            GROUP BY criptomoneda_salida;
            """
            conn = sqlite3.connect(self.path)
            cur = conn.cursor()
            cur.execute(query)

            resultados = cur.fetchall()

            total_por_criptomoneda_salida = {}

            for row in resultados:
                criptomoneda_salida = row[0]
                total_cantidad_salida = row[1]

                total_por_criptomoneda_salida[criptomoneda_salida] = total_cantidad_salida

            cur.close()
            conn.close()

            return total_por_criptomoneda_salida
        except sqlite3.Error as e:
            print("Error al acceder a la base de datos:", e)
            return None
        
    def intercambio_salida(self):
        #aqui busco calcular todas las cryptomonedas obtenidas por intercambios y su valor
        try:
            query = """
            SELECT criptomoneda_salida, SUM(cantidad_salida) as total_cantidad_salida
            FROM movements
            WHERE tipo_operacion = 'Intercambio'
            GROUP BY criptomoneda_salida;
            """
            conn = sqlite3.connect(self.path)
            cur = conn.cursor()
            cur.execute(query)

    
            resultados = cur.fetchall()

          
            intercambio_salida_list = []

  
            for row in resultados:
                criptomoneda_salida = row[0]
                total_cantidad_salida = row[1]

                
                intercambio_salida_list.append((criptomoneda_salida, total_cantidad_salida))

            cur.close()
            conn.close()

            return intercambio_salida_list
        except sqlite3.Error as e:
            print("Error al acceder a la base de datos:", e)
            return None
    
    def total_criptomonedas_ganadas(self):
        try:
            intercambio_salida = self.intercambio_salida()
            total_por_criptomoneda_salida = self.total_criptomoneda_por_compra()

            criptomonedas_ganadas = {}
            for criptomoneda, cantidad_ganada in intercambio_salida:
                criptomonedas_ganadas[criptomoneda] = cantidad_ganada

            for criptomoneda, cantidad_ganada in total_por_criptomoneda_salida.items():
                if criptomoneda in criptomonedas_ganadas:
                    criptomonedas_ganadas[criptomoneda] += cantidad_ganada
                else:
                    criptomonedas_ganadas[criptomoneda] = cantidad_ganada

            return criptomonedas_ganadas

        except Exception as e:
            print("Error al calcular las criptomonedas ganadas:", e)
            return None

    def total_criptomoneda_por_venta(self):
        #aqui busco calcular todas las cryptomonedas perdidas por ventas y sus cantidades
        try:
            query = """
            SELECT criptomoneda_origen, SUM(cantidad_origen) as total_cantidad_origen
            FROM movements
            WHERE tipo_operacion = 'Venta'
            GROUP BY criptomoneda_origen;
            """
            conn = sqlite3.connect(self.path)
            cur = conn.cursor()
            cur.execute(query)

           
            resultados = cur.fetchall()

         
            total_por_criptomoneda_origen = {}

           
            for row in resultados:
                criptomoneda_origen = row[0]
                total_cantidad_origen = row[1]

                total_por_criptomoneda_origen[criptomoneda_origen] = total_cantidad_origen

            
            cur.close()
            conn.close()

            return total_por_criptomoneda_origen
        except sqlite3.Error as e:
            print("Error al acceder a la base de datos:", e)
            return None  

    def intercambio_origen(self):
        #aqui busco controlar todas las cryptomonedas perdidas por intercambio y sus cantidades
        try:
            query = """
            SELECT criptomoneda_origen, SUM(cantidad_origen) as total_cantidad_origen
            FROM movements
            WHERE tipo_operacion = 'Intercambio'
            GROUP BY criptomoneda_origen;
            """
            conn = sqlite3.connect(self.path)
            cur = conn.cursor()
            cur.execute(query)

          
            resultados = cur.fetchall()

            intercambio_origen = {}


            for row in resultados:
                criptomoneda_origen = row[0]
                total_cantidad_origen = row[1]

                
                intercambio_origen[criptomoneda_origen] = total_cantidad_origen

            
            cur.close()
            conn.close()

            return intercambio_origen
        except sqlite3.Error as e:
            print("Error al acceder a la base de datos:", e)
            return None
        
    def total_criptomonedas_perdidas(self):
        #combino en un solo diccionario todas las cryptomonedas perdidas
        try:
            intercambio_origen = self.intercambio_origen()
            total_por_criptomoneda_origen = self.total_criptomoneda_por_venta()

            
            criptomonedas_perdidas = {}
            for criptomoneda, cantidad_perdida in intercambio_origen.items():
                criptomonedas_perdidas[criptomoneda] = cantidad_perdida

            for criptomoneda, cantidad_perdida in total_por_criptomoneda_origen.items():
                if criptomoneda in criptomonedas_perdidas:
                    criptomonedas_perdidas[criptomoneda] += cantidad_perdida
                else:
                    criptomonedas_perdidas[criptomoneda] = cantidad_perdida

            return criptomonedas_perdidas

        except Exception as e:
            print("Error al calcular las criptomonedas perdidas:", e)
            return None
    
    def diferencia_criptomonedas_perdidas_ganadas(self):
        try:
            criptomonedas_perdidas = self.total_criptomonedas_perdidas()
            criptomonedas_ganadas = self.total_criptomonedas_ganadas()

           
            diferencia_criptomonedas = {}

            for criptomoneda, cantidad_perdida in criptomonedas_perdidas.items():
                diferencia_criptomonedas[criptomoneda] = cantidad_perdida

            for criptomoneda, cantidad_ganada in criptomonedas_ganadas.items():
                if criptomoneda in diferencia_criptomonedas:
                    diferencia_criptomonedas[criptomoneda] += cantidad_ganada
                else:
                    diferencia_criptomonedas[criptomoneda] = +cantidad_ganada
            #elimino las criptomonedas con valor 0
            diferencia_criptomonedas = {moneda: cantidad for moneda, cantidad in diferencia_criptomonedas.items() if cantidad != 0}

            return diferencia_criptomonedas

        except Exception as e:
            print("Error al calcular la diferencia de criptomonedas perdidas y ganadas:", e)
            return None
        
    def calcular_valor_euros_wallet(self, estado_wallet):
        coin_api_handler = CoinAPIHandler()
        valor_en_euros_dic = {}

        exchange_rates_to_eur = coin_api_handler.get_all_coins()

        if exchange_rates_to_eur is not None:
            for criptomoneda, cantidad in estado_wallet.items():
                if criptomoneda in exchange_rates_to_eur:
                    exchange_rate = exchange_rates_to_eur[criptomoneda]
                    valor_en_euros = cantidad / exchange_rate
                    valor_en_euros_dic[criptomoneda] = valor_en_euros
                else:
                    flash(f"No se pudo obtener el tipo de cambio para {criptomoneda}")
        else:
            # si falla la llamda anterior a get_all_coins, utilizo esta como respaldo
            for criptomoneda, cantidad in estado_wallet.items():
                exchange_rate = coin_api_handler.get_exchange_rate(criptomoneda, 'EUR')
                if exchange_rate is not None:
                    valor_en_euros = cantidad * exchange_rate
                    valor_en_euros_dic[criptomoneda] = valor_en_euros
                else:
                    flash(f"No se pudo obtener el tipo de cambio para {criptomoneda}")

        return valor_en_euros_dic

class Valida_transaccion:
    def __init__(self, dao, fecha_actual, hora_actual, tipo_operacion, criptomoneda_origen, cantidad_origen, criptomoneda_salida, cantidad_salida):
        self.dao = dao
        self.fecha_actual = fecha_actual
        self.hora_actual = hora_actual
        self.tipo_operacion = tipo_operacion
        self.criptomoneda_origen = criptomoneda_origen
        self.cantidad_origen = float(cantidad_origen)
        self.criptomoneda_salida = criptomoneda_salida
        self.cantidad_salida = float(cantidad_salida) if cantidad_salida is not None else None

    def validar_venta(self):
        errores = []
        if self.tipo_operacion == "Venta" and self.criptomoneda_salida != "EUR":
            errores.append("Sólo puedes vender por Euros.")
        if self.tipo_operacion == "Venta" or self.tipo_operacion == "Intercambio":
            criptomonedas_perdidas_ganadas = self.dao.diferencia_criptomonedas_perdidas_ganadas()
            if self.criptomoneda_origen not in criptomonedas_perdidas_ganadas:
                errores.append("No dispones de esta Moneda y por lo tanto no puede ser vendida o Intercambiada.")
            else:
                cantidad_disponible = criptomonedas_perdidas_ganadas[self.criptomoneda_origen]
                if self.cantidad_origen > cantidad_disponible:
                    errores.append("No dispones de suficientes fondos, introduce una cantidad menor.")
        
        return errores
        
class CoinAPIHandler:
    def __init__(self):
        self.coin_api_key = os.environ.get('FLASK_COIN_API_KEY')


    def get_all_coins(self):
        url = f"https://rest.coinapi.io/v1/exchangerate/EUR?apikey={self.coin_api_key}"

        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if "rates" in data:
                    required_coins = CURRENCIES
                    exchange_rates_to_eur = {coin: None for coin in required_coins}

                    for rate_data in data["rates"]:
                        symbol = rate_data.get("asset_id_quote")
                        if symbol in exchange_rates_to_eur:
                            exchange_rates_to_eur[symbol] = rate_data.get("rate")

                    return exchange_rates_to_eur
            else:
                print(f'Error en la solicitud: {response.status_code}')
                return None
        except requests.exceptions.RequestException as e:
            print(f'Error en la solicitud: {str(e)}')
            return None
        
    def get_exchange_rate(self, criptomoneda_origen, criptomoneda_salida):
        url = f"https://rest.coinapi.io/v1/exchangerate/{criptomoneda_origen}/{criptomoneda_salida}?apikey={self.coin_api_key}"
        try:
            response = requests.get(url)
            data = response.json()
            if response.status_code == 200:
                return data['rate']
            else:
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener los datos: {str(e)}")
            return None

    def process_transaction(self, tipo_operacion, criptomoneda_origen, cantidad_origen, criptomoneda_salida, cantidad_salida):
        exchange_rate = self.get_exchange_rate(criptomoneda_origen, criptomoneda_salida)
        if cantidad_salida is None:
            return False, "Debes pulsar el botón 'Consultar' para finalizar correctamente la operación."
        
        if exchange_rate is None:
            return False, "Ha habido un error al procesar la operación."

        if tipo_operacion == "Compra":
                return True, "Compra realizada exitosamente."

        elif tipo_operacion == "Venta":
                return True, "Venta realizada exitosamente."

        elif tipo_operacion == "Intercambio":
            return True, "Intercambio realizado exitosamente."

    def obtener_icono_criptomoneda(self, criptomoneda):
        
        if criptomoneda == 'BTC':
            return 'BTC.png'
        elif criptomoneda == 'ETH':
            return 'ETH.png'
        elif criptomoneda == 'BNB':
            return 'BNB.png'
        elif criptomoneda == 'ADA':
            return 'ADA.png'
        elif criptomoneda == 'DOT':
            return 'DOT.png'
        elif criptomoneda == 'USDT':
            return 'USDT.png'
        elif criptomoneda == 'XRP':
            return 'XRP.png'
        elif criptomoneda == 'SOL':
            return 'SOL.png'
        elif criptomoneda == 'MATIC':
            return 'MATIC.png'
        else:
            return 'default.png'  