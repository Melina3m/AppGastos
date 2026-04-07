from flask import Flask, render_template, request, redirect
import psycopg2
import os

app = Flask(__name__)

# 🔑 conexión a la BD (Render usa esta variable automáticamente)
DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL)

# 🧠 lógica quincena
def quincena(fecha):
    return "Q1" if int(fecha.split("-")[2]) <= 15 else "Q2"

# 🧱 crear tablas (solo si no existen)
def crear_tablas():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ingresos (
        id SERIAL PRIMARY KEY,
        monto FLOAT,
        fecha DATE,
        quincena TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS gastos (
        id SERIAL PRIMARY KEY,
        nombre TEXT,
        monto FLOAT,
        fecha DATE,
        quincena TEXT
    );
    """)

    conn.commit()
    cur.close()
    conn.close()

crear_tablas()

# 🏠 HOME
@app.route("/")
def index():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT fecha, nombre, monto, quincena FROM gastos ORDER BY fecha DESC")
    gastos = cur.fetchall()

    cur.execute("SELECT fecha, monto, quincena FROM ingresos ORDER BY fecha DESC")
    ingresos = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("index.html", gastos=gastos, ingresos=ingresos)

# ➕ AGREGAR
@app.route("/agregar", methods=["POST"])
def agregar():
    tipo = request.form["tipo"]
    monto = float(request.form["monto"])
    fecha = request.form["fecha"]
    q = quincena(fecha)

    conn = get_conn()
    cur = conn.cursor()

    if tipo == "ingreso":
        cur.execute(
            "INSERT INTO ingresos (monto, fecha, quincena) VALUES (%s, %s, %s)",
            (monto, fecha, q)
        )
    else:
        nombre = request.form["nombre"]
        cur.execute(
            "INSERT INTO gastos (nombre, monto, fecha, quincena) VALUES (%s, %s, %s, %s)",
            (nombre, monto, fecha, q)
        )

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/")

# 🚀 RUN
if __name__ == "__main__":
    app.run()