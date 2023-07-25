import sqlite3, os, requests
from datetime import date, datetime
from dotenv import load_dotenv
load_dotenv()


CURRENCIES = ["EUR", "ETH", "BNB", "ADA", "DOT", "BTC", "USDT", "XRP", "SOL", "MATIC"]



def crea_db_si_no_existe():
    try:
        if not os.path.exists('db_path'):
            conn = sqlite3.connect('db_path')
            cur = conn.cursor()

            with open('data/create.sql', 'r') as create_file:
                create_query = create_file.read()

            cur.executescript(create_query)

            conn.commit()
            conn.close()
    except Exception as e:
        print(f"Error al crear la base de datos: {str(e)}")        


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
        errors = []
    
        if self.cantidad_origen <= 0:
            errors.append("Debe introducir una cantidad positiva.")  
        if self.tipo_operacion == "Intercambio" and self.criptomoneda_origen == "EUR":
            errors.append("Solo puede realizar intercambios entre cryptomonedas.") 
        if self.tipo_operacion == "Intercambio" and self.criptomoneda_salida == "EUR":
            errors.append("Solo puede realizar intercambios entre cryptomonedas.")    
        if self.tipo_operacion == "Compra" and self.criptomoneda_salida == "EUR":
            errors.append("No puedes comprar Euros. ")
        if self.tipo_operacion == "Venta" and self.criptomoneda_origen == "EUR":
            errors.append("La moneda 'EUR' no puede ser vendida.")

        
        return errors
        

    def __repr__(self):
        return f"Movement: {self._date}- {self.hora_actual} - {self.tipo_operacion} - {self.criptomoneda_origen} - {self.cantidad_origen} - {self.criptomoneda_salida} - {self.cantidad_salida}"

    



