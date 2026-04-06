from flask import Flask, render_template, request, redirect
import json
import os
from datetime import datetime

app = Flask(__name__)

ARCHIVO = "datos.json"

def cargar():
    if os.path.exists(ARCHIVO):
        with open(ARCHIVO) as f:
            return json.load(f)
    return {"ingresos": [], "gastos": []}

def guardar(data):
    with open(ARCHIVO, "w") as f:
        json.dump(data, f, indent=4)

def quincena(fecha):
    return "Q1" if int(fecha.split("-")[2]) <= 15 else "Q2"

@app.route("/")
def index():
    data = cargar()
    return render_template("index.html", data=data)

@app.route("/agregar", methods=["POST"])
def agregar():
    data = cargar()

    tipo = request.form["tipo"]
    monto = float(request.form["monto"])
    fecha = request.form["fecha"]

    if tipo == "ingreso":
        data["ingresos"].append({
            "monto": monto,
            "fecha": fecha,
            "quincena": quincena(fecha)
        })
    else:
        nombre = request.form["nombre"]
        data["gastos"].append({
            "nombre": nombre,
            "monto": monto,
            "fecha": fecha,
            "quincena": quincena(fecha)
        })

    guardar(data)
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)