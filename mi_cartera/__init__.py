from flask import Flask, render_template
import csv

app = Flask(__name__)
app.config.from_prefixed_env()