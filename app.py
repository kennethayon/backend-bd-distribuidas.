
# USERNAME = 'kenneth_admin' 
# PASSWORD = 'C0d1g0#51' 
from flask import Flask, request, jsonify
from flask_cors import CORS
import pymssql

app = Flask(__name__)
CORS(app) 

# --- CONFIGURACIÓN DE TU BASE DE DATOS EN AZURE ---
SERVER = 'servidorkenneth.database.windows.net'
DATABASE = 'Papeleria_MainDB'
USERNAME = 'kenneth_admin' 
PASSWORD = 'C0d1g0#51' 

def get_db_connection():
    return pymssql.connect(server=SERVER, user=USERNAME, password=PASSWORD, database=DATABASE)

# --- RUTAS DE LOGIN Y REGISTRO ---
@app.route('/registro', methods=['POST'])
def registro():
    datos = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Cambiamos los ? por %s
        cursor.execute("""
            INSERT INTO Usuarios (nombre, usuario, correo, contrasena)
            VALUES (%s, %s, %s, %s)
        """, (datos['nombre'], datos['usuario'], datos['correo'], datos['contrasena']))
        conn.commit()
        return jsonify({'success': True, 'mensaje': 'Usuario registrado exitosamente'})
    except Exception as e:
        print("Error real de BD:", e) # Esto te ayudará a ver errores en la consola de Render
        return jsonify({'success': False, 'mensaje': 'Error, el usuario o correo ya existe'})
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    datos = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    # Cambiamos los ? por %s
    cursor.execute("""
        SELECT id_usuario, nombre FROM Usuarios 
        WHERE usuario = %s AND contrasena = %s
    """, (datos['usuario'], datos['contrasena']))
    
    usuario = cursor.fetchone()
    conn.close()
    
    if usuario:
        return jsonify({'success': True, 'nombre': usuario[1]})
    else:
        return jsonify({'success': False, 'mensaje': 'Usuario o contraseña incorrectos'})

# --- RUTAS DEL PUNTO DE VENTA ---
@app.route('/buscar_producto', methods=['GET'])
def buscar_producto():
    termino = request.args.get('q', '')
    conn = get_db_connection()
    cursor = conn.cursor()
    # Cambiamos los ? por %s
    cursor.execute("""
        SELECT id_producto, codigo_barras, nombre, precio, stock 
        FROM Productos 
        WHERE codigo_barras = %s OR nombre LIKE %s
    """, (termino, f'%{termino}%'))
    
    productos = [{'id_producto': r[0], 'codigo_barras': r[1], 'nombre': r[2], 'precio': float(r[3]), 'stock': r[4]} for r in cursor.fetchall()]
    conn.close()
    return jsonify(productos)

@app.route('/guardar_corte', methods=['POST'])
def guardar_corte():
    datos = request.json
    total_efectivo = sum([
        datos.get('b1000',0)*1000, datos.get('b500',0)*500, datos.get('b200',0)*200, 
        datos.get('b100',0)*100, datos.get('b50',0)*50, datos.get('b20',0)*20, 
        datos.get('m10',0)*10, datos.get('m5',0)*5, datos.get('m2',0)*2, 
        datos.get('m1',0)*1, datos.get('m05',0)*0.5
    ])
    gastos = float(datos.get('gastos_salidas', 0))
    total_calculado = total_efectivo - gastos

    conn = get_db_connection()
    cursor = conn.cursor()
    # Cambiamos los ? por %s
    cursor.execute("""
        INSERT INTO Cortes_Caja (b1000, b500, b200, b100, b50, b20, m10, m5, m2, m1, m05, gastos_salidas, total_calculado)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (datos.get('b1000',0), datos.get('b500',0), datos.get('b200',0), datos.get('b100',0), 
          datos.get('b50',0), datos.get('b20',0), datos.get('m10',0), datos.get('m5',0), 
          datos.get('m2',0), datos.get('m1',0), datos.get('m05',0), gastos, total_calculado))
    
    conn.commit()
    conn.close()
    return jsonify({'mensaje': 'Corte guardado', 'total': total_calculado})

@app.route('/agregar_producto', methods=['POST'])
def agregar_producto():
    datos = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Productos (codigo_barras, nombre, precio, stock)
            VALUES (%s, %s, %s, %s)
        """, (datos['codigo_barras'], datos['nombre'], datos['precio'], datos['stock']))
        conn.commit()
        return jsonify({'success': True, 'mensaje': '¡Producto agregado al inventario!'})
    except Exception as e:
        return jsonify({'success': False, 'mensaje': f'Error al agregar: {str(e)}'})
    finally:
        conn.close()

@app.route('/registrar_venta', methods=['POST'])
def registrar_venta():
    datos = request.json # Recibirá un arreglo de productos vendidos
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Por cada producto vendido, restamos la cantidad del stock en la BD
        for item in datos['productos']:
            cursor.execute("""
                UPDATE Productos 
                SET stock = stock - %s 
                WHERE id_producto = %s
            """, (item['cantidad'], item['id_producto']))
        conn.commit()
        return jsonify({'success': True, 'mensaje': 'Venta registrada. Stock actualizado.'})
    except Exception as e:
        return jsonify({'success': False, 'mensaje': f'Error en la venta: {str(e)}'})
    finally:
        conn.close()
        
if __name__ == '__main__':
    app.run(debug=True, port=5000)