class MovementDAOsqlite:
    def __init__(self, db_path):
        self.path = db_path

        query = """
        CREATE TABLE IF NOT EXISTS movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_actual TEXT NOT NULL,
            hora_actual TEXT NOT NULL,
            tipo_operacion TEXT NOT NULL,
            criptomoneda_origen TEXT NOT NULL,
            cantidad_origen REAL NOT NULL,
            criptomoneda_salida TEXT NOT NULL,
            cantidad_salida REAL
        );
        """
        
        

    def insert(self, movement):#almaceno movimientos con esta funcion
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
            return None  # No se produjo ningún error, retorna None indicando éxito
        except sqlite3.Error as e:
            # Algo salió mal, captura el error y retorna el mensaje de error para mostrar al usuario
            error_msg = f"Error al insertar el movimiento en la base de datos: {str(e)}"
            return error_msg
    
    def get_all(self):#obtengo todos los movimientos para mostrar en index.html
        query = """
        SELECT fecha_actual, hora_actual, tipo_operacion, criptomoneda_origen,
               cantidad_origen, criptomoneda_salida, cantidad_salida
          FROM movements
         ORDER by fecha_actual;
        """
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()
        cur.execute(query)
        res = cur.fetchall()

        lista = [Movement(*reg) for reg in res]

        conn.close()
        return lista    
    
    def get_all_purchases(self): #obtengo listado de todas las compras (cripto + importe)
        query = """
        SELECT id, fecha_actual, hora_actual, tipo_operacion, criptomoneda_origen,
            cantidad_origen, criptomoneda_salida, cantidad_salida
        FROM movements
        WHERE tipo_operacion = 'Compra';
        """
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()
        cur.execute(query)
        purchases = []

        for res in cur.fetchall():
            id, fecha_actual_str, hora_actual_str, tipo_operacion, criptomoneda_origen, \
            cantidad_origen, criptomoneda_salida, cantidad_salida = res

            fecha_actual = datetime.strptime(fecha_actual_str, '%Y-%m-%d').date()
            hora_actual = datetime.strptime(hora_actual_str, '%H:%M:%S').time()

            purchases.append({
                "id": id,
                "fecha_actual": fecha_actual,
                "hora_actual": hora_actual,
                "tipo_operacion": tipo_operacion,
                "criptomoneda_origen": criptomoneda_origen,
                "cantidad_origen": cantidad_origen,
                "criptomoneda_salida": criptomoneda_salida,
                "cantidad_salida": cantidad_salida
            })

        conn.close()
        return purchases

    def get_all_sales(self): #obtengo listado de todas las ventas (cripto + importe)
        query = """
        SELECT id, fecha_actual, hora_actual, tipo_operacion, criptomoneda_origen,
            cantidad_origen, criptomoneda_salida, cantidad_salida
        FROM movements
        WHERE tipo_operacion = 'Venta';
        """
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()
        cur.execute(query)
        sales = []

        for res in cur.fetchall():
            id, fecha_actual_str, hora_actual_str, tipo_operacion, criptomoneda_origen, \
            cantidad_origen, criptomoneda_salida, cantidad_salida = res

            fecha_actual = datetime.strptime(fecha_actual_str, '%Y-%m-%d').date()
            hora_actual = datetime.strptime(hora_actual_str, '%H:%M:%S').time()

            sales.append({
                "id": id,
                "fecha_actual": fecha_actual,
                "hora_actual": hora_actual,
                "tipo_operacion": tipo_operacion,
                "criptomoneda_origen": criptomoneda_origen,
                "cantidad_origen": cantidad_origen,
                "criptomoneda_salida": criptomoneda_salida,
                "cantidad_salida": cantidad_salida
            })

    def total_invertido(self):#Calculo el importe total en € que el invertido
        try:
            query = """
            SELECT SUM(cantidad_origen)
            FROM movements
            WHERE tipo_operacion = 'Compra';
            """
            conn = sqlite3.connect(self.path)
            cur = conn.cursor()
            cur.execute(query)
           
            resultado = cur.fetchone()
            total_compras = resultado[0] if resultado[0] is not None else 0

            cur.close()
            conn.close()

            return total_compras
        except sqlite3.Error as e:
            print("Error al acceder a la base de datos:", e)
            return 0

    def total_vendido(self):#Calculo el importe total en € que he vendido
        try:
            query = """
            SELECT SUM(cantidad_salida)
            FROM movements
            WHERE tipo_operacion = 'Venta';
            """
            conn = sqlite3.connect(self.path)
            cur = conn.cursor()
            cur.execute(query)
            # Obtener el resultado de la suma
            resultado = cur.fetchone()
            total_ventas = resultado[0] if resultado[0] is not None else 0

            # Cerrar cursor y conexión a la base de datos
            cur.close()
            conn.close()

            return total_ventas
        except sqlite3.Error as e:
            print("Error al acceder a la base de datos:", e)
            return 0
    
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

            # Obtener los resultados de la consulta
            resultados = cur.fetchall()

            # Crear una lista para almacenar las criptomonedas de salida y sus totales de cantidad_salida
            intercambio_salida_list = []

            # Procesar los resultados y almacenar las criptomonedas de salida y sus totales de cantidad_salida
            for row in resultados:
                criptomoneda_salida = row[0]
                total_cantidad_salida = row[1]

                # Agregar una tupla (criptomoneda_salida, total_cantidad_salida) a la lista
                intercambio_salida_list.append((criptomoneda_salida, total_cantidad_salida))

            # Cerrar cursor y conexión a la base de datos
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

            # Combinar los resultados en un solo diccionario
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

            # Obtener los resultados de la consulta
            resultados = cur.fetchall()

            # Crear un diccionario para almacenar los totales por criptomoneda_salida
            total_por_criptomoneda_origen = {}

            # Procesar los resultados y almacenar los totales por criptomoneda_salida
            for row in resultados:
                criptomoneda_origen = row[0]
                total_cantidad_origen = row[1]

                total_por_criptomoneda_origen[criptomoneda_origen] = total_cantidad_origen

            # Cerrar cursor y conexión a la base de datos
            cur.close()
            conn.close()

            return total_por_criptomoneda_origen
        except sqlite3.Error as e:
            print("Error al acceder a la base de datos:", e)
            return None  

    def intercambio_origen(self):
        #aqui busco controlar todas las cryptomonedas perdidas por intercamboo y sus cantidades
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

            # Obtener los resultados de la consulta
            resultados = cur.fetchall()

            # Crear un diccionario para almacenar los totales por criptomoneda_origen
            intercambio_origen = {}

            # Procesar los resultados y almacenar los totales por criptomoneda_origen
            for row in resultados:
                criptomoneda_origen = row[0]
                total_cantidad_origen = row[1]

                # Asignar el total_cantidad_origen al diccionario intercambio_origen
                intercambio_origen[criptomoneda_origen] = total_cantidad_origen

            # Cerrar cursor y conexión a la base de datos
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

            # Combinar los resultados en un solo diccionario
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
        if self.tipo_operacion == "Venta":
            criptomonedas_perdidas_ganadas = self.dao.diferencia_criptomonedas_perdidas_ganadas()
            if self.criptomoneda_origen not in criptomonedas_perdidas_ganadas:
                errores.append("No dispones de esta Moneda y por lo tanto no puede ser vendida.")
            else:
                cantidad_disponible = criptomonedas_perdidas_ganadas[self.criptomoneda_origen]
                if self.cantidad_origen > cantidad_disponible:
                    errores.append("No dispones de suficientes fondos, introduce una cantidad menor.")
        if self.tipo_operacion == "Intercambio":
            criptomonedas_perdidas_ganadas = self.dao.diferencia_criptomonedas_perdidas_ganadas()
            if self.criptomoneda_origen not in criptomonedas_perdidas_ganadas:
                errores.append("No dispones de esta Moneda y por lo tanto no puede ser Intercambiada.")
            else:
                cantidad_disponible = criptomonedas_perdidas_ganadas[self.criptomoneda_origen]
                if self.cantidad_origen > cantidad_disponible:
                    errores.append("No dispones de suficientes fondos, introduce una cantidad menor.")
        return errores
        
class CoinAPIHandler:
    def __init__(self):
        self.coin_api_key = os.environ.get('FLASK_Coin_Api_key')

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

        