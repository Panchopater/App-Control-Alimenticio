from flask import Flask, render_template, request, jsonify
import requests
import gspread
from datetime import datetime
from deep_translator import GoogleTranslator

app = Flask(__name__)

# 1. Usuarios actualizados
USUARIOS = {
    "Pancho": {"peso_base": 90, "altura_cm": 185, "edad": 20, "sexo": "M"},
    "Angie": {"peso_base": 60, "altura_cm": 165, "edad": 20, "sexo": "F"},
    "Vitto": {"peso_base": 75, "altura_cm": 170, "edad": 20, "sexo": "M"} # Ajustá los datos de Vitto si es necesario
}

METS = {"Basquet": 8.0, "Gym": 4.0, "Caminata": 3.0, "Descanso": 1.2}

def calcular_gasto_total(usuario, actividades):
    datos = USUARIOS[usuario]
    if datos["sexo"] == "M":
        tmb = (10 * datos["peso_base"]) + (6.25 * datos["altura_cm"]) - (5 * datos["edad"]) + 5
    else:
        tmb = (10 * datos["peso_base"]) + (6.25 * datos["altura_cm"]) - (5 * datos["edad"]) - 161
    
    gasto_base = tmb * 1.2 # Gasto diario estándar
    
    gasto_extra = 0
    for act in actividades:
        nombre = act["nombre"]
        horas = float(act["horas"])
        if nombre != "Descanso":
            gasto_extra += METS.get(nombre, 0) * datos["peso_base"] * horas
            
    return round(gasto_base + gasto_extra)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/buscar_alimento', methods=['POST'])
def buscar_alimento():
    datos = request.json
    alimento_espanol = datos.get('alimento')
    gramos = float(datos.get('gramos'))
    
    try:
        # Traducción invisible de Español a Inglés para engañar al USDA
        traductor = GoogleTranslator(source='es', target='en')
        alimento_ingles = traductor.translate(alimento_espanol)
    except:
        alimento_ingles = alimento_espanol # Failsafe
        
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {"api_key": "DEMO_KEY", "query": alimento_ingles, "pageSize": 1}
    
    resp = requests.get(url, params=params)
    if resp.status_code == 200 and len(resp.json().get("foods", [])) > 0:
        producto = resp.json()["foods"][0]
        factor = gramos / 100.0
        
        calorias = proteinas = grasas = carbohidratos = 0
        for nut in producto.get("foodNutrients", []):
            if nut["nutrientId"] == 1008: calorias = nut["value"] * factor
            elif nut["nutrientId"] == 1003: proteinas = nut["value"] * factor
            elif nut["nutrientId"] == 1004: grasas = nut["value"] * factor
            elif nut["nutrientId"] == 1005: carbohidratos = nut["value"] * factor
            
        return jsonify({
            "nombre_original": alimento_espanol,
            "calorias": round(calorias, 1),
            "proteinas": round(proteinas, 1),
            "carbohidratos": round(carbohidratos, 1),
            "grasas": round(grasas, 1)
        })
    return jsonify({"error": "No se encontró el alimento en la base de datos."}), 404

@app.route('/cerrar_dia', methods=['POST'])
def cerrar_dia():
    datos = request.json
    usuario = datos["usuario"]
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    dia_semana = datetime.now().strftime("%A")
    
    t_cal = sum(float(c["calorias"]) for c in datos["comidas"])
    t_prot = sum(float(c["proteinas"]) for c in datos["comidas"])
    t_carb = sum(float(c["carbohidratos"]) for c in datos["comidas"])
    t_gras = sum(float(c["grasas"]) for c in datos["comidas"])
    
    tdee = calcular_gasto_total(usuario, datos["actividades"])
    balance = t_cal - tdee

    # Formatear el baño para el Excel
    bano_texto = f"N1: {datos['bano_1']} | N2: {datos['bano_2']}"
    # Formatear actividades para el Excel
    act_texto = ", ".join([f"{a['nombre']} ({a['horas']}h)" for a in datos["actividades"]])

    try:
        gc = gspread.service_account(filename="credenciales.json")
        hoja_datos = gc.open("Mi_Nutricion_2026") 
        
        mes_actual = datetime.now().strftime("%B")
        nombre_pestana = f"{usuario}_{mes_actual}"
        
        try:
            worksheet = hoja_datos.worksheet(nombre_pestana)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = hoja_datos.add_worksheet(title=nombre_pestana, rows="100", cols="15")
            worksheet.append_row(["Fecha", "Día", "Peso (kg)", "Sueño (hs)", "Líquidos (L)", "Digestión", "Actividades", "Calorías", "Proteínas", "Carbos", "Grasas", "Gasto (TDEE)", "Balance", "Notas"])
            
        fila = [fecha_hoy, dia_semana, datos["peso"], datos["sueno"], datos["liquidos"], bano_texto, act_texto, round(t_cal), round(t_prot), round(t_carb), round(t_gras), tdee, round(balance), ""]
        worksheet.append_row(fila)
        
        return jsonify({"mensaje": "¡Día cerrado y guardado en Google Sheets con éxito!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
    