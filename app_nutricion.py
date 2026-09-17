from flask import Flask, render_template, request, jsonify
import requests
import gspread
import os
from datetime import datetime

app = Flask(__name__)

# Configuración de usuarios y métricas METs
USUARIOS = {
    "Pancho": {"peso_base": 90, "altura_cm": 185, "edad": 20, "sexo": "M"},
    "Angie": {"peso_base": 60, "altura_cm": 165, "edad": 20, "sexo": "F"},
    "Vitto": {"peso_base": 75, "altura_cm": 170, "edad": 20, "sexo": "M"},
    "Fede": {"peso_base": 80, "altura_cm": 175, "edad": 30, "sexo": "M"},
    "Gabi": {"peso_base": 65, "altura_cm": 160, "edad": 30, "sexo": "F"}
}

METS = {
    "Basquet": 8.0,
    "Gym": 4.0,
    "Correr": 9.0,
    "Caminata": 3.0,
    "Descanso": 1.2
}

DIAS_ESPANOL = {
    "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
    "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"
}

MESES_ESPANOL = {
    "January": "Enero", "February": "Febrero", "March": "Marzo", "April": "Abril",
    "May": "Mayo", "June": "Junio", "July": "Julio", "August": "Agosto",
    "September": "Septiembre", "October": "Octubre", "November": "Noviembre", "December": "Diciembre"
}

