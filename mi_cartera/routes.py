from mi_cartera import app
from mi_cartera.models import MovementDAOsqlite, try_db, Movement, CoinAPIHandler, Valida_transaccion
from flask import render_template, request, redirect, flash
import datetime as dt
from mi_cartera.forms import PurchaseForm, Views
from decimal import Decimal

dao = MovementDAOsqlite(app.config.get("PATH_SQLITE"))


@app.before_request
def before_request():
    try_db()

@app.errorhandler(500)
def internal_server_error(e):
    return "Error interno del servidor. La aplicación no puede continuar debido a un problema con la base de datos, reinicia la aplicación.", 500




def get_tipo_vista():
    form = Views()
    if request.method == "POST" and form.validate_on_submit():
        return form.tipo_vista.data
    else:
        return "Todos"


@app.route("/", methods=["POST", "GET"])
def index():
    tipo_vista = get_tipo_vista()
    form = Views()  
    
    try:
        if tipo_vista == "Venta":
            movements = dao.get_all_sales()
        elif tipo_vista == "Compra":
            movements = dao.get_all_purchases()
        elif tipo_vista == "Intercambio":
            movements = dao.get_all_trading()
        else:
            movements = dao.get_all()
        return render_template("index.html", form=form, the_movements=movements, title="Todos", tipo_vista=tipo_vista)
    except ValueError as e:
        flash(str(e), "error")
        return render_template("index.html", form=form, the_movements=movements, title="Todos", tipo_vista=tipo_vista)
    

@app.route("/purchase", methods=["GET", "POST"])
def purchase():
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
                flash(error, 'error')
            return render_template("purchase.html", form=form)
        
        if "limpiar" in request.form:
            
            return redirect("purchase")
        
        elif "obtener_tipo_cambio" in request.form: 

            movimiento = Movement(fecha_actual, hora_actual, tipo_operacion, criptomoneda_origen, cantidad_origen,
                        criptomoneda_salida, cantidad_salida)
        
            errores = movimiento.validate()
            
            
            if not errores:
                exchange_rate = coin_api_handler.get_exchange_rate(criptomoneda_origen, criptomoneda_salida)
                
                if exchange_rate is not None:
                        
                    cantidad_origen_decimal = Decimal(cantidad_origen)  
                    
                    exchange_rate_decimal = Decimal(exchange_rate)  
                    
                    cantidad_salida_calculada = cantidad_origen_decimal * exchange_rate_decimal
                    form.cantidad_salida.dada = cantidad_salida_calculada
                    form.cantidad_origen_readonly = True 
                else:
                    flash("No se pudo obtener el tipo de cambio.", 'error')
                       
            else:
                for error in errores:
                    flash(error, 'error')     

        
           
        elif 'ejecutar' in request.form:
            if cantidad_salida is None:
                flash("Por favor, pulsa el botón 'Consultar' para que se rellene el campo 'Cantidad de salida'.", 'error')
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

                success, message = coin_api_handler.process_transaction(tipo_operacion, criptomoneda_origen, cantidad_origen, criptomoneda_salida, cantidad_salida)

                if success:
                    dao.insert(Movement(fecha_actual, hora_actual, tipo_operacion, criptomoneda_origen, cantidad_origen,
                            criptomoneda_salida, cantidad_salida))
                    message = "La transacción se ha procesado correctamente."
                
                flash(message)
                return redirect("/")
        else:
            for error in errores:
                flash(error, 'error')
    return render_template("purchase.html", form=form)
   

@app.route("/status")
def status():
    coin_api_handler = CoinAPIHandler()
    precio_de_compra =  dao.total_invertido() - (-dao.total_vendido())
   

    total_criptomoneda_ganada = dao.total_criptomonedas_ganadas()
    total_criptomoneda_perdida = dao.total_criptomonedas_perdidas()
    estado_wallet = dao.diferencia_criptomonedas_perdidas_ganadas()
    valor_euros_wallet = dao.calcular_valor_euros_wallet(estado_wallet)
    valor_actual = sum(valor_euros_wallet.values())
    
    resultado_inversion= valor_actual - (-precio_de_compra)
    
    iconos_criptomonedas = {}
    for criptomoneda in estado_wallet.keys():
        icono = coin_api_handler.obtener_icono_criptomoneda(criptomoneda)
        iconos_criptomonedas[criptomoneda] = icono
    return render_template("status.html", 
                            total_criptomoneda_ganada=total_criptomoneda_ganada,
                            total_criptomoneda_perdida=total_criptomoneda_perdida,
                            precio_de_compra=precio_de_compra,
                            estado_wallet=estado_wallet,
                            valor_euros_wallet=valor_euros_wallet,
                            valor_actual=valor_actual,
                            resultado_inversion=resultado_inversion, iconos_criptomonedas=iconos_criptomonedas) 

