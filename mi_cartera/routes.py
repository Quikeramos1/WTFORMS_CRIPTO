from mi_cartera import app
from mi_cartera.models import MovementDAOsqlite, crea_db_si_no_existe, Movement, CoinAPIHandler
from flask import render_template, request, redirect, flash
import datetime as dt
from mi_cartera.forms import PurchaseForm
from decimal import Decimal

dao = MovementDAOsqlite(app.config.get("PATH_SQLITE"))



@app.route("/")
def index():
    try:
        movements = dao.get_all()
        return render_template("index.html", the_movements=movements, title="Todos")
    except ValueError as e:
        flash("Su fichero de datos está corrupto")
        flash(str(e))
        return render_template("index.html", the_movements=[], title="Todos")

    

@app.route("/purchase", methods=["GET", "POST"])
def purchase():
    crea_db_si_no_existe()
    coin_api_handler = CoinAPIHandler()
    form = PurchaseForm()

    if request.method == "GET":
        form.fecha_actual.data = dt.date.today()
        form.hora_actual.data = dt.datetime.now().time()

        return render_template("purchase.html", form=form)
    
    else:
        fecha_hora_actual = dt.datetime.now()
        fecha_actual = fecha_hora_actual.strftime('%Y-%m-%d')
        hora_actual = fecha_hora_actual.strftime('%H:%M:%S')
        tipo_operacion = form.tipo_operacion.data
        criptomoneda_origen = form.criptomoneda_origen.data
        cantidad_origen = form.cantidad_origen.data
        criptomoneda_salida = form.criptomoneda_salida.data
        cantidad_salida = form.cantidad_salida.data

    
        if "obtener_tipo_cambio" in request.form:  # Se ha pulsado el botón "Consultar"
            exchange_rate = coin_api_handler.get_exchange_rate(criptomoneda_origen, criptomoneda_salida)
            
            if exchange_rate is not None:
                # Calcular la cantidad de salida en base al tipo de cambio obtenido
                cantidad_origen_decimal = Decimal(cantidad_origen)  # Convertir cantidad_origen a Decimal
                print("origen decimal")
                print(cantidad_origen_decimal)
                exchange_rate_decimal = Decimal(exchange_rate)  # Convertir exchange_rate a Decimal
                print("exchange decimal")
                print(exchange_rate_decimal)
                cantidad_salida_calculada = cantidad_origen_decimal * exchange_rate_decimal
                form.cantidad_salida.dada = cantidad_salida_calculada
                
                print(cantidad_salida_calculada)
            else:
                flash("No se pudo obtener el tipo de cambio.")
        elif 'ejecutar' in request.form:  # Se ha pulsado el botón "Ejecutar"
            # Procesar la transacción utilizando la clase CoinAPIHandler
            success, message = coin_api_handler.process_transaction(tipo_operacion, criptomoneda_origen, cantidad_origen, criptomoneda_salida, cantidad_salida)

            if success:
                dao.insert(Movement(fecha_actual, hora_actual, tipo_operacion, criptomoneda_origen, cantidad_origen,
                        criptomoneda_salida, cantidad_salida))

            # Redireccionar a la página de inicio con un mensaje flash
            flash(message)
            return redirect("/")
    return render_template("purchase.html", form=form)
   

@app.route("/status")
def status():
    criptomonedas = ["EUR", "ETH", "BNB", "ADA", "DOT", "BTC", "USDT", "XRP", "SOL", "MATIC"]
    balance = 1000  # Aquí puedes calcular el balance real
    valor_total = 2000  # Aquí puedes calcular el valor total de inversión

    return render_template("status.html", criptomonedas=criptomonedas, balance=balance, valor_total=valor_total)
