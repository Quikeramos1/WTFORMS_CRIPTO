from mi_cartera import app
from mi_cartera.models import MovementDAOsqlite, crea_db_si_no_existe, Movement
from flask import render_template, request, redirect, flash
import datetime as dt
from mi_cartera.forms import PurchaseForm

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
    form = PurchaseForm()

    if request.method == "GET":
        form.fecha_actual.data = dt.date.today()
        form.hora_actual.data = dt.datetime.now().time()

        return render_template("purchase.html", form=form)
    
    else:
        # Obtener la fecha y hora actuales
        fecha_hora_actual = dt.datetime.now()
        fecha_actual = fecha_hora_actual.strftime('%Y-%m-%d')
        hora_actual = fecha_hora_actual.strftime('%H:%M:%S')

        # Guardar el movimiento en la base de datos
        dao.insert(Movement(fecha_actual, hora_actual, form.tipo_operacion.data, form.criptomoneda_origen.data, form.cantidad_origen.data,
                            form.criptomoneda_salida.data, form.cantidad_salida.data))

        return redirect("/")
        
    

@app.route("/status")
def status():
    criptomonedas = ["EUR", "ETH", "BNB", "ADA", "DOT", "BTC", "USDT", "XRP", "SOL", "MATIC"]
    balance = 1000  # Aquí puedes calcular el balance real
    valor_total = 2000  # Aquí puedes calcular el valor total de inversión

    return render_template("status.html", criptomonedas=criptomonedas, balance=balance, valor_total=valor_total)
