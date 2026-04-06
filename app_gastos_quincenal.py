import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta
import json
import os

ARCHIVO = "datos.json"

# ------------------ DATA ------------------
def cargar_datos():
    if os.path.exists(ARCHIVO):
        with open(ARCHIVO, "r") as f:
            return json.load(f)
    return {"ingresos": [], "gastos": []}

def guardar_datos():
    with open(ARCHIVO, "w") as f:
        json.dump(data, f, indent=4)

data = cargar_datos()

# ------------------ LOGICA ------------------
def obtener_quincena(fecha):
    dia = int(fecha.split("-")[2])
    return "Q1" if dia <= 15 else "Q2"

def agregar_ingreso():
    try:
        monto = float(entry_ingreso.get())
        fecha = entry_fecha_ingreso.get()

        data["ingresos"].append({
            "monto": monto,
            "fecha": fecha,
            "quincena": obtener_quincena(fecha)
        })

        guardar_datos()
        messagebox.showinfo("OK", "Ingreso guardado")
        entry_ingreso.delete(0, tk.END)
    except:
        messagebox.showerror("Error", "Datos inválidos")

def agregar_gasto():
    try:
        nombre = entry_nombre.get()
        monto = float(entry_monto.get())
        fecha = entry_fecha.get()

        data["gastos"].append({
            "nombre": nombre,
            "monto": monto,
            "fecha": fecha,
            "quincena": obtener_quincena(fecha)
        })

        guardar_datos()
        messagebox.showinfo("OK", "Gasto guardado")
        entry_nombre.delete(0, tk.END)
        entry_monto.delete(0, tk.END)
    except:
        messagebox.showerror("Error", "Datos inválidos")

def ver_resumen():
    q1_i = sum(i["monto"] for i in data["ingresos"] if i["quincena"]=="Q1")
    q2_i = sum(i["monto"] for i in data["ingresos"] if i["quincena"]=="Q2")
    q1_g = sum(g["monto"] for g in data["gastos"] if g["quincena"]=="Q1")
    q2_g = sum(g["monto"] for g in data["gastos"] if g["quincena"]=="Q2")

    texto = f"""
🔹 Q1
Ingresos: {q1_i}
Gastos: {q1_g}
Disponible: {q1_i - q1_g}

🔹 Q2
Ingresos: {q2_i}
Gastos: {q2_g}
Disponible: {q2_i - q2_g}
"""
    messagebox.showinfo("Resumen", texto)

def ver_gastos():
    ventana = tk.Toplevel(root)
    ventana.title("Gastos")

    lista = tk.Listbox(ventana, width=60)
    lista.pack()

    for g in data["gastos"]:
        lista.insert(tk.END, f"{g['fecha']} | {g['nombre']} | ${g['monto']} | {g['quincena']}")

def alertas():
    hoy = datetime.today()
    mensajes = []

    for g in data["gastos"]:
        fecha = datetime.strptime(g["fecha"], "%Y-%m-%d")
        dias = (fecha - hoy).days

        if 0 <= dias <= 3:
            mensajes.append(f"{g['nombre']} vence en {dias} días")

    if mensajes:
        messagebox.showwarning("⚠️ Alertas", "\n".join(mensajes))

# ------------------ UI ------------------
root = tk.Tk()
root.title("💰 Control Financiero Pro")
root.geometry("350x400")
root.config(bg="#1e1e2f")

def label(text, row):
    tk.Label(root, text=text, bg="#1e1e2f", fg="white").grid(row=row, column=0)

def entry(row):
    e = tk.Entry(root)
    e.grid(row=row, column=1)
    return e

# INGRESOS
label("Ingreso", 0)
entry_ingreso = entry(0)

label("Fecha", 1)
entry_fecha_ingreso = entry(1)

tk.Button(root, text="Agregar Ingreso", command=agregar_ingreso, bg="#4CAF50").grid(row=2, column=0, columnspan=2)

# GASTOS
label("Nombre", 3)
entry_nombre = entry(3)

label("Monto", 4)
entry_monto = entry(4)

label("Fecha", 5)
entry_fecha = entry(5)

tk.Button(root, text="Agregar Gasto", command=agregar_gasto, bg="#f44336").grid(row=6, column=0, columnspan=2)

# BOTONES
tk.Button(root, text="Resumen", command=ver_resumen).grid(row=7, column=0)
tk.Button(root, text="Ver Gastos", command=ver_gastos).grid(row=7, column=1)

alertas()

root.mainloop()