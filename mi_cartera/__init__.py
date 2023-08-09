from flask import Flask
from mi_cartera.models import crea_db_si_no_existe

app = Flask(__name__)
app.config.from_prefixed_env()

crea_db_si_no_existe()

