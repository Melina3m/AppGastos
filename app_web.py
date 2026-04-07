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
    mes = request.args.get("mes")

    conn = get_conn()
    cur = conn.cursor()

    if mes:
        cur.execute("""
            SELECT fecha, nombre, monto, quincena 
            FROM gastos 
            WHERE EXTRACT(MONTH FROM fecha) = %s
            ORDER BY fecha DESC
        """, (mes,))
        
        cur.execute("""
            SELECT fecha, monto, quincena 
            FROM ingresos 
            WHERE EXTRACT(MONTH FROM fecha) = %s
            ORDER BY fecha DESC
        """, (mes,))
    else:
        cur.execute("SELECT fecha, nombre, monto, quincena FROM gastos ORDER BY fecha DESC")
        gastos = cur.fetchall()

        cur.execute("SELECT fecha, monto, quincena FROM ingresos ORDER BY fecha DESC")
        ingresos = cur.fetchall()

    gastos = cur.fetchall()
    ingresos = cur.fetchall()

    # 💰 cálculos
    total_ingresos = sum(i[1] for i in ingresos) if ingresos else 0
    total_gastos = sum(g[2] for g in gastos) if gastos else 0
    saldo = total_ingresos - total_gastos

    cur.close()
    conn.close()

    return render_template(
        "index.html",
        gastos=gastos,
        ingresos=ingresos,
        saldo=saldo,
        total_ingresos=total_ingresos,
        total_gastos=total_gastos
    )
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