# Tabla de composición de Alimentos Argentina (Valores reales por 100g / 100ml cocidos)
TABLA_ARGENTINA = {
    # Carnes y Proteínas
    "huevo": {"calorias": 155, "proteinas": 12.6, "carbohidratos": 1.1, "grasas": 10.6},
    "huevos": {"calorias": 155, "proteinas": 12.6, "carbohidratos": 1.1, "grasas": 10.6},
    "huevo duro": {"calorias": 155, "proteinas": 12.6, "carbohidratos": 1.1, "grasas": 10.6},
    "pechuga de pollo": {"calorias": 165, "proteinas": 31.0, "carbohidratos": 0.0, "grasas": 3.6},
    "pollo": {"calorias": 165, "proteinas": 31.0, "carbohidratos": 0.0, "grasas": 3.6},
    "carne de cerdo": {"calorias": 242, "proteinas": 27.0, "carbohidratos": 0.0, "grasas": 14.0},
    "carne vacuna": {"calorias": 250, "proteinas": 26.0, "carbohidratos": 0.0, "grasas": 15.0},
    "asado": {"calorias": 290, "proteinas": 24.0, "carbohidratos": 0.0, "grasas": 21.0},
    "carne picada": {"calorias": 220, "proteinas": 26.0, "carbohidratos": 0.0, "grasas": 12.0},
    
    # Milanesas (Promedio fritas/horno)
    "milanesa": {"calorias": 260, "proteinas": 19.0, "carbohidratos": 15.0, "grasas": 13.0},
    "milanesa de carne": {"calorias": 260, "proteinas": 19.0, "carbohidratos": 15.0, "grasas": 13.0},
    "milanesa de pollo": {"calorias": 250, "proteinas": 18.0, "carbohidratos": 15.0, "grasas": 12.0},
    "milanesa de cerdo": {"calorias": 270, "proteinas": 17.0, "carbohidratos": 15.0, "grasas": 15.0},
    "milanesa de soja": {"calorias": 220, "proteinas": 14.0, "carbohidratos": 18.0, "grasas": 10.0},
    
    # Carbohidratos y Guarniciones
    "arroz": {"calorias": 130, "proteinas": 2.7, "carbohidratos": 28.0, "grasas": 0.3},
    "fideos": {"calorias": 131, "proteinas": 5.0, "carbohidratos": 25.0, "grasas": 1.1},
    "pure": {"calorias": 88, "proteinas": 1.5, "carbohidratos": 15.0, "grasas": 3.0},
    "puré": {"calorias": 88, "proteinas": 1.5, "carbohidratos": 15.0, "grasas": 3.0},
    "pure de papa": {"calorias": 88, "proteinas": 1.5, "carbohidratos": 15.0, "grasas": 3.0},
    "pure de calabaza": {"calorias": 45, "proteinas": 1.0, "carbohidratos": 10.0, "grasas": 0.5},
    "calabaza": {"calorias": 40, "proteinas": 1.0, "carbohidratos": 9.0, "grasas": 0.2},
    "pastel de papa": {"calorias": 140, "proteinas": 6.0, "carbohidratos": 12.0, "grasas": 7.0},
    "tostadas de arroz": {"calorias": 380, "proteinas": 8.0, "carbohidratos": 82.0, "grasas": 2.0},
    "pan": {"calorias": 265, "proteinas": 9.0, "carbohidratos": 49.0, "grasas": 3.2},
    "empanada de carne": {"calorias": 260, "proteinas": 10.0, "carbohidratos": 25.0, "grasas": 13.0},
    "tarta de jamon y queso": {"calorias": 280, "proteinas": 12.0, "carbohidratos": 22.0, "grasas": 15.0},
    
    # Verduras y Frutas
    "tomate": {"calorias": 18, "proteinas": 0.9, "carbohidratos": 3.9, "grasas": 0.2},
    "zanahoria": {"calorias": 41, "proteinas": 0.9, "carbohidratos": 10.0, "grasas": 0.2},
    "acelga cocida": {"calorias": 20, "proteinas": 1.9, "carbohidratos": 4.1, "grasas": 0.1},
    "lechuga": {"calorias": 15, "proteinas": 1.4, "carbohidratos": 2.9, "grasas": 0.2},
    "cebolla": {"calorias": 40, "proteinas": 1.1, "carbohidratos": 9.0, "grasas": 0.1},
    "banana": {"calorias": 89, "proteinas": 1.1, "carbohidratos": 22.8, "grasas": 0.3},
    "manzana": {"calorias": 52, "proteinas": 0.3, "carbohidratos": 13.8, "grasas": 0.2},
    
    # Comida Rápida y Fiambres
    "salchicha": {"calorias": 250, "proteinas": 11.0, "carbohidratos": 3.0, "grasas": 21.0},
    "pancho": {"calorias": 270, "proteinas": 10.0, "carbohidratos": 25.0, "grasas": 14.0},
    "panchos": {"calorias": 270, "proteinas": 10.0, "carbohidratos": 25.0, "grasas": 14.0},
    
    # Grasas, Aceites y Lácteos
    "mantequilla de mani": {"calorias": 588, "proteinas": 25.0, "carbohidratos": 20.0, "grasas": 50.0},
    "aceite de oliva": {"calorias": 884, "proteinas": 0.0, "carbohidratos": 0.0, "grasas": 100.0},
    "aceite": {"calorias": 884, "proteinas": 0.0, "carbohidratos": 0.0, "grasas": 100.0},
    "queso cremoso": {"calorias": 290, "proteinas": 19.0, "carbohidratos": 1.5, "grasas": 23.0},
    "queso cheddar": {"calorias": 402, "proteinas": 25.0, "carbohidratos": 1.3, "grasas": 33.0},
    "chedar": {"calorias": 402, "proteinas": 25.0, "carbohidratos": 1.3, "grasas": 33.0},
    "roquefort": {"calorias": 369, "proteinas": 21.0, "carbohidratos": 2.0, "grasas": 30.0},
    "leche": {"calorias": 60, "proteinas": 3.2, "carbohidratos": 4.7, "grasas": 3.2},
    "yogur": {"calorias": 63, "proteinas": 3.7, "carbohidratos": 7.0, "grasas": 2.0},
    "mayonesa": {"calorias": 680, "proteinas": 1.0, "carbohidratos": 1.0, "grasas": 75.0},
    
    # Bebidas (con y sin alcohol) y Condimentos líquidos
    "vinagre de manzana": {"calorias": 21, "proteinas": 0.0, "carbohidratos": 0.9, "grasas": 0.0},
    "vinagre de alcohol": {"calorias": 21, "proteinas": 0.0, "carbohidratos": 0.9, "grasas": 0.0},
    "cerveza": {"calorias": 43, "proteinas": 0.5, "carbohidratos": 3.6, "grasas": 0.0},
    "fernet": {"calorias": 275, "proteinas": 0.0, "carbohidratos": 11.0, "grasas": 0.0},
    "fernet con coca": {"calorias": 150, "proteinas": 0.0, "carbohidratos": 15.0, "grasas": 0.0},
    "vino": {"calorias": 85, "proteinas": 0.1, "carbohidratos": 2.6, "grasas": 0.0},
    "gin": {"calorias": 263, "proteinas": 0.0, "carbohidratos": 0.0, "grasas": 0.0},
    "coca cola": {"calorias": 42, "proteinas": 0.0, "carbohidratos": 10.6, "grasas": 0.0},
    "sprite": {"calorias": 39, "proteinas": 0.0, "carbohidratos": 9.5, "grasas": 0.0},
    "fanta": {"calorias": 45, "proteinas": 0.0, "carbohidratos": 12.0, "grasas": 0.0},
    "coca cola zero": {"calorias": 0, "proteinas": 0.0, "carbohidratos": 0.0, "grasas": 0.0},
    "terma": {"calorias": 30, "proteinas": 0.0, "carbohidratos": 7.0, "grasas": 0.0},
    "soda": {"calorias": 0, "proteinas": 0.0, "carbohidratos": 0.0, "grasas": 0.0},
    "agua": {"calorias": 0, "proteinas": 0.0, "carbohidratos": 0.0, "grasas": 0.0},
    "mate": {"calorias": 2, "proteinas": 0.0, "carbohidratos": 0.4, "grasas": 0.0},
    "mate canarias": {"calorias": 2, "proteinas": 0.0, "carbohidratos": 0.4, "grasas": 0.0},
    "mate baldo": {"calorias": 2, "proteinas": 0.0, "carbohidratos": 0.4, "grasas": 0.0},
    "mate rei verde": {"calorias": 2, "proteinas": 0.0, "carbohidratos": 0.4, "grasas": 0.0},
    "cafe con leche": {"calorias": 40, "proteinas": 2.0, "carbohidratos": 4.0, "grasas": 1.8},
    
    # Dulces
    "nesquik": {"calorias": 379, "proteinas": 4.5, "carbohidratos": 81.0, "grasas": 2.8},
    "chocotorta": {"calorias": 390, "proteinas": 6.0, "carbohidratos": 48.0, "grasas": 20.0},
    "tiramisu": {"calorias": 280, "proteinas": 4.5, "carbohidratos": 32.0, "grasas": 15.0},
    "dulce de leche": {"calorias": 315, "proteinas": 6.0, "carbohidratos": 55.0, "grasas": 7.5}
}

