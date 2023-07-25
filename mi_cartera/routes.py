from mi_cartera import app
from mi_cartera.models import MovementDAOsqlite, crea_db_si_no_existe, Movement, CoinAPIHandler, Valida_transaccion
from flask import render_template, request, redirect, flash
import datetime as dt
from mi_cartera.forms import PurchaseForm
from decimal import Decimal

dao = MovementDAOsqlite(app.config.get("PATH_SQLITE"))



@app.route("/")
def index():
    crea_db_si_no_existe()
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
        
        cantidad_salida = form.cantidad_salida.data
        cantidad_salida = float(cantidad_salida) if cantidad_salida is not None else None
        validador_transaccion = Valida_transaccion(dao, fecha_actual, hora_actual, tipo_operacion, criptomoneda_origen, cantidad_origen,
                                                   criptomoneda_salida, cantidad_salida)
        errores_venta = validador_transaccion.validar_venta()
        if errores_venta:
            for error in errores_venta:
                flash(error)
            return render_template("purchase.html", form=form)
        
        

        if "obtener_tipo_cambio" in request.form: 

            movimiento = Movement(fecha_actual, hora_actual, tipo_operacion, criptomoneda_origen, cantidad_origen,
                        criptomoneda_salida, cantidad_salida)
        
            errores = movimiento.validate()
            
            
            if not errores:
                exchange_rate = coin_api_handler.get_exchange_rate(criptomoneda_origen, criptomoneda_salida)
            
                if exchange_rate is not None:
            
                    cantidad_origen_decimal = Decimal(cantidad_origen)  
                    print("origen decimal")
                    print(cantidad_origen_decimal)
                    exchange_rate_decimal = Decimal(exchange_rate)  
                    print("exchange decimal")
                    print(exchange_rate_decimal)
                    cantidad_salida_calculada = cantidad_origen_decimal * exchange_rate_decimal
                    form.cantidad_salida.dada = cantidad_salida_calculada
                    
                else:
                    flash("No se pudo obtener el tipo de cambio.")
            else:
                for error in errores:
                    flash(error)        
        elif 'ejecutar' in request.form:
            if cantidad_salida is None:
                flash("Por favor, ingresa un número válido en el campo 'Cantidad Salida'.")
            else:
                movimiento = Movement(fecha_actual, hora_actual, tipo_operacion, criptomoneda_origen, cantidad_origen,
                            criptomoneda_salida, cantidad_salida)
                errores = movimiento.validate()
                if not errores:
                    #convierto el importe invertido en compra en valor negativo
                    if tipo_operacion == "Compra":
                        cantidad_origen = -cantidad_origen
                    elif tipo_operacion == "Intercambio":
                        cantidad_origen = -cantidad_origen
                    elif tipo_operacion == "Venta":
                        cantidad_origen = -cantidad_origen


                # Procesar la transacción utilizando la clase CoinAPIHandler
                success, message = coin_api_handler.process_transaction(tipo_operacion, criptomoneda_origen, cantidad_origen, criptomoneda_salida, cantidad_salida)

                if success:
                    dao.insert(Movement(fecha_actual, hora_actual, tipo_operacion, criptomoneda_origen, cantidad_origen,
                            criptomoneda_salida, cantidad_salida))
                    message = "La transacción se ha procesado correctamente."
                # Redireccionar a la página de inicio con un mensaje flash
                flash(message)
                return redirect("/")
        else:
            for error in errores:
                flash(error)
    return render_template("purchase.html", form=form)
   

@app.route("/status")
def status():

    precio_de_compra =  dao.total_invertido() + dao.total_vendido()

    total_criptomoneda_ganada = dao.total_criptomonedas_ganadas()
    total_criptomoneda_perdida = dao.total_criptomonedas_perdidas()
    estado_wallet = dao.diferencia_criptomonedas_perdidas_ganadas()

    
    
   
    

    return render_template("status.html", 
                            total_criptomoneda_ganada=total_criptomoneda_ganada,
                            total_criptomoneda_perdida=total_criptomoneda_perdida,
                            precio_de_compra=precio_de_compra,
                            estado_wallet=estado_wallet) 