from flask import Flask, render_template, request, jsonify
import requests
import gspread
import os
from datetime import datetime

app = Flask(__name__)

# Configuración de usuarios y métricas METs
USUARIOS = {
    "Pancho": {"peso_base": 90, "altura_cm": 185, "edad": 20, "sexo": "M"},
    "Angie": {"peso_base": 60, "altura_cm": 165, "edad": 18, "sexo": "F"},
    "Vitto": {"peso_base": 85, "altura_cm": 170, "edad": 22, "sexo": "M"},
    "Fede": {"peso_base": 100, "altura_cm": 180, "edad": 52, "sexo": "M"},
    "Gabi": {"peso_base": 70, "altura_cm": 165, "edad": 53, "sexo": "F"}
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
    # Huevos y Pollo
    "huevo": {"calorias": 155, "proteinas": 12.6, "carbohidratos": 1.1, "grasas": 10.6},
    "huevos": {"calorias": 155, "proteinas": 12.6, "carbohidratos": 1.1, "grasas": 10.6},
    "huevo duro": {"calorias": 155, "proteinas": 12.6, "carbohidratos": 1.1, "grasas": 10.6},
    "pechuga de pollo": {"calorias": 165, "proteinas": 31.0, "carbohidratos": 0.0, "grasas": 3.6},
    "pollo": {"calorias": 165, "proteinas": 31.0, "carbohidratos": 0.0, "grasas": 3.6},
    "facturas": {"calorias": 380, "proteinas": 6.0, "carbohidratos": 45.0, "grasas": 18.0},
    "factura": {"calorias": 380, "proteinas": 6.0, "carbohidratos": 45.0, "grasas": 18.0},
    "tarta de verdura y pollo": {"calorias": 180, "proteinas": 10.0, "carbohidratos": 15.0, "grasas": 9.0},
    "pera": {"calorias": 57, "proteinas": 0.4, "carbohidratos": 15.2, "grasas": 0.1},
    "mandarina": {"calorias": 53, "proteinas": 0.8, "carbohidratos": 13.3, "grasas": 0.3},
    "manzana verde": {"calorias": 52, "proteinas": 0.3, "carbohidratos": 14.0, "grasas": 0.2},
    "capuccino": {"calorias": 45, "proteinas": 3.0, "carbohidratos": 5.0, "grasas": 1.5},
    "cappuccino": {"calorias": 45, "proteinas": 3.0, "carbohidratos": 5.0, "grasas": 1.5},
    # Carnes y Parrilla Argentina
    "carne vacuna": {"calorias": 250, "proteinas": 26.0, "carbohidratos": 0.0, "grasas": 15.0},
    "carne picada": {"calorias": 220, "proteinas": 26.0, "carbohidratos": 0.0, "grasas": 12.0},
    "carne de cerdo": {"calorias": 242, "proteinas": 27.0, "carbohidratos": 0.0, "grasas": 14.0},
    "asado": {"calorias": 290, "proteinas": 24.0, "carbohidratos": 0.0, "grasas": 21.0},
    "tapa de asado": {"calorias": 260, "proteinas": 25.0, "carbohidratos": 0.0, "grasas": 17.0},
    "vacio": {"calorias": 220, "proteinas": 26.0, "carbohidratos": 0.0, "grasas": 13.0},
    "chorizo": {"calorias": 330, "proteinas": 14.0, "carbohidratos": 2.0, "grasas": 30.0},
    "choripan": {"calorias": 450, "proteinas": 18.0, "carbohidratos": 40.0, "grasas": 31.0},
    "morcilla": {"calorias": 300, "proteinas": 12.0, "carbohidratos": 1.0, "grasas": 27.0},
    "chinchulines": {"calorias": 200, "proteinas": 14.0, "carbohidratos": 0.0, "grasas": 16.0},
    # Facturas y Panadería Argentina
    "chipa": {"calorias": 330, "proteinas": 10.0, "carbohidratos": 40.0, "grasas": 15.0},
    "media luna": {"calorias": 400, "proteinas": 7.0, "carbohidratos": 45.0, "grasas": 21.0},
    "medialuna": {"calorias": 400, "proteinas": 7.0, "carbohidratos": 45.0, "grasas": 21.0},
    "medialuna de grasa": {"calorias": 420, "proteinas": 8.0, "carbohidratos": 45.0, "grasas": 23.0},
    "torta negra": {"calorias": 380, "proteinas": 6.0, "carbohidratos": 60.0, "grasas": 13.0},
    "vigilante": {"calorias": 350, "proteinas": 6.0, "carbohidratos": 48.0, "grasas": 15.0},
    "bola de fraile": {"calorias": 410, "proteinas": 6.0, "carbohidratos": 50.0, "grasas": 20.0},
    "cañoncito de dulce de leche": {"calorias": 430, "proteinas": 5.0, "carbohidratos": 55.0, "grasas": 21.0},

    # Picada, Fiambres y Agregados
    "cebolla": {"calorias": 40, "proteinas": 1.1, "carbohidratos": 9.0, "grasas": 0.1},
    "cebolla salteada": {"calorias": 85, "proteinas": 1.5, "carbohidratos": 10.0, "grasas": 5.0},
    "panceta": {"calorias": 450, "proteinas": 14.0, "carbohidratos": 1.0, "grasas": 43.0},
    "salamin": {"calorias": 400, "proteinas": 22.0, "carbohidratos": 1.5, "grasas": 35.0},
    "salame": {"calorias": 400, "proteinas": 22.0, "carbohidratos": 1.5, "grasas": 35.0},
    "jamon cocido": {"calorias": 110, "proteinas": 18.0, "carbohidratos": 1.5, "grasas": 3.5},
    "jamon crudo": {"calorias": 240, "proteinas": 26.0, "carbohidratos": 0.0, "grasas": 15.0},
    "mortadela": {"calorias": 310, "proteinas": 16.0, "carbohidratos": 3.0, "grasas": 25.0},

# === EMPANADAS ===
    "empanada de carne dulce": {"calorias": 265, "proteinas": 10.0, "carbohidratos": 28.0, "grasas": 12.0},
    "empanada de carne picante": {"calorias": 260, "proteinas": 10.0, "carbohidratos": 25.0, "grasas": 13.0},
    "empanada de pollo": {"calorias": 240, "proteinas": 12.0, "carbohidratos": 25.0, "grasas": 10.0},
    "empanada de jamon y queso": {"calorias": 250, "proteinas": 11.0, "carbohidratos": 24.0, "grasas": 12.0},
    "empanada de humita": {"calorias": 230, "proteinas": 6.0, "carbohidratos": 30.0, "grasas": 9.0},
    "empanada de choclo": {"calorias": 230, "proteinas": 6.0, "carbohidratos": 30.0, "grasas": 9.0},
    "empanada de verdura": {"calorias": 210, "proteinas": 6.0, "carbohidratos": 26.0, "grasas": 9.0},
    "empanada de cebolla y queso": {"calorias": 245, "proteinas": 9.0, "carbohidratos": 25.0, "grasas": 12.0},
    "empanada de roquefort": {"calorias": 270, "proteinas": 10.0, "carbohidratos": 24.0, "grasas": 15.0},
    "empanada caprese": {"calorias": 220, "proteinas": 9.0, "carbohidratos": 25.0, "grasas": 10.0},
    "empanada de matambre": {"calorias": 270, "proteinas": 11.0, "carbohidratos": 24.0, "grasas": 14.0},
    "empanada de atun": {"calorias": 240, "proteinas": 11.0, "carbohidratos": 26.0, "grasas": 10.0},
    "sfija": {"calorias": 220, "proteinas": 10.0, "carbohidratos": 28.0, "grasas": 8.0},
    "empanada arabe": {"calorias": 220, "proteinas": 10.0, "carbohidratos": 28.0, "grasas": 8.0},

    # === PIZZAS ===
    "pizza de muzzarella": {"calorias": 260, "proteinas": 11.0, "carbohidratos": 33.0, "grasas": 10.0},
    "pizza fugazzetta": {"calorias": 275, "proteinas": 12.0, "carbohidratos": 32.0, "grasas": 11.0},
    "pizza napolitana": {"calorias": 245, "proteinas": 10.0, "carbohidratos": 32.0, "grasas": 9.0},
    "pizza de jamon y morron": {"calorias": 255, "proteinas": 12.0, "carbohidratos": 32.0, "grasas": 9.5},
    "pizza calabresa": {"calorias": 290, "proteinas": 13.0, "carbohidratos": 32.0, "grasas": 13.0},
    "pizza de provolone": {"calorias": 285, "proteinas": 13.0, "carbohidratos": 31.0, "grasas": 12.0},
    "pizza rucula y crudo": {"calorias": 250, "proteinas": 12.0, "carbohidratos": 31.0, "grasas": 9.0},
    "pizza cuatro quesos": {"calorias": 295, "proteinas": 14.0, "carbohidratos": 31.0, "grasas": 13.0},
    "pizza de anchoas": {"calorias": 240, "proteinas": 11.0, "carbohidratos": 33.0, "grasas": 7.0},
    "pizza de palmitos": {"calorias": 255, "proteinas": 11.0, "carbohidratos": 34.0, "grasas": 9.0},

    # === TARTAS ===
    "tarta de zapallito": {"calorias": 140, "proteinas": 5.0, "carbohidratos": 16.0, "grasas": 7.0},
    "tarta de choclo": {"calorias": 180, "proteinas": 6.0, "carbohidratos": 22.0, "grasas": 8.0},
    "tarta de atun": {"calorias": 200, "proteinas": 10.0, "carbohidratos": 20.0, "grasas": 9.0},
    "tarta de calabaza": {"calorias": 160, "proteinas": 5.0, "carbohidratos": 19.0, "grasas": 7.0},
    "tarta de puerro": {"calorias": 170, "proteinas": 6.0, "carbohidratos": 17.0, "grasas": 9.0},
    "tarta de acelga": {"calorias": 150, "proteinas": 5.0, "carbohidratos": 18.0, "grasas": 7.0},
    "tarta de espinaca": {"calorias": 150, "proteinas": 6.0, "carbohidratos": 17.0, "grasas": 7.0},
    "tarta de jamon y queso": {"calorias": 280, "proteinas": 12.0, "carbohidratos": 22.0, "grasas": 15.0},
    "tarta de brocoli": {"calorias": 145, "proteinas": 6.0, "carbohidratos": 16.0, "grasas": 7.0},
    "tarta de pollo": {"calorias": 210, "proteinas": 12.0, "carbohidratos": 20.0, "grasas": 9.0},

    # === RAVIOLES ===
    "ravioles de verdura y pollo": {"calorias": 190, "proteinas": 9.0, "carbohidratos": 28.0, "grasas": 5.0},
    "ravioles de ricota": {"calorias": 210, "proteinas": 8.0, "carbohidratos": 30.0, "grasas": 6.0},
    "ravioles de carne": {"calorias": 220, "proteinas": 10.0, "carbohidratos": 28.0, "grasas": 7.0},
    "ravioles de jamon y queso": {"calorias": 230, "proteinas": 10.0, "carbohidratos": 28.0, "grasas": 8.0},
    "ravioles de espinaca": {"calorias": 185, "proteinas": 7.0, "carbohidratos": 29.0, "grasas": 4.0},
    "ravioles de calabaza": {"calorias": 180, "proteinas": 6.0, "carbohidratos": 32.0, "grasas": 3.5},
    "ravioles cuatro quesos": {"calorias": 250, "proteinas": 11.0, "carbohidratos": 28.0, "grasas": 10.0},
    "ravioles de salmon": {"calorias": 230, "proteinas": 11.0, "carbohidratos": 28.0, "grasas": 8.0},
    "ravioles de seso": {"calorias": 215, "proteinas": 9.0, "carbohidratos": 27.0, "grasas": 8.0},
    "ravioles de champignones": {"calorias": 195, "proteinas": 7.0, "carbohidratos": 29.0, "grasas": 5.0},

    # === SORRENTINOS ===
    "sorrentinos de jamon y queso": {"calorias": 260, "proteinas": 12.0, "carbohidratos": 30.0, "grasas": 10.0},
    "sorrentinos de ricota y nuez": {"calorias": 275, "proteinas": 9.0, "carbohidratos": 30.0, "grasas": 13.0},
    "sorrentinos de calabaza y queso": {"calorias": 230, "proteinas": 8.0, "carbohidratos": 33.0, "grasas": 7.0},
    "sorrentinos caprese": {"calorias": 240, "proteinas": 10.0, "carbohidratos": 31.0, "grasas": 8.0},
    "sorrentinos de muzzarella y albahaca": {"calorias": 250, "proteinas": 11.0, "carbohidratos": 30.0, "grasas": 9.0},
    "sorrentinos de bondiola": {"calorias": 280, "proteinas": 13.0, "carbohidratos": 29.0, "grasas": 12.0},
    "sorrentinos de cordero": {"calorias": 285, "proteinas": 13.0, "carbohidratos": 29.0, "grasas": 13.0},
    "sorrentinos de salmon": {"calorias": 265, "proteinas": 12.0, "carbohidratos": 29.0, "grasas": 11.0},
    "sorrentinos de roquefort": {"calorias": 290, "proteinas": 12.0, "carbohidratos": 29.0, "grasas": 14.0},
    "sorrentinos de pollo y verdura": {"calorias": 235, "proteinas": 12.0, "carbohidratos": 30.0, "grasas": 7.0},

    # === CORTES DE CERDO ===
    "bondiola": {"calorias": 250, "proteinas": 17.0, "carbohidratos": 0.0, "grasas": 20.0},
    "pechito de cerdo": {"calorias": 280, "proteinas": 16.0, "carbohidratos": 0.0, "grasas": 24.0},
    "matambrito de cerdo": {"calorias": 260, "proteinas": 17.0, "carbohidratos": 0.0, "grasas": 21.0},
    "solomillo": {"calorias": 140, "proteinas": 21.0, "carbohidratos": 0.0, "grasas": 5.0},
    "carre de cerdo": {"calorias": 160, "proteinas": 22.0, "carbohidratos": 0.0, "grasas": 7.0},
    "costillita de cerdo": {"calorias": 230, "proteinas": 19.0, "carbohidratos": 0.0, "grasas": 17.0},
    "churrasquito de cerdo": {"calorias": 210, "proteinas": 18.0, "carbohidratos": 0.0, "grasas": 15.0},
    "chorizo de cerdo": {"calorias": 330, "proteinas": 14.0, "carbohidratos": 2.0, "grasas": 30.0},
    "patita de cerdo": {"calorias": 200, "proteinas": 16.0, "carbohidratos": 0.0, "grasas": 15.0},
    "cuerito de cerdo": {"calorias": 540, "proteinas": 17.0, "carbohidratos": 0.0, "grasas": 52.0},
    "tocino": {"calorias": 670, "proteinas": 4.0, "carbohidratos": 0.0, "grasas": 72.0},

    # === CORTES DE POLLO ===
    "pechuga": {"calorias": 165, "proteinas": 31.0, "carbohidratos": 0.0, "grasas": 3.6},
    "pata de pollo": {"calorias": 210, "proteinas": 24.0, "carbohidratos": 0.0, "grasas": 12.0},
    "muslo de pollo": {"calorias": 230, "proteinas": 23.0, "carbohidratos": 0.0, "grasas": 14.0},
    "pata muslo": {"calorias": 220, "proteinas": 23.5, "carbohidratos": 0.0, "grasas": 13.0},
    "alita de pollo": {"calorias": 290, "proteinas": 20.0, "carbohidratos": 0.0, "grasas": 19.0},
    "menudos de pollo": {"calorias": 140, "proteinas": 22.0, "carbohidratos": 1.0, "grasas": 5.0},
    "higado de pollo": {"calorias": 160, "proteinas": 24.0, "carbohidratos": 1.0, "grasas": 6.0},
    "corazon de pollo": {"calorias": 150, "proteinas": 26.0, "carbohidratos": 0.0, "grasas": 5.0},
    "suprema": {"calorias": 165, "proteinas": 31.0, "carbohidratos": 0.0, "grasas": 3.6},
    "cuarto trasero de pollo": {"calorias": 225, "proteinas": 23.0, "carbohidratos": 0.0, "grasas": 14.0},

    # === CORTES DE CARNE VACUNA ===
    "bife de chorizo": {"calorias": 230, "proteinas": 24.0, "carbohidratos": 0.0, "grasas": 14.0},
    "lomo": {"calorias": 170, "proteinas": 25.0, "carbohidratos": 0.0, "grasas": 7.0},
    "cuadril": {"calorias": 180, "proteinas": 26.0, "carbohidratos": 0.0, "grasas": 8.0},
    "bola de lomo": {"calorias": 165, "proteinas": 25.0, "carbohidratos": 0.0, "grasas": 6.5},
    "peceto": {"calorias": 150, "proteinas": 24.0, "carbohidratos": 0.0, "grasas": 5.0},
    "roast beef": {"calorias": 240, "proteinas": 22.0, "carbohidratos": 0.0, "grasas": 16.0},
    "nalga": {"calorias": 160, "proteinas": 24.0, "carbohidratos": 0.0, "grasas": 6.0},
    "entraña": {"calorias": 220, "proteinas": 24.0, "carbohidratos": 0.0, "grasas": 13.0},
    "matambre": {"calorias": 250, "proteinas": 23.0, "carbohidratos": 0.0, "grasas": 17.0},
    "paleta": {"calorias": 210, "proteinas": 22.0, "carbohidratos": 0.0, "grasas": 13.0},

    # === PESCADO ===
    "merluza": {"calorias": 90, "proteinas": 19.0, "carbohidratos": 0.0, "grasas": 1.5},
    "salmon": {"calorias": 205, "proteinas": 20.0, "carbohidratos": 0.0, "grasas": 13.0},
    "atun al natural": {"calorias": 110, "proteinas": 24.0, "carbohidratos": 0.0, "grasas": 1.0},
    "atun en aceite": {"calorias": 190, "proteinas": 23.0, "carbohidratos": 0.0, "grasas": 10.0},
    "corvina": {"calorias": 105, "proteinas": 18.0, "carbohidratos": 0.0, "grasas": 3.0},
    "pejerrey": {"calorias": 95, "proteinas": 19.0, "carbohidratos": 0.0, "grasas": 1.5},

# === COOKIES Y TARTAS DULCES ===
    "lemon pie": {"calorias": 320, "proteinas": 4.0, "carbohidratos": 45.0, "grasas": 14.0},
    "cookie": {"calorias": 420, "proteinas": 5.0, "carbohidratos": 60.0, "grasas": 18.0},
    "cookie con chips de chocolate": {"calorias": 430, "proteinas": 5.0, "carbohidratos": 62.0, "grasas": 19.0},
    "cookie rellena": {"calorias": 460, "proteinas": 5.0, "carbohidratos": 58.0, "grasas": 24.0},
    "cookie rellena de dulce de leche": {"calorias": 450, "proteinas": 5.0, "carbohidratos": 60.0, "grasas": 22.0},
    "cookie rellena de nutella": {"calorias": 480, "proteinas": 5.0, "carbohidratos": 58.0, "grasas": 25.0},
    "cookie rellena de chocolate": {"calorias": 460, "proteinas": 5.0, "carbohidratos": 55.0, "grasas": 24.0},
    "cookie rellena de chocolate blanco": {"calorias": 470, "proteinas": 4.5, "carbohidratos": 56.0, "grasas": 25.0},
    "cookie rellena de pasta de mani": {"calorias": 490, "proteinas": 8.0, "carbohidratos": 50.0, "grasas": 28.0},
    "cookie rellena de frutos rojos": {"calorias": 430, "proteinas": 4.0, "carbohidratos": 65.0, "grasas": 18.0},
    "cookie red velvet": {"calorias": 450, "proteinas": 5.0, "carbohidratos": 60.0, "grasas": 21.0},

    
# === TORTAS Y POSTRES EXTRAS ===
    "torta invertida de manzana": {"calorias": 280, "proteinas": 3.0, "carbohidratos": 45.0, "grasas": 10.0},
    "torta oreo": {"calorias": 450, "proteinas": 5.0, "carbohidratos": 55.0, "grasas": 25.0},
    "torta de frutilla": {"calorias": 220, "proteinas": 3.0, "carbohidratos": 35.0, "grasas": 8.0},
    "pionono dulce": {"calorias": 310, "proteinas": 6.0, "carbohidratos": 50.0, "grasas": 10.0},
    "arrollado de dulce de leche": {"calorias": 340, "proteinas": 5.0, "carbohidratos": 55.0, "grasas": 12.0},
    "torta galesa": {"calorias": 400, "proteinas": 5.0, "carbohidratos": 60.0, "grasas": 18.0},
    "torta bombom": {"calorias": 460, "proteinas": 6.0, "carbohidratos": 50.0, "grasas": 26.0},
    "budin de pan": {"calorias": 250, "proteinas": 6.0, "carbohidratos": 45.0, "grasas": 5.0},
    "flan casero": {"calorias": 180, "proteinas": 6.0, "carbohidratos": 25.0, "grasas": 6.0},
    "torta de durazno": {"calorias": 240, "proteinas": 3.0, "carbohidratos": 38.0, "grasas": 9.0},
    "torta de ricota y durazno": {"calorias": 300, "proteinas": 7.0, "carbohidratos": 40.0, "grasas": 13.0},

    # === EMPANADAS EXTRAS ===
    "empanada cortada a cuchillo": {"calorias": 260, "proteinas": 12.0, "carbohidratos": 24.0, "grasas": 13.0},
    "empanada salteña": {"calorias": 250, "proteinas": 11.0, "carbohidratos": 25.0, "grasas": 12.0},
    "empanada tucumana": {"calorias": 255, "proteinas": 11.0, "carbohidratos": 25.0, "grasas": 12.5},
    "empanada de panceta y ciruela": {"calorias": 290, "proteinas": 9.0, "carbohidratos": 26.0, "grasas": 16.0},
    "empanada de cantimpalo": {"calorias": 300, "proteinas": 11.0, "carbohidratos": 24.0, "grasas": 18.0},
    "empanada de mondongo": {"calorias": 210, "proteinas": 10.0, "carbohidratos": 24.0, "grasas": 8.0},
    "empanada de provolone": {"calorias": 280, "proteinas": 12.0, "carbohidratos": 24.0, "grasas": 15.0},
    "empanada de carne suave": {"calorias": 250, "proteinas": 10.0, "carbohidratos": 25.0, "grasas": 12.0},

    # === PIZZAS EXTRAS ===
    "pizza de champignones": {"calorias": 230, "proteinas": 11.0, "carbohidratos": 32.0, "grasas": 7.0},
    "pizza de pepperoni": {"calorias": 290, "proteinas": 13.0, "carbohidratos": 31.0, "grasas": 14.0},
    "pizza de cantimpalo": {"calorias": 295, "proteinas": 13.0, "carbohidratos": 31.0, "grasas": 15.0},
    "pizza de panceta y huevo": {"calorias": 310, "proteinas": 14.0, "carbohidratos": 31.0, "grasas": 15.0},
    "pizza con papas fritas": {"calorias": 320, "proteinas": 10.0, "carbohidratos": 42.0, "grasas": 13.0},
    "pizza de roquefort": {"calorias": 295, "proteinas": 14.0, "carbohidratos": 31.0, "grasas": 14.0},
    "faina": {"calorias": 280, "proteinas": 10.0, "carbohidratos": 35.0, "grasas": 11.0},
    "faina con queso": {"calorias": 330, "proteinas": 14.0, "carbohidratos": 36.0, "grasas": 15.0},

    # === TARTAS EXTRAS ===
    "tarta de cebolla y queso": {"calorias": 240, "proteinas": 9.0, "carbohidratos": 22.0, "grasas": 13.0},
    "tarta de berenjena": {"calorias": 150, "proteinas": 5.0, "carbohidratos": 17.0, "grasas": 7.0},
    "tarta gallega": {"calorias": 230, "proteinas": 12.0, "carbohidratos": 24.0, "grasas": 10.0},
    "tarta de zapallo y choclo": {"calorias": 160, "proteinas": 5.0, "carbohidratos": 20.0, "grasas": 7.0},
    "tarta de pollo y champignones": {"calorias": 200, "proteinas": 11.0, "carbohidratos": 19.0, "grasas": 9.0},
    "tarta de caprese": {"calorias": 210, "proteinas": 9.0, "carbohidratos": 20.0, "grasas": 11.0},
    "tarta de humita": {"calorias": 180, "proteinas": 5.0, "carbohidratos": 25.0, "grasas": 7.0},

    # === OTRAS PASTAS Y RELLENOS ===
    "canelones de verdura": {"calorias": 160, "proteinas": 7.0, "carbohidratos": 22.0, "grasas": 5.0},
    "canelones de choclo": {"calorias": 180, "proteinas": 6.0, "carbohidratos": 26.0, "grasas": 6.0},
    "canelones de carne": {"calorias": 210, "proteinas": 11.0, "carbohidratos": 22.0, "grasas": 8.0},
    "lasagna de carne": {"calorias": 230, "proteinas": 12.0, "carbohidratos": 20.0, "grasas": 11.0},
    "lasagna de verdura": {"calorias": 180, "proteinas": 8.0, "carbohidratos": 20.0, "grasas": 7.0},
    "capeletis de pollo": {"calorias": 200, "proteinas": 10.0, "carbohidratos": 28.0, "grasas": 5.0},
    "capeletis de carne": {"calorias": 210, "proteinas": 11.0, "carbohidratos": 28.0, "grasas": 6.0},
    "agnolottis de ricota y nuez": {"calorias": 260, "proteinas": 9.0, "carbohidratos": 30.0, "grasas": 12.0},
    "tallarines al huevo": {"calorias": 150, "proteinas": 6.0, "carbohidratos": 28.0, "grasas": 2.0},
    "fideos de espinaca": {"calorias": 140, "proteinas": 5.0, "carbohidratos": 26.0, "grasas": 1.5},

    # === CARNES Y ACHURAS EXTRAS ===
    "asado de tira": {"calorias": 290, "proteinas": 23.0, "carbohidratos": 0.0, "grasas": 22.0},
    "ojo de bife": {"calorias": 250, "proteinas": 24.0, "carbohidratos": 0.0, "grasas": 16.0},
    "bife de lomo": {"calorias": 170, "proteinas": 26.0, "carbohidratos": 0.0, "grasas": 7.0},
    "costillar de cerdo": {"calorias": 280, "proteinas": 16.0, "carbohidratos": 0.0, "grasas": 24.0},
    "mollejas": {"calorias": 240, "proteinas": 15.0, "carbohidratos": 0.0, "grasas": 20.0},
    "rinones": {"calorias": 130, "proteinas": 18.0, "carbohidratos": 0.0, "grasas": 6.0},
    "corazon de vaca": {"calorias": 115, "proteinas": 17.0, "carbohidratos": 0.0, "grasas": 4.5},
    "lengua a la vinagreta": {"calorias": 280, "proteinas": 15.0, "carbohidratos": 1.0, "grasas": 24.0},
    "carrillera": {"calorias": 180, "proteinas": 21.0, "carbohidratos": 0.0, "grasas": 10.0},
    "osobuco": {"calorias": 190, "proteinas": 24.0, "carbohidratos": 0.0, "grasas": 10.0},

    # === PESCADOS Y MARISCOS EXTRAS ===
    "rabas": {"calorias": 220, "proteinas": 15.0, "carbohidratos": 18.0, "grasas": 10.0}, # Fritas
    "trucha": {"calorias": 150, "proteinas": 20.0, "carbohidratos": 0.0, "grasas": 7.0},
    "pacu": {"calorias": 180, "proteinas": 18.0, "carbohidratos": 0.0, "grasas": 12.0},
    "boga": {"calorias": 160, "proteinas": 19.0, "carbohidratos": 0.0, "grasas": 9.0},
    "calamar": {"calorias": 90, "proteinas": 16.0, "carbohidratos": 3.0, "grasas": 1.5},
    "langostinos": {"calorias": 100, "proteinas": 20.0, "carbohidratos": 0.0, "grasas": 1.0},
    "surimi": {"calorias": 100, "proteinas": 15.0, "carbohidratos": 7.0, "grasas": 1.0},
    "kanikama": {"calorias": 100, "proteinas": 15.0, "carbohidratos": 7.0, "grasas": 1.0},

    # === TORTAS Y POSTRES ===
    "torta de manzana": {"calorias": 250, "proteinas": 3.0, "carbohidratos": 40.0, "grasas": 9.0},
    "torta de ricota": {"calorias": 320, "proteinas": 8.0, "carbohidratos": 35.0, "grasas": 16.0},
    "pasta frola": {"calorias": 380, "proteinas": 5.0, "carbohidratos": 60.0, "grasas": 14.0},
    "pastafrola": {"calorias": 380, "proteinas": 5.0, "carbohidratos": 60.0, "grasas": 14.0},
    "lemon pie": {"calorias": 320, "proteinas": 4.0, "carbohidratos": 45.0, "grasas": 14.0},
    "cheesecake": {"calorias": 350, "proteinas": 6.0, "carbohidratos": 30.0, "grasas": 24.0},
    "selva negra": {"calorias": 340, "proteinas": 4.0, "carbohidratos": 45.0, "grasas": 16.0},
    "torta de chocolate": {"calorias": 370, "proteinas": 5.0, "carbohidratos": 50.0, "grasas": 18.0},
    "torta marmolada": {"calorias": 360, "proteinas": 5.0, "carbohidratos": 50.0, "grasas": 16.0},
    "torta de coco y dulce de leche": {"calorias": 410, "proteinas": 6.0, "carbohidratos": 55.0, "grasas": 20.0},
    "torta brownie": {"calorias": 420, "proteinas": 5.0, "carbohidratos": 55.0, "grasas": 22.0},
    "torta de naranja": {"calorias": 340, "proteinas": 5.0, "carbohidratos": 52.0, "grasas": 13.0},
    "torta de zanahoria": {"calorias": 380, "proteinas": 4.0, "carbohidratos": 48.0, "grasas": 20.0},
    "rogel": {"calorias": 400, "proteinas": 5.0, "carbohidratos": 60.0, "grasas": 16.0},
    "torta rogel": {"calorias": 400, "proteinas": 5.0, "carbohidratos": 60.0, "grasas": 16.0},
    "postre balcarce": {"calorias": 360, "proteinas": 5.0, "carbohidratos": 50.0, "grasas": 16.0},
    "torta balcarce": {"calorias": 360, "proteinas": 5.0, "carbohidratos": 50.0, "grasas": 16.0},
    "torta mil hojas": {"calorias": 420, "proteinas": 5.0, "carbohidratos": 45.0, "grasas": 25.0},
    
    # Clásicos de Parrilla y Rotisería
    "provoleta": {"calorias": 350, "proteinas": 22.0, "carbohidratos": 2.0, "grasas": 28.0},
    "matambre a la pizza": {"calorias": 280, "proteinas": 20.0, "carbohidratos": 5.0, "grasas": 20.0},
    "tortilla de papa": {"calorias": 170, "proteinas": 5.0, "carbohidratos": 18.0, "grasas": 9.0},
    # Tubérculos cocidos/hervidos
    "papa hervida": {"calorias": 87, "proteinas": 1.9, "carbohidratos": 20.0, "grasas": 0.1},
    "camote": {"calorias": 90, "proteinas": 2.0, "carbohidratos": 21.0, "grasas": 0.1},
    "calamote": {"calorias": 90, "proteinas": 2.0, "carbohidratos": 21.0, "grasas": 0.1},
    "batata": {"calorias": 90, "proteinas": 2.0, "carbohidratos": 21.0, "grasas": 0.1},
    "boniato": {"calorias": 90, "proteinas": 2.0, "carbohidratos": 21.0, "grasas": 0.1},
    # Milanesas (Promedio fritas/horno)
    "milanesa": {"calorias": 260, "proteinas": 19.0, "carbohidratos": 15.0, "grasas": 13.0},
    "milanesa de carne": {"calorias": 260, "proteinas": 19.0, "carbohidratos": 15.0, "grasas": 13.0},
    "milanesa de pollo": {"calorias": 250, "proteinas": 18.0, "carbohidratos": 15.0, "grasas": 12.0},
    "milanesa de cerdo": {"calorias": 270, "proteinas": 17.0, "carbohidratos": 15.0, "grasas": 15.0},
    "milanesa de soja": {"calorias": 220, "proteinas": 14.0, "carbohidratos": 18.0, "grasas": 10.0},
    
    # Pastas, Arroz y Guarniciones
    "arroz": {"calorias": 130, "proteinas": 2.7, "carbohidratos": 28.0, "grasas": 0.3},
    "fideos": {"calorias": 131, "proteinas": 5.0, "carbohidratos": 25.0, "grasas": 1.1},
    "ravioles": {"calorias": 200, "proteinas": 8.0, "carbohidratos": 30.0, "grasas": 5.0},
    "ñoquis": {"calorias": 160, "proteinas": 4.0, "carbohidratos": 32.0, "grasas": 1.5},
    "pure": {"calorias": 88, "proteinas": 1.5, "carbohidratos": 15.0, "grasas": 3.0},
    "puré": {"calorias": 88, "proteinas": 1.5, "carbohidratos": 15.0, "grasas": 3.0},
    "pure de papa": {"calorias": 88, "proteinas": 1.5, "carbohidratos": 15.0, "grasas": 3.0},
    "pure de calabaza": {"calorias": 45, "proteinas": 1.0, "carbohidratos": 10.0, "grasas": 0.5},
    "calabaza": {"calorias": 40, "proteinas": 1.0, "carbohidratos": 9.0, "grasas": 0.2},
    "pastel de papa": {"calorias": 140, "proteinas": 6.0, "carbohidratos": 12.0, "grasas": 7.0},
    
    # Panadería, Pizzas y Empanadas
    "pan": {"calorias": 265, "proteinas": 9.0, "carbohidratos": 49.0, "grasas": 3.2},
    "pan frances": {"calorias": 265, "proteinas": 9.0, "carbohidratos": 49.0, "grasas": 3.2},
    "pan lactal": {"calorias": 260, "proteinas": 8.0, "carbohidratos": 50.0, "grasas": 3.0},
    "pan lactal integral": {"calorias": 250, "proteinas": 10.0, "carbohidratos": 45.0, "grasas": 4.0},
    "galleta de arroz integral": {"calorias": 380, "proteinas": 8.0, "carbohidratos": 82.0, "grasas": 2.0},
    "tostadas de arroz": {"calorias": 380, "proteinas": 8.0, "carbohidratos": 82.0, "grasas": 2.0},
    "empanada de carne": {"calorias": 260, "proteinas": 10.0, "carbohidratos": 25.0, "grasas": 13.0},
    "empanada de jamon y queso": {"calorias": 250, "proteinas": 11.0, "carbohidratos": 24.0, "grasas": 12.0},
    "tarta de jamon y queso": {"calorias": 280, "proteinas": 12.0, "carbohidratos": 22.0, "grasas": 15.0},
    "pizza": {"calorias": 260, "proteinas": 11.0, "carbohidratos": 33.0, "grasas": 10.0},
    
    # Verduras y Frutas
    "tomate": {"calorias": 18, "proteinas": 0.9, "carbohidratos": 3.9, "grasas": 0.2},
    "zanahoria": {"calorias": 41, "proteinas": 0.9, "carbohidratos": 10.0, "grasas": 0.2},
    "acelga cocida": {"calorias": 20, "proteinas": 1.9, "carbohidratos": 4.1, "grasas": 0.1},
    "lechuga": {"calorias": 15, "proteinas": 1.4, "carbohidratos": 2.9, "grasas": 0.2},
    "cebolla": {"calorias": 40, "proteinas": 1.1, "carbohidratos": 9.0, "grasas": 0.1},
    "banana": {"calorias": 89, "proteinas": 1.1, "carbohidratos": 22.8, "grasas": 0.3},
    "manzana": {"calorias": 52, "proteinas": 0.3, "carbohidratos": 13.8, "grasas": 0.2},
    
    # Comida Rápida, Fiambres y Aderezos
    "salchicha": {"calorias": 250, "proteinas": 11.0, "carbohidratos": 3.0, "grasas": 21.0},
    "pancho": {"calorias": 270, "proteinas": 10.0, "carbohidratos": 25.0, "grasas": 14.0},
    "panchos": {"calorias": 270, "proteinas": 10.0, "carbohidratos": 25.0, "grasas": 14.0},
    "mayonesa": {"calorias": 680, "proteinas": 1.0, "carbohidratos": 1.0, "grasas": 75.0},
    "ketchup": {"calorias": 110, "proteinas": 1.0, "carbohidratos": 25.0, "grasas": 0.0},
    "mostaza": {"calorias": 60, "proteinas": 3.0, "carbohidratos": 5.0, "grasas": 3.0},
    "salsa golf": {"calorias": 450, "proteinas": 1.0, "carbohidratos": 15.0, "grasas": 45.0},
    
    # Grasas, Lácteos y Untables
    "mantequilla de mani": {"calorias": 588, "proteinas": 25.0, "carbohidratos": 20.0, "grasas": 50.0},
    "aceite de oliva": {"calorias": 884, "proteinas": 0.0, "carbohidratos": 0.0, "grasas": 100.0},
    "aceite": {"calorias": 884, "proteinas": 0.0, "carbohidratos": 0.0, "grasas": 100.0},
    "queso cremoso": {"calorias": 290, "proteinas": 19.0, "carbohidratos": 1.5, "grasas": 23.0},
    "queso cheddar": {"calorias": 402, "proteinas": 25.0, "carbohidratos": 1.3, "grasas": 33.0},
    "chedar": {"calorias": 402, "proteinas": 25.0, "carbohidratos": 1.3, "grasas": 33.0},
    "roquefort": {"calorias": 369, "proteinas": 21.0, "carbohidratos": 2.0, "grasas": 30.0},
    "queso crema": {"calorias": 250, "proteinas": 6.0, "carbohidratos": 4.0, "grasas": 24.0},
    "leche": {"calorias": 60, "proteinas": 3.2, "carbohidratos": 4.7, "grasas": 3.2},
    "yogur": {"calorias": 63, "proteinas": 3.7, "carbohidratos": 7.0, "grasas": 2.0},
    "mermelada": {"calorias": 250, "proteinas": 0.0, "carbohidratos": 60.0, "grasas": 0.0},
    "dulce de leche": {"calorias": 315, "proteinas": 6.0, "carbohidratos": 55.0, "grasas": 7.5},
    
    # Bebidas (con y sin alcohol)
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
    
    # Snacks y Dulces
    
    "helado": {"calorias": 200, "proteinas": 4.0, "carbohidratos": 24.0, "grasas": 10.0},
    "alfajor": {"calorias": 380, "proteinas": 6.0, "carbohidratos": 55.0, "grasas": 15.0},
    "bizcochitos": {"calorias": 450, "proteinas": 10.0, "carbohidratos": 50.0, "grasas": 25.0},
    "don satur": {"calorias": 450, "proteinas": 10.0, "carbohidratos": 50.0, "grasas": 25.0},
    "nesquik": {"calorias": 379, "proteinas": 4.5, "carbohidratos": 81.0, "grasas": 2.8},
    "chocotorta": {"calorias": 390, "proteinas": 6.0, "carbohidratos": 48.0, "grasas": 20.0},
    "tiramisu": {"calorias": 280, "proteinas": 4.5, "carbohidratos": 32.0, "grasas": 15.0} 
    # Tartas y Empanadas
    "tarta de verdura": {"calorias": 150, "proteinas": 5.0, "carbohidratos": 18.0, "grasas": 7.0},
    "empanada de verdura": {"calorias": 210, "proteinas": 6.0, "carbohidratos": 26.0, "grasas": 9.0},
    "empanada de pollo": {"calorias": 240, "proteinas": 12.0, "carbohidratos": 25.0, "grasas": 10.0},
    
    # Salsas y Lácteos
    "salsa de tomate": {"calorias": 30, "proteinas": 1.0, "carbohidratos": 6.0, "grasas": 0.2},
    "crema de leche": {"calorias": 340, "proteinas": 2.0, "carbohidratos": 3.0, "grasas": 35.0},
    
    # Bebidas y Cítricos
    "limon": {"calorias": 29, "proteinas": 1.1, "carbohidratos": 9.3, "grasas": 0.3},
    "jugo de limon": {"calorias": 22, "proteinas": 0.4, "carbohidratos": 7.0, "grasas": 0.2},
    "agua mineral": {"calorias": 0, "proteinas": 0.0, "carbohidratos": 0.0, "grasas": 0.0},
    "agua con limon": {"calorias": 2, "proteinas": 0.0, "carbohidratos": 0.5, "grasas": 0.0},
    "limonada": {"calorias": 40, "proteinas": 0.0, "carbohidratos": 10.0, "grasas": 0.0},
    
    # Frituras, Snacks y Picadas
    "papas fritas": {"calorias": 312, "proteinas": 3.4, "carbohidratos": 41.0, "grasas": 15.0}, # De rotisería/bastón
    "papas fritas de paquete": {"calorias": 536, "proteinas": 6.0, "carbohidratos": 50.0, "grasas": 35.0}, # Lays
    "chizitos": {"calorias": 500, "proteinas": 6.0, "carbohidratos": 55.0, "grasas": 30.0},
    "palitos": {"calorias": 480, "proteinas": 9.0, "carbohidratos": 60.0, "grasas": 22.0},
    "nachos": {"calorias": 500, "proteinas": 6.0, "carbohidratos": 60.0, "grasas": 25.0},
    "mani salado": {"calorias": 590, "proteinas": 25.0, "carbohidratos": 15.0, "grasas": 50.0},
    "puflitos": {"calorias": 400, "proteinas": 4.0, "carbohidratos": 75.0, "grasas": 8.0},
    
    # Galletitas y Chocolates
    "galletitas de agua": {"calorias": 420, "proteinas": 10.0, "carbohidratos": 70.0, "grasas": 12.0},
    "galletitas dulces": {"calorias": 450, "proteinas": 6.0, "carbohidratos": 70.0, "grasas": 16.0}, # Surtidas
    "chocolinas": {"calorias": 440, "proteinas": 6.0, "carbohidratos": 72.0, "grasas": 14.0},
    "oreo": {"calorias": 480, "proteinas": 5.0, "carbohidratos": 68.0, "grasas": 20.0},
    "chocolate": {"calorias": 535, "proteinas": 8.0, "carbohidratos": 59.0, "grasas": 30.0}, # Con leche
    "chocolate amargo": {"calorias": 550, "proteinas": 8.0, "carbohidratos": 45.0, "grasas": 35.0},
    "chocolate blanco": {"calorias": 540, "proteinas": 6.0, "carbohidratos": 59.0, "grasas": 32.0},
    
    # Panadería dulce
    "churros": {"calorias": 400, "proteinas": 5.0, "carbohidratos": 40.0, "grasas": 22.0},
    "alfajor de maicena": {"calorias": 390, "proteinas": 5.0, "carbohidratos": 60.0, "grasas": 15.0},

# Panqueques y Tortas
    "panqueques proteicos": {"calorias": 160, "proteinas": 15.0, "carbohidratos": 18.0, "grasas": 3.0},
    "panqueques de avena": {"calorias": 180, "proteinas": 7.0, "carbohidratos": 28.0, "grasas": 4.5},
    "torta de aceite": {"calorias": 380, "proteinas": 5.0, "carbohidratos": 50.0, "grasas": 18.0},
    "torta": {"calorias": 350, "proteinas": 5.0, "carbohidratos": 55.0, "grasas": 13.0},

# Legumbres, Guisos y Endulzantes
    "lenteja": {"calorias": 116, "proteinas": 9.0, "carbohidratos": 20.0, "grasas": 0.4},
    "lentejas": {"calorias": 116, "proteinas": 9.0, "carbohidratos": 20.0, "grasas": 0.4},
    "guiso de lentejas": {"calorias": 160, "proteinas": 8.0, "carbohidratos": 15.0, "grasas": 7.0},
    "arvejas": {"calorias": 81, "proteinas": 5.0, "carbohidratos": 14.0, "grasas": 0.4},
    "arbejas": {"calorias": 81, "proteinas": 5.0, "carbohidratos": 14.0, "grasas": 0.4},
    "miel": {"calorias": 304, "proteinas": 0.3, "carbohidratos": 82.0, "grasas": 0.0},
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
            
            # Comando de gspread para inmovilizar las primeras 2 filas visualmente
            worksheet.freeze(rows=2)
            
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