def calcular_gasto_total(usuario, actividades):
    datos = USUARIOS[usuario]
    if datos["sexo"] == "M":
        tmb = (10 * datos["peso_base"]) + (6.25 * datos["altura_cm"]) - (5 * datos["edad"]) + 5
    else:
        tmb = (10 * datos["peso_base"]) + (6.25 * datos["altura_cm"]) - (5 * datos["edad"]) - 161
    
    gasto_base = tmb * 1.2
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
    alimento_espanol = datos.get('alimento', '').strip().lower()
    gramos = float(datos.get('gramos', 100))
    factor = gramos / 100.0

    if alimento_espanol in TABLA_ARGENTINA:
        item = TABLA_ARGENTINA[alimento_espanol]
        return jsonify({
            "encontrado": True,
            "nombre_original": alimento_espanol.capitalize(),
            "calorias": round(item["calorias"] * factor, 1),
            "proteinas": round(item["proteinas"] * factor, 1),
            "carbohidratos": round(item["carbohidratos"] * factor, 1),
            "grasas": round(item["grasas"] * factor, 1)
        })

    try:
        url = f"https://es.openfoodfacts.org/cgi/search.pl?search_terms={alimento_espanol}&search_simple=1&action=process&json=1&page_size=1"
        headers = {'User-Agent': 'NutriAppArgentina - Web - Version 1.0'}
        resp = requests.get(url, headers=headers, timeout=4)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get('products') and len(data['products']) > 0:
                prod = data['products'][0]
                nutr = prod.get('nutriments', {})
                
                cal_100 = nutr.get('energy-kcal_100g') or nutr.get('energy-kcal') or 0
                prot_100 = nutr.get('proteins_100g') or nutr.get('proteins') or 0
                carb_100 = nutr.get('carbohydrates_100g') or nutr.get('carbohydrates') or 0
                gras_100 = nutr.get('fat_100g') or nutr.get('fat') or 0

                if cal_100 > 0:
                    return jsonify({
                        "encontrado": True,
                        "nombre_original": prod.get('product_name', alimento_espanol).capitalize(),
                        "calorias": round(float(cal_100) * factor, 1),
                        "proteinas": round(float(prot_100) * factor, 1),
                        "carbohidratos": round(float(carb_100) * factor, 1),
                        "grasas": round(float(gras_100) * factor, 1)
                    })
    except Exception as e:
        pass

    return jsonify({
        "encontrado": False,
        "error": "Alimento no encontrado en la base de datos. Podés ingresarlo manualmente."
    }), 404

