
from flask import Flask, render_template, request, redirect, jsonify, send_file
import json, os
from datetime import datetime
from functools import wraps

app = Flask(__name__)

ARCHIVO_COMPRAS = "compras.json"
ARCHIVO_HISTORIAL = "historial.json"
ARCHIVO_MOTOS_ROBADAS = "motos_robadas.json"
ARCHIVO_CONFIG = "config.json"

def cargar_o_crear(ruta, valor_defecto):
    if os.path.exists(ruta):
        with open(ruta, "r") as f:
            return json.load(f)
    with open(ruta, "w") as f:
        json.dump(valor_defecto, f)
    return valor_defecto

compras = cargar_o_crear(ARCHIVO_COMPRAS, [])
historial = cargar_o_crear(ARCHIVO_HISTORIAL, [])
motos_robadas = cargar_o_crear(ARCHIVO_MOTOS_ROBADAS, [])
config = cargar_o_crear(ARCHIVO_CONFIG, {
    "litros_moto": 5,
    "litros_auto": 10,
    "admin_password": "1234"
})

def guardar_json(ruta, data):
    with open(ruta, "w") as f:
        json.dump(data, f, indent=2)

@app.route("/")
def index():
    contador_motos = sum(1 for c in compras if c["tipo"] == "Motocicleta")
    contador_autos = sum(1 for c in compras if c["tipo"] == "Automóvil")
    total_motos = contador_motos * config["litros_moto"]
    total_autos = contador_autos * config["litros_auto"]
    return render_template("index.html", contador_motos=contador_motos, contador_autos=contador_autos,
                           total_motos=total_motos, total_autos=total_autos)

@app.route("/buscar", methods=["POST"])
def buscar():
    carnet = request.form.get("carnet")
    cliente = next((c for c in historial if c["carnet"] == carnet), None)
    return jsonify(cliente if cliente else {})

@app.route("/registrar", methods=["POST"])
def registrar():
    carnet = request.form.get("carnet")
    nombre = request.form.get("nombre")
    chasis = request.form.get("chasis")
    tipo = request.form.get("tipo")
    if not carnet or not nombre or not chasis:
        return "Faltan datos", 400
    for c in compras:
        if carnet == c["carnet"] and tipo == c["tipo"]:
            return "Ya compró combustible para este tipo de vehículo", 403
        if nombre == c["nombre"] or chasis == c["chasis"]:
            return "Datos ya registrados para otro vehículo", 403
    if any(chasis.endswith(r[-3:]) for r in motos_robadas):
        return "Moto con denuncia de robo. Verificar documentos", 403
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    registro = {"carnet": carnet, "nombre": nombre, "chasis": chasis, "tipo": tipo, "fecha": fecha}
    compras.append(registro)
    historial.append(registro)
    guardar_json(ARCHIVO_COMPRAS, compras)
    guardar_json(ARCHIVO_HISTORIAL, historial)
    return "Registrado", 200

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        clave = request.form.get("clave")
        if clave == config["admin_password"]:
            return render_template("admin.html", config=config, motos=motos_robadas)
        return "Contraseña incorrecta", 403
    return render_template("login.html")

@app.route("/admin/reset", methods=["POST"])
def reset_dia():
    clave = request.form.get("clave")
    if clave != config["admin_password"]:
        return "Contraseña incorrecta", 403
    compras.clear()
    guardar_json(ARCHIVO_COMPRAS, compras)
    return "Compras del día reseteadas", 200

@app.route("/admin/reset_todo", methods=["POST"])
def reset_todo():
    clave = request.form.get("clave")
    if clave != config["admin_password"]:
        return "Contraseña incorrecta", 403
    compras.clear()
    historial.clear()
    guardar_json(ARCHIVO_COMPRAS, compras)
    guardar_json(ARCHIVO_HISTORIAL, historial)
    return "Todo el sistema fue reseteado", 200

@app.route("/admin/guardar_config", methods=["POST"])
def guardar_config():
    clave = request.form.get("clave")
    if clave != config["admin_password"]:
        return "Contraseña incorrecta", 403
    config["litros_moto"] = int(request.form.get("litros_moto"))
    config["litros_auto"] = int(request.form.get("litros_auto"))
    guardar_json(ARCHIVO_CONFIG, config)
    return "Configuración actualizada", 200

@app.route("/admin/guardar_motos", methods=["POST"])
def guardar_motos():
    clave = request.form.get("clave")
    if clave != config["admin_password"]:
        return "Contraseña incorrecta", 403
    datos = request.form.get("lista_motos")
    lista = datos.splitlines()
    motos_robadas.clear()
    motos_robadas.extend(lista)
    guardar_json(ARCHIVO_MOTOS_ROBADAS, motos_robadas)
    return "Lista de motos robadas actualizada", 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
