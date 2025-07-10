from flask import Flask, render_template, request, redirect, jsonify, session, url_for
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "clave_segura_para_admin"

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
config = cargar_o_crear(ARCHIVO_CONFIG, {"litros_moto": 5, "litros_auto": 10})

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
    return jsonify(cliente or {})

@app.route("/registrar", methods=["POST"])
def registrar():
    carnet = request.form.get("carnet")
    nombre = request.form.get("nombre")
    chasis = request.form.get("chasis")
    tipo = request.form.get("tipo")
    if not carnet or not nombre or not chasis:
        return "<h2 style='font-size:1.5em; color:red;'>Faltan datos</h2>", 400
    for c in compras:
        if carnet == c["carnet"] and tipo == c["tipo"]:
            return "<h2 style='font-size:1.5em; color:orange;'>Ya compró combustible para este tipo de vehículo</h2>", 403
        if nombre == c["nombre"] or chasis == c["chasis"]:
            return "<h2 style='font-size:1.5em; color:orange;'>Datos ya registrados para otro vehículo</h2>", 403
    if any(chasis.endswith(r[-3:]) for r in motos_robadas):
        return "<h2 style='font-size:1.5em; color:red;'>Moto con denuncia de robo. Verificar documentos</h2>", 403
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    registro = {"carnet": carnet, "nombre": nombre, "chasis": chasis, "tipo": tipo, "fecha": fecha}
    compras.append(registro)
    historial.append(registro)
    with open(ARCHIVO_COMPRAS, "w") as f:
        json.dump(compras, f)
    with open(ARCHIVO_HISTORIAL, "w") as f:
        json.dump(historial, f)
    return redirect("/")

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        contraseña = request.form.get("password")
        if contraseña == "1234":
            session["admin"] = True
            return redirect(url_for("panel"))
        return render_template("admin_login.html", error="Contraseña incorrecta")
    return render_template("admin_login.html")

@app.route("/panel")
def panel():
    if not session.get("admin"):
        return redirect(url_for("admin"))
    return render_template("admin_panel.html", registros=compras, config=config, motos=motos_robadas)
    contador_motos = sum(1 for c in compras if c["tipo"] == "Motocicleta")
    contador_autos = sum(1 for c in compras if c["tipo"] == "Automóvil")
    total_motos = contador_motos * config["litros_moto"]
    total_autos = contador_autos * config["litros_auto"]
    return render_template("admin_panel.html", registros=compras, config=config,
                           motos=motos_robadas, contador_motos=contador_motos,
                           contador_autos=contador_autos, total_motos=total_motos,
                           total_autos=total_autos)
@app.route("/config", methods=["POST"])
def actualizar_config():
    if not session.get("admin"):
        return redirect(url_for("admin"))
    litros_moto = request.form.get("litros_moto", type=int)
    litros_auto = request.form.get("litros_auto", type=int)
    if litros_moto and litros_auto:
        config["litros_moto"] = litros_moto
        config["litros_auto"] = litros_auto
        with open(ARCHIVO_CONFIG, "w") as f:
            json.dump(config, f)
    return redirect(url_for("panel"))

@app.route("/resetear", methods=["POST"])
def resetear():
    global compras
    compras = []
    with open(ARCHIVO_COMPRAS, "w") as f:
        json.dump(compras, f)
    return ("", 204)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