@app.route('/cerrar_dia', methods=['POST'])
def cerrar_dia():
    datos = request.json
    usuario = datos["usuario"]
    fecha_seleccionada = datos.get("fecha") or datetime.now().strftime("%Y-%m-%d")
    
    dt_obj = datetime.strptime(fecha_seleccionada, "%Y-%m-%d")
    dia_ingles = dt_obj.strftime("%A")
    mes_ingles = dt_obj.strftime("%B")
    
    dia_semana = DIAS_ESPANOL.get(dia_ingles, dia_ingles)
    mes_actual = MESES_ESPANOL.get(mes_ingles, mes_ingles)
    
    t_cal = sum(float(c["calorias"]) for c in datos["comidas"])
    t_prot = sum(float(c["proteinas"]) for c in datos["comidas"])
    t_carb = sum(float(c["carbohidratos"]) for c in datos["comidas"])
    t_gras = sum(float(c["grasas"]) for c in datos["comidas"])
    
    tdee = calcular_gasto_total(usuario, datos["actividades"])

    detalle_comidas = " | ".join([f"[{c['horario']}] {c['nombre_original']} ({c['calorias']}kcal)" for c in datos["comidas"]])
    bano_texto = f"Orina (#1): {datos['bano_1']} | Sólido (#2): {datos['bano_2']}"
    act_texto = ", ".join([f"{a['nombre']} ({a['horas']}h)" for a in datos["actividades"]])
    notas = datos.get("notas", "")

    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        ruta_credenciales = os.path.join(base_dir, "credenciales.json")
        
        gc = gspread.service_account(filename=ruta_credenciales)
        hoja_datos = gc.open("Mi_Nutricion_2026") 
        
        nombre_pestana = f"{usuario}_{mes_actual}"
        
        try:
            worksheet = hoja_datos.worksheet(nombre_pestana)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = hoja_datos.add_worksheet(title=nombre_pestana, rows="100", cols="16")
            
            # Fila 1: Encabezados
            worksheet.append_row([
                "Fecha", "Día", "Peso (kg)", "Sueño (hs)", "Líquidos (L)", "Digestión", 
                "Detalle Comidas", "Calorías Consumidas", "Proteínas (g)", "Carbos (g)", 
                "Grasas (g)", "Actividades", "Gasto (TDEE)", "Balance", "Notas"
            ])
            
            # Fila 2: Meta de Recomposición Corporal
            worksheet.append_row([
                "OBJETIVO", "Diario", "89-90", "8", "3.0", "-", 
                "Meta para perder grasa y mantener músculo ->", "2200", "180", "200", 
                "75", "Básquet / Gym", "2700", "-500", "Priorizar proteína"
            ])
            
        num_fila = len(worksheet.get_all_values()) + 1
        formula_balance = f"=H{num_fila}-M{num_fila}"

        fila = [
            fecha_seleccionada, dia_semana, datos["peso"], datos["sueno"], datos["liquidos"], 
            bano_texto, detalle_comidas, round(t_cal), round(t_prot), round(t_carb), 
            round(t_gras), act_texto, tdee, formula_balance, notas
        ]
        
        worksheet.append_row(fila, value_input_option="USER_ENTERED")
        
        return jsonify({"mensaje": "¡Día cerrado y guardado exitosamente en Google Sheets!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
