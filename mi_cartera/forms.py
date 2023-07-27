from flask_wtf import FlaskForm
from wtforms import SelectField, DecimalField, SubmitField
from wtforms.validators import InputRequired, DataRequired
from wtforms.fields import DateField, TimeField, FloatField
from datetime import datetime 


class PurchaseForm(FlaskForm):
    
    fecha_actual = DateField("Fecha actual:", validators=[InputRequired()])

    hora_actual = TimeField("Hora actual:", validators=[InputRequired()])

    tipo_operacion = SelectField("Compra, Venta o Intercambio:",
            choices=[
              ("", "-- ¿Que operación deseas realizar? --"),
              ("Compra", "Compra"),
              ("Venta", "Venta"),
              ("Intercambio", "Intercambio")
            ],
            validators=[InputRequired()])
    
    criptomoneda_origen = SelectField("From:",
            choices=[
              ("", "-- Seleccionar Moneda --"),
              ("EUR", "EUR"),("ETH", "ETH"),
              ("BNB", "BNB"),("ADA", "ADA"),
              ("DOT", "DOT"),("BTC", "BTC"),
              ("USDT", "USDT"),("XRP", "XRP"),
              ("SOL", "SOL"),("MATIC", "MATIC")],
            validators=[InputRequired()])
    
    cantidad_origen = DecimalField("Cantidad de Origen:",
            validators=[InputRequired()])
    
    criptomoneda_salida = SelectField("To:", 
            choices=[
              ("", "-- Seleccionar Moneda --"),
              ("EUR", "EUR"),("ETH", "ETH"),
              ("BNB", "BNB"),("ADA", "ADA"),
              ("DOT", "DOT"),("BTC", "BTC"),
              ("USDT", "USDT"),("XRP", "XRP"),
              ("SOL", "SOL"),("MATIC", "MATIC")],
            validators=[DataRequired()])
    
    cantidad_salida = FloatField("Cantidad de Salida",
            render_kw={"placeholder":"Presiona el botón 'Consultar' para obtener la cantidad de salida"},
            validators=[InputRequired()])

    obtener_tipo_cambio = SubmitField("Consultar") 

    ejecutar = SubmitField("Ejecutar")

class Views(FlaskForm):
    
    tipo_vista = SelectField("Elige la vista que prefieras:",
            choices=[
              ("Todo","Todo"),
              ("Compra", "Compra"),
              ("Venta", "Venta"),
              ("Intercambio", "Intercambio")
            ],
            validators=[InputRequired()])
    aceptar = SubmitField("aceptar")
    