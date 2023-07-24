import sqlite3, os, requests, datetime
from datetime import date
from dotenv import load_dotenv
load_dotenv()


CURRENCIES = ["EUR", "ETH", "BNB", "ADA", "DOT", "BTC", "USDT", "XRP", "SOL", "MATIC"]

def get_rate(criptomoneda_origen, criptomoneda_salida):
    coin_api_key = os.environ.get('FLASK_Coin_Api_key')
    url =f"https://rest.coinapi.io/v1/exchangerate/{criptomoneda_origen}/{criptomoneda_salida}?apikey={coin_api_key}"
    try:
        response = requests.get(url)
        data = response.json()
        if response.status_code == 200:
            return data['rate']
            
        
        else:
            return False, data["error"]
    except requests.exceptions.RequestException as e:
        print(f"Error al obtenerlos datos: {str(e)}")
        return False, str(e)

def crea_db_si_no_existe():
    try:
        if not os.path.exists('data/movements.db'):
            # Conectar con la base de datos SQLite
            conn = sqlite3.connect('data/movements.db')
            cur = conn.cursor()

            # Leer el contenido del archivo "create.sql"
            with open('data/create.sql', 'r') as create_file:
                create_query = create_file.read()

            # Ejecutar el contenido del archivo "create.sql" para crear la tabla "movements"
            cur.executescript(create_query)

            # Guardar los cambios en la base de datos y cerrar la conexión
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
        self.cantidad_salida = float(cantidad_salida) if cantidad_salida else None

    @property
    def date(self):
        return self._date

    def to_dict(self):
        return {
            "date": self._date.strftime("%Y-%m-%d"),
            "tipo_operacion": self.tipo_operacion,
            "criptomoneda_origen": self.criptomoneda_origen,
            "cantidad_origen": self.cantidad_origen,
            "criptomoneda_salida": self.criptomoneda_salida,
            "cantidad_salida": self.cantidad_salida,
        }

    def validate(self):
        errors = []
        if self._date > date.today():
            errors.append("Date must be today or lower.")
        if self.tipo_operacion not in ["Compra", "Venta", "Intercambio"]:
            errors.append("Invalid operation type.")
        if self.criptomoneda_origen not in CURRENCIES:
            errors.append("Invalid origin cryptocurrency.")
        if self.criptomoneda_salida not in CURRENCIES:
            errors.append("Invalid output cryptocurrency.")
        if self.cantidad_origen <= 0:
            errors.append("Amount must be positive.")
        if self.cantidad_salida is not None and self.cantidad_salida <= 0:
            errors.append("Output amount must be positive.")

        return errors

    def __repr__(self):
        return f"Movement: {self._date} - {self.tipo_operacion} - {self.criptomoneda_origen} - {self.cantidad_origen} - {self.criptomoneda_salida} - {self.cantidad_salida}"


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
        
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()
        cur.execute(query)
        conn.close()

    def insert(self, movement):
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

        cur.execute(query, (fecha_actual_str, hora_actual_str,
                            movement.tipo_operacion, movement.criptomoneda_origen,
                            movement.cantidad_origen, movement.criptomoneda_salida,
                            movement.cantidad_salida))
        conn.commit()
        conn.close()

    def get(self, id):
        query = """
        SELECT fecha_actual, hora_actual, tipo_operacion, criptomoneda_origen,
               cantidad_origen, criptomoneda_salida, cantidad_salida, id
          FROM movements
         WHERE id = ?;
        """
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()
        cur.execute(query, (id,))
        res = cur.fetchone()
        conn.close()
        if res:
            # Suponiendo que tu modelo de datos es la clase Movement
            fecha_actual_str, hora_actual_str, tipo_operacion, criptomoneda_origen, \
                cantidad_origen, criptomoneda_salida, cantidad_salida, id = res

            fecha_actual = datetime.strptime(fecha_actual_str, '%Y-%m-%d').date()
            hora_actual = datetime.strptime(hora_actual_str, '%H:%M:%S').time()

            return Movement(fecha_actual, tipo_operacion, criptomoneda_origen,
                            cantidad_origen, criptomoneda_salida, cantidad_salida, id)

    def get_all(self):
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
        if exchange_rate is None:
            return False, "No se pudo obtener el tipo de cambio."

        if tipo_operacion == "Compra":
            # Lógica para manejar una compra (actualizar la base de datos, calcular balances, etc.)
            # Aquí puedes implementar la lógica para realizar la compra y guardarla en la base de datos.
            return True, "Compra realizada exitosamente."

        elif tipo_operacion == "Venta":
            # Lógica para manejar una venta (actualizar la base de datos, calcular balances, etc.)
            # Aquí puedes implementar la lógica para realizar la venta y guardarla en la base de datos.
            return True, "Venta realizada exitosamente."

        elif tipo_operacion == "Intercambio":
            # Lógica para manejar un intercambio (actualizar la base de datos, calcular balances, etc.)
            # Aquí puedes implementar la lógica para realizar el intercambio y guardarla en la base de datos.
            return True, "Intercambio realizado exitosamente."

        else:
            return False, "Operación no válida. Por favor, seleccione 'Compra', 'Venta' o 'Intercambio'."
