from flask import Flask, render_template, request, redirect, session
import psycopg2
import os

app = Flask(__name__)
app.secret_key = "clave_secreta"

DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode='require')


def quincena(fecha):
    return "Q1" if int(fecha.split("-")[2]) <= 15 else "Q2"


def crear_tablas():
    conn = get_conn()
    cur = conn.cursor()

    # 👤 USUARIOS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT
    );
    """)

    # 💰 INGRESOS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ingresos (
        id SERIAL PRIMARY KEY,
        monto FLOAT,
        fecha DATE,
        quincena TEXT,
        user_id INT
    );
    """)

    # 💸 GASTOS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS gastos (
        id SERIAL PRIMARY KEY,
        nombre TEXT,
        monto FLOAT,
        fecha DATE,
        quincena TEXT,
        categoria TEXT,
        user_id INT
    );
    """)

    # 💳 DEUDAS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS deudas (
        id SERIAL PRIMARY KEY,
        user_id INT,
        total FLOAT
    );
    """)

    # 🔥 FIX AUTOMÁTICO (ESTO ES LO IMPORTANTE)
    cur.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='gastos' AND column_name='categoria'
        ) THEN
            ALTER TABLE gastos ADD COLUMN categoria TEXT;
        END IF;
    END $$;
    """)

    conn.commit()
    cur.close()
    conn.close()


crear_tablas()


@app.before_request
def require_login():
    rutas_publicas = ["/login", "/registro", "/static"]

    if not session.get("user_id"):
        if not any(request.path.startswith(r) for r in rutas_publicas):
            return redirect("/login")


# 🔐 LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        password = request.form["password"]

        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            "SELECT id FROM usuarios WHERE username=%s AND password=%s",
            (user, password)
        )
        result = cur.fetchone()

        cur.close()
        conn.close()

        if result:
            session["user_id"] = result[0]
            return redirect("/")

        return "Credenciales incorrectas"

    return render_template("login.html")


# 🧾 REGISTRO
@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        user = request.form["username"]
        password = request.form["password"]

        conn = get_conn()
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO usuarios (username, password) VALUES (%s, %s)",
                (user, password)
            )
            conn.commit()
        except:
            conn.rollback()
            cur.close()
            conn.close()
            return "El usuario ya existe"

        cur.close()
        conn.close()

        return redirect("/login")

    return render_template("registro.html")


# 🏠 HOME
@app.route("/")
def home():
    return redirect("/dashboard")


@app.route("/dashboard")
def index():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    mes = request.args.get("mes")

    conn = get_conn()
    cur = conn.cursor()

    try:
        if mes:
            cur.execute("""
                SELECT fecha, nombre, monto, quincena, COALESCE(categoria, 'Sin categoría')
                FROM gastos 
                WHERE user_id=%s AND EXTRACT(MONTH FROM fecha) = %s
                ORDER BY fecha DESC
            """, (user_id, mes))
            gastos = cur.fetchall()

            cur.execute("""
                SELECT fecha, monto, quincena 
                FROM ingresos 
                WHERE user_id=%s AND EXTRACT(MONTH FROM fecha) = %s
                ORDER BY fecha DESC
            """, (user_id, mes))
            ingresos = cur.fetchall()
        else:
            cur.execute("""
                SELECT fecha, nombre, monto, quincena, COALESCE(categoria, 'Sin categoría')
                FROM gastos 
                WHERE user_id=%s 
                ORDER BY fecha DESC
            """, (user_id,))
            gastos = cur.fetchall()

            cur.execute("""
                SELECT fecha, monto, quincena 
                FROM ingresos 
                WHERE user_id=%s 
                ORDER BY fecha DESC
            """, (user_id,))
            ingresos = cur.fetchall()

        total_ingresos = sum(i[1] for i in ingresos) if ingresos else 0
        total_gastos = sum(g[2] for g in gastos) if gastos else 0
        saldo = total_ingresos - total_gastos

        # 🚨 ALERTA
        alerta = total_gastos > total_ingresos * 0.8 if total_ingresos else False

        # 💳 DEUDA
        cur.execute("SELECT total FROM deudas WHERE user_id=%s", (user_id,))
        deuda = cur.fetchone()

        cur.execute("""
            SELECT SUM(monto) 
            FROM gastos 
            WHERE user_id=%s AND categoria='Deuda'
        """, (user_id,))
        pagado = cur.fetchone()[0] or 0

        restante = (deuda[0] - pagado) if deuda else 0

    except Exception as e:
        print("ERROR:", e)
        gastos = []
        ingresos = []
        total_ingresos = 0
        total_gastos = 0
        saldo = 0
        alerta = False
        restante = 0

    cur.close()
    conn.close()

    return render_template(
        "index.html",
        gastos=gastos,
        ingresos=ingresos,
        saldo=saldo,
        total_ingresos=total_ingresos,
        total_gastos=total_gastos,
        alerta=alerta,
        restante=restante,
        mes_actual=mes
    )


# ➕ AGREGAR
@app.route("/agregar", methods=["GET", "POST"])
def agregar():
    if request.method == "GET":
        return redirect("/")

    user_id = session.get("user_id")

    tipo = request.form.get("tipo")
    try:
        monto = float(request.form.get("monto", 0))
    except Exception:
        monto = 0

    fecha = request.form.get("fecha")
    if not fecha:
        return redirect("/")

    q = quincena(fecha)

    conn = get_conn()
    cur = conn.cursor()

    if tipo == "ingreso":
        cur.execute("""
            INSERT INTO ingresos (monto, fecha, quincena, user_id)
            VALUES (%s, %s, %s, %s)
        """, (monto, fecha, q, user_id))
    else:
        nombre = request.form.get("nombre", "")
        categoria = request.form.get("categoria", "Otros")

        cur.execute("""
            INSERT INTO gastos (nombre, monto, fecha, quincena, categoria, user_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (nombre, monto, fecha, q, categoria, user_id))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/")


# 💳 GUARDAR DEUDA
@app.route("/guardar_deuda", methods=["POST"])
def guardar_deuda():
    user_id = session.get("user_id")
    total = float(request.form["total"])

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("DELETE FROM deudas WHERE user_id=%s", (user_id,))
    cur.execute("""
        INSERT INTO deudas (user_id, total)
        VALUES (%s, %s)
    """, (user_id, total))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/")


if __name__ == "__main__":
    app.run()