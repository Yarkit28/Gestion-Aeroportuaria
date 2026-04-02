# =============================================
# app.py - Sistema Aeropuerto (alineado con Nuevo inicio.sql)
# =============================================

from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta

# =============================================
# CONFIGURACIÓN FLASK
# =============================================

app = Flask(__name__)
app.secret_key = 'clave_ultra_secreta_cambia_esto'

# =============================================
# CONEXIÓN A BASE DE DATOS
# =============================================

def get_db_connection():
    try:
        return mysql.connector.connect(
            host='localhost',
            user='root',
            password='tuclave',
            database='aeropuerto',
            port=3306
        )
    except Error as e:
        print(f"❌ Error de conexión MySQL: {e}")
        return None

# =============================================
# UTILIDADES
# =============================================

def obtener_ciudades():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id_ciudad, nombre FROM Ciudades ORDER BY nombre")
    ciudades = cursor.fetchall()
    cursor.close()
    conn.close()
    return ciudades

# =============================================
# RUTA PRINCIPAL
# =============================================

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Obtener estadísticas para el dashboard
    cursor.execute("SELECT COUNT(*) as total FROM Vuelos WHERE estado = 'Programado'")
    total_vuelos = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM Pasajeros WHERE activo = TRUE")
    total_pasajeros = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM Reservas WHERE id_estado = 2")  # Confirmadas
    total_reservas = cursor.fetchone()['total']
    
    cursor.execute("SELECT SUM(precio_reserva) as total FROM Reservas WHERE id_estado = 2")
    ingresos_totales = cursor.fetchone()['total'] or 0
    
    cursor.close()
    conn.close()
    
    return render_template('index.html',
                         total_vuelos=total_vuelos,
                         total_pasajeros=total_pasajeros,
                         total_boletos=total_reservas,  # Cambié el nombre para coincidir con tu template
                         ingresos_totales=ingresos_totales)

# =============================================
# VUELOS
# =============================================

@app.route('/vuelos')
def vuelos():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT v.id_vuelo, v.numero_vuelo, v.fecha, v.hora_salida, v.hora_llegada,
               co.nombre AS origen, cd.nombre AS destino,
               a.nombre AS aerolinea, ta.modelo, fa.nombre AS fabricante,
               v.precio_base
        FROM Vuelos v
        JOIN Ciudades co ON v.id_ciudad_origen = co.id_ciudad
        JOIN Ciudades cd ON v.id_ciudad_destino = cd.id_ciudad
        JOIN Aerolineas a ON v.id_aerolinea = a.id_aerolinea
        JOIN TiposAvion ta ON v.id_tipo_avion = ta.id_tipo_avion
        JOIN FabricantesAvion fa ON ta.id_fabricante = fa.id_fabricante
        ORDER BY v.fecha, v.hora_salida
    """)

    vuelos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('vuelos.html', vuelos=vuelos)

@app.route('/vuelos/nuevo', methods=['GET', 'POST'])
def nuevo_vuelo():  # <-- ESTA ES LA ÚNICA FUNCIÓN nuevo_vuelo
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        try:
            # CORREGIR: Cambiar origen/destino por id_ciudad_origen/id_ciudad_destino
            cursor.execute("""
                INSERT INTO Vuelos (
                    numero_vuelo, id_aerolinea, id_piloto, id_tipo_avion,
                    id_ciudad_origen, id_ciudad_destino,
                    fecha, hora_salida, hora_llegada
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                f"MX-{datetime.now().strftime('%H%M%S')}",
                request.form['id_aerolinea'],
                request.form.get('id_piloto') or None,  # Permitir NULL
                request.form['id_tipo_avion'],
                request.form['id_ciudad_origen'],  # CAMBIADO
                request.form['id_ciudad_destino'],  # CAMBIADO
                request.form['fecha'],
                request.form['hora_salida'],
                request.form['hora_llegada']
            ))

            conn.commit()
            flash('✅ Vuelo creado correctamente (precio calculado por MySQL)', 'success')
            return redirect(url_for('vuelos'))

        except Exception as e:
            conn.rollback()
            flash(f'❌ Error al crear vuelo: {e}', 'danger')

    cursor.execute("SELECT * FROM Aerolineas WHERE activa = TRUE")
    aerolineas = cursor.fetchall()

    cursor.execute("SELECT * FROM Pilotos WHERE activo = TRUE")
    pilotos = cursor.fetchall()

    cursor.execute("""
        SELECT ta.id_tipo_avion, ta.modelo, fa.nombre AS fabricante
        FROM TiposAvion ta
        JOIN FabricantesAvion fa ON ta.id_fabricante = fa.id_fabricante
    """)
    tipos_avion = cursor.fetchall()

    ciudades = obtener_ciudades()
    
    # Obtener precios de rutas desde la BD
    cursor.execute("""
        SELECT 
            pr.id_recorrido,
            co.nombre AS origen,
            cd.nombre AS destino,
            pr.precio_base,
            pr.duracion_estimada_min
        FROM PreciosRecorrido pr
        JOIN Ciudades co ON pr.id_ciudad_origen = co.id_ciudad
        JOIN Ciudades cd ON pr.id_ciudad_destino = cd.id_ciudad
        WHERE pr.activo = TRUE
        ORDER BY co.nombre, cd.nombre
    """)
    precios_rutas = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('nuevo_vuelo.html',
                           aerolineas=aerolineas,
                           pilotos=pilotos,
                           tipos_avion=tipos_avion,
                           ciudades=ciudades,
                           precios_rutas=precios_rutas)  # <-- Agregar este parámetro

# =============================================
# PASAJEROS
# =============================================

@app.route('/pasajeros')
def pasajeros():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Pasajeros WHERE activo = TRUE ORDER BY nombre")
    pasajeros = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('pasajeros.html', pasajeros=pasajeros)


@app.route('/pasajeros/nuevo', methods=['GET', 'POST'])
def nuevo_pasajero():
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO Pasajeros (nombre, edad, email, telefono) VALUES (%s,%s,%s,%s)",
                (request.form['nombre'], request.form['edad'],
                 request.form.get('email'), request.form.get('telefono'))
            )
            conn.commit()
            flash('✅ Pasajero registrado', 'success')
            return redirect(url_for('pasajeros'))
        except Exception as e:
            conn.rollback()
            flash(f'❌ Error: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()
    return render_template('nuevo_pasajero.html')

@app.route('/pasajeros/eliminar/<int:id>', methods=['POST'])
def eliminar_pasajero_completo(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Llamar al procedimiento almacenado
        cursor.callproc('EliminarPasajeroCompleto', [id, ''])
        conn.commit()
        flash('✅ Pasajero eliminado correctamente', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'❌ Error al eliminar pasajero: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('pasajeros'))

# =============================================
# RESERVAS - VERSIÓN COMPLETA CON CÁLCULO AUTOMÁTICO
# =============================================

@app.route('/reservas/nueva', methods=['GET', 'POST'])
def nueva_reserva():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Cargar datos para el formulario (siempre)
    cursor.execute("""
        SELECT v.id_vuelo, v.numero_vuelo, v.fecha, v.hora_salida, v.hora_llegada,
               co.nombre as origen, cd.nombre as destino,
               v.precio_base as precio_turista,
               ad_t.asientos_disponibles as turista_disponible,
               ad_e.asientos_disponibles as ejecutiva_disponible,
               ad_p.asientos_disponibles as primera_disponible
        FROM Vuelos v
        JOIN Ciudades co ON v.id_ciudad_origen = co.id_ciudad
        JOIN Ciudades cd ON v.id_ciudad_destino = cd.id_ciudad
        LEFT JOIN AsientosDisponibles ad_t ON v.id_vuelo = ad_t.id_vuelo AND ad_t.id_tipo_asiento = 1
        LEFT JOIN AsientosDisponibles ad_e ON v.id_vuelo = ad_e.id_vuelo AND ad_e.id_tipo_asiento = 2
        LEFT JOIN AsientosDisponibles ad_p ON v.id_vuelo = ad_p.id_vuelo AND ad_p.id_tipo_asiento = 3
        WHERE v.estado = 'Programado'
          AND v.fecha >= CURDATE()
        ORDER BY v.fecha, v.hora_salida
    """)
    vuelos = cursor.fetchall()

    cursor.execute("SELECT * FROM TiposAsiento")
    tipos_asiento = cursor.fetchall()

    cursor.execute("SELECT id_pasajero, nombre, edad FROM Pasajeros WHERE activo = TRUE")
    pasajeros = cursor.fetchall()

    if request.method == 'POST':
        try:
            # =============================================
            # 1. OBTENER Y VALIDAR DATOS DEL FORMULARIO
            # =============================================
            id_vuelo = int(request.form['id_vuelo'])
            id_tipo_asiento = int(request.form['id_tipo_asiento'])
            
            # Verificar si es pasajero existente o nuevo
            if request.form.get('id_pasajero') and request.form['id_pasajero'] != 'nuevo':
                id_pasajero = int(request.form['id_pasajero'])
                
                # Obtener información del pasajero existente
                cursor.execute("SELECT * FROM Pasajeros WHERE id_pasajero = %s", (id_pasajero,))
                pasajero = cursor.fetchone()
                if not pasajero:
                    flash('❌ Pasajero no encontrado', 'danger')
                    return redirect(url_for('nueva_reserva'))
                    
                edad = pasajero['edad']
                nombre_pasajero = pasajero['nombre']
            else:
                # =============================================
                # 2. REGISTRAR NUEVO PASAJERO
                # =============================================
                nombre = request.form['nombre_nuevo'].strip()
                edad = int(request.form['edad_nuevo'])
                email = request.form.get('email_nuevo', '').strip() or None
                telefono = request.form.get('telefono_nuevo', '').strip() or None
                
                if not nombre or edad <= 0:
                    flash('❌ Nombre y edad son obligatorios para nuevo pasajero', 'danger')
                    return redirect(url_for('nueva_reserva'))
                
                cursor.execute("""
                    INSERT INTO Pasajeros (nombre, edad, email, telefono)
                    VALUES (%s, %s, %s, %s)
                """, (nombre, edad, email, telefono))
                
                id_pasajero = cursor.lastrowid
                nombre_pasajero = nombre
            
            # =============================================
            # 3. OBTENER PRECIO BASE DEL VUELO
            # =============================================
            cursor.execute("""
                SELECT v.precio_base, ta.modelo, fa.nombre as fabricante,
                       fa.multiplicador_precio as mult_fabricante
                FROM Vuelos v
                JOIN TiposAvion ta ON v.id_tipo_avion = ta.id_tipo_avion
                JOIN FabricantesAvion fa ON ta.id_fabricante = fa.id_fabricante
                WHERE v.id_vuelo = %s
            """, (id_vuelo,))
            vuelo_info = cursor.fetchone()
            
            if not vuelo_info:
                flash('❌ Vuelo no encontrado', 'danger')
                return redirect(url_for('nueva_reserva'))
            
            precio_base_vuelo = float(vuelo_info['precio_base'])
            
            # =============================================
            # 4. OBTENER MULTIPLICADOR DEL TIPO DE ASIENTO
            # =============================================
            cursor.execute("""
                SELECT descripcion, multiplicador_precio 
                FROM TiposAsiento 
                WHERE id_tipo_asiento = %s
            """, (id_tipo_asiento,))
            tipo_asiento_info = cursor.fetchone()
            
            if not tipo_asiento_info:
                flash('❌ Tipo de asiento no válido', 'danger')
                return redirect(url_for('nueva_reserva'))
            
            multiplicador_asiento = float(tipo_asiento_info['multiplicador_precio'])
            descripcion_asiento = tipo_asiento_info['descripcion']
            
            # =============================================
            # 5. CALCULAR DESCUENTO POR TIPO DE PASAJERO
            # =============================================
            if edad < 12:
                # Niño: 25% de descuento
                multiplicador_edad = 0.75
                tipo_pasajero = "Niño (25% descuento)"
            elif edad >= 60:
                # Adulto mayor: 30% de descuento
                multiplicador_edad = 0.70
                tipo_pasajero = "Adulto Mayor (30% descuento)"
            else:
                # Adulto: precio normal
                multiplicador_edad = 1.00
                tipo_pasajero = "Adulto (precio normal)"
            
            # =============================================
            # 6. CALCULAR PRECIO FINAL
            # =============================================
            precio_sin_descuento = precio_base_vuelo * multiplicador_asiento
            precio_final = precio_sin_descuento * multiplicador_edad
            
            # Redondear a 2 decimales
            precio_final = round(precio_final, 2)
            
            # =============================================
            # 7. VERIFICAR DISPONIBILIDAD DE ASIENTOS
            # =============================================
            cursor.execute("""
                SELECT asientos_disponibles 
                FROM AsientosDisponibles 
                WHERE id_vuelo = %s AND id_tipo_asiento = %s
            """, (id_vuelo, id_tipo_asiento))
            
            disponibilidad = cursor.fetchone()
            
            if not disponibilidad or disponibilidad['asientos_disponibles'] <= 0:
                flash(f'❌ No hay asientos disponibles en {descripcion_asiento}', 'danger')
                return redirect(url_for('nueva_reserva'))
            
            # =============================================
            # 8. CREAR LA RESERVA
            # =============================================
            codigo_reserva = f"RSV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            cursor.execute("""
                INSERT INTO Reservas (
                    id_vuelo, id_pasajero, id_tipo_asiento,
                    precio_reserva, codigo_reserva, fecha_expiracion, id_estado
                ) VALUES (%s, %s, %s, %s, %s, DATE_ADD(NOW(), INTERVAL 1 DAY), 1)
            """, (id_vuelo, id_pasajero, id_tipo_asiento, precio_final, codigo_reserva))
            
            # =============================================
            # 9. ACTUALIZAR DISPONIBILIDAD DE ASIENTOS
            # =============================================
            cursor.execute("""
                UPDATE AsientosDisponibles 
                SET asientos_disponibles = asientos_disponibles - 1,
                    asientos_reservados = asientos_reservados + 1,
                    fecha_actualizacion = NOW()
                WHERE id_vuelo = %s AND id_tipo_asiento = %s
            """, (id_vuelo, id_tipo_asiento))
            
            conn.commit()
            
            # =============================================
            # 10. PREPARAR MENSAJE DE CONFIRMACIÓN
            # =============================================
            mensaje = f"""
            ✅ RESERVA CONFIRMADA<br><br>
            <strong>Detalles:</strong><br>
            • Pasajero: {nombre_pasajero}<br>
            • Tipo: {tipo_pasajero}<br>
            • Asiento: {descripcion_asiento}<br>
            • Precio base: ${precio_base_vuelo:,.2f}<br>
            • Multiplicador asiento: {multiplicador_asiento}x<br>
            • Descuento: {round((1-multiplicador_edad)*100)}%<br>
            • <strong>Total a pagar: ${precio_final:,.2f}</strong><br>
            • Código de reserva: {codigo_reserva}<br>
            • Válido hasta: {(datetime.now() + timedelta(days=1)).strftime('%d/%m/%Y %H:%M')}
            """
            
            flash(mensaje, 'success')
            return redirect(url_for('reservas'))
            
        except Exception as e:
            conn.rollback()
            flash(f'❌ Error al crear reserva: {str(e)}', 'danger')
            print(f"Error detallado: {e}")  # Para debugging
    
    cursor.close()
    conn.close()
    
    return render_template('reservas/nueva.html',
                           vuelos=vuelos,
                           tipos_asiento=tipos_asiento,
                           pasajeros=pasajeros)

# =============================================
# LISTAR RESERVAS
# =============================================

@app.route('/reservas')
def reservas():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT r.id_reserva, r.codigo_reserva, r.fecha_reserva, r.precio_reserva,
               e.nombre as estado, e.id_estado, e.permite_pago,
               v.numero_vuelo, v.fecha, v.hora_salida,
               co.nombre as origen, cd.nombre as destino,
               p.nombre as pasajero, p.id_pasajero,
               t.descripcion as tipo_asiento,
               r.fecha_expiracion,
               (SELECT COUNT(*) FROM Boletos b WHERE b.id_reserva = r.id_reserva AND b.estado = 'Activo') as tiene_boleto
        FROM Reservas r
        JOIN EstadosReserva e ON r.id_estado = e.id_estado
        JOIN Vuelos v ON r.id_vuelo = v.id_vuelo
        JOIN Pasajeros p ON r.id_pasajero = p.id_pasajero
        JOIN TiposAsiento t ON r.id_tipo_asiento = t.id_tipo_asiento
        JOIN Ciudades co ON v.id_ciudad_origen = co.id_ciudad
        JOIN Ciudades cd ON v.id_ciudad_destino = cd.id_ciudad
        ORDER BY r.fecha_reserva DESC
    """)
    reservas = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('reservas.html', reservas=reservas)

# =============================================
# PAGAR RESERVA
# =============================================

@app.route('/reservas/pagar/<int:id_reserva>', methods=['POST'])
def pagar_reserva(id_reserva):
    print(f"DEBUG: Intentando pagar reserva ID: {id_reserva}")
    
    conn = get_db_connection()
    if not conn:
        flash('❌ Error de conexión a la base de datos', 'danger')
        return redirect(url_for('reservas'))
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 1. Verificar si la reserva existe y obtener datos necesarios
        cursor.execute("""
            SELECT r.*, e.nombre as estado_nombre, e.permite_pago,
                   v.numero_vuelo, p.nombre as pasajero_nombre,
                   v.fecha, v.hora_salida,
                   co.nombre as origen, cd.nombre as destino,
                   v.id_ciudad_origen, v.id_ciudad_destino,
                   v.id_aerolinea, v.id_tipo_avion
            FROM Reservas r
            JOIN EstadosReserva e ON r.id_estado = e.id_estado
            JOIN Vuelos v ON r.id_vuelo = v.id_vuelo
            JOIN Pasajeros p ON r.id_pasajero = p.id_pasajero
            JOIN Ciudades co ON v.id_ciudad_origen = co.id_ciudad
            JOIN Ciudades cd ON v.id_ciudad_destino = cd.id_ciudad
            WHERE r.id_reserva = %s
        """, (id_reserva,))
        
        reserva = cursor.fetchone()
        
        if not reserva:
            flash('❌ Reserva no encontrada', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('reservas'))
        
        print(f"DEBUG: Reserva encontrada - Estado: {reserva['estado_nombre']}, "
              f"Código: {reserva['codigo_reserva']}, "
              f"Permite pago: {reserva['permite_pago']}")
        
        # 2. Verificar si permite pago
        if not reserva['permite_pago']:
            flash(f'❌ Esta reserva está {reserva["estado_nombre"]} y no permite pago', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('reservas'))
        
        # 3. Verificar si no ha expirado (si tiene fecha_expiracion)
        if reserva.get('fecha_expiracion'):
            cursor.execute("""
                SELECT 1 
                FROM Reservas 
                WHERE id_reserva = %s AND fecha_expiracion > NOW()
            """, (id_reserva,))
            
            if not cursor.fetchone():
                flash('❌ La reserva ha expirado. Por favor, crea una nueva reserva.', 'danger')
                cursor.close()
                conn.close()
                return redirect(url_for('reservas'))
        
        # 4. Verificar disponibilidad de asientos
        cursor.execute("""
            SELECT asientos_disponibles 
            FROM AsientosDisponibles 
            WHERE id_vuelo = %s AND id_tipo_asiento = %s
            FOR UPDATE  -- Bloquear la fila para evitar condiciones de carrera
        """, (reserva['id_vuelo'], reserva['id_tipo_asiento']))
        
        disponibilidad = cursor.fetchone()
        
        if not disponibilidad or disponibilidad['asientos_disponibles'] <= 0:
            flash('❌ No hay asientos disponibles para confirmar esta reserva', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('reservas'))
        
        print(f"DEBUG: Todo validado. Asientos disponibles: {disponibilidad['asientos_disponibles']}")
        
        # 5. Actualizar estado de reserva a "Confirmada" (id_estado = 2)
        cursor.execute("""
            UPDATE Reservas 
            SET id_estado = 2  -- Confirmada
            WHERE id_reserva = %s
        """, (id_reserva,))
        
        print(f"DEBUG: Estado de reserva actualizado a Confirmada")
        
        # 6. Reducir disponibilidad de asientos
        cursor.execute("""
            UPDATE AsientosDisponibles 
            SET asientos_disponibles = asientos_disponibles - 1,
                asientos_reservados = asientos_reservados + 1,
                fecha_actualizacion = NOW()
            WHERE id_vuelo = %s AND id_tipo_asiento = %s
        """, (reserva['id_vuelo'], reserva['id_tipo_asiento']))
        
        print(f"DEBUG: Disponibilidad de asientos actualizada")
        
        # 7. Crear boleto
        import random
        from datetime import datetime
        
        # Generar código de boleto único
        codigo_boleto = f"BOL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Generar número de asiento (ejemplo simple)
        letras = ['A', 'B', 'C', 'D', 'E', 'F']
        filas = list(range(1, 31))
        numero_asiento = f"{random.choice(letras)}{random.choice(filas):02d}"
        
        # Obtener información del tipo de asiento
        cursor.execute("""
            SELECT descripcion FROM TiposAsiento WHERE id_tipo_asiento = %s
        """, (reserva['id_tipo_asiento'],))
        tipo_asiento_info = cursor.fetchone()
        descripcion_asiento = tipo_asiento_info['descripcion'] if tipo_asiento_info else "Asiento"
        
        # Obtener precio base del vuelo
        cursor.execute("SELECT precio_base FROM Vuelos WHERE id_vuelo = %s", (reserva['id_vuelo'],))
        vuelo_info = cursor.fetchone()
        precio_base = vuelo_info['precio_base'] if vuelo_info else reserva['precio_reserva']
        
        # Obtener información de aerolínea
        cursor.execute("""
            SELECT a.nombre as aerolinea, 
                   fa.nombre as fabricante,
                   ta.modelo as modelo_avion
            FROM Vuelos v
            JOIN Aerolineas a ON v.id_aerolinea = a.id_aerolinea
            JOIN TiposAvion ta ON v.id_tipo_avion = ta.id_tipo_avion
            JOIN FabricantesAvion fa ON ta.id_fabricante = fa.id_fabricante
            WHERE v.id_vuelo = %s
        """, (reserva['id_vuelo'],))
        info_vuelo = cursor.fetchone()
        
        # Insertar boleto
        cursor.execute("""
            INSERT INTO Boletos (
                id_reserva, id_vuelo, id_pasajero, id_tipo_asiento,
                precio_base, precio_final, codigo_boleto, numero_asiento,
                estado, fecha_compra
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Activo', NOW())
        """, (
            id_reserva,
            reserva['id_vuelo'],
            reserva['id_pasajero'],
            reserva['id_tipo_asiento'],
            precio_base,
            reserva['precio_reserva'],
            codigo_boleto,
            numero_asiento
        ))
        
        boleto_id = cursor.lastrowid
        print(f"DEBUG: Boleto creado con ID: {boleto_id}, Código: {codigo_boleto}")
        
        # 8. Registrar pago (si existe tabla MetodosPago)
        try:
            cursor.execute("SELECT id_metodo FROM MetodosPago LIMIT 1")
            metodo_pago = cursor.fetchone()
            
            if metodo_pago:
                referencia_pago = f"PAY-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                cursor.execute("""
                    INSERT INTO Pagos (
                        id_reserva, id_metodo, monto, fecha_pago,
                        estado, referencia
                    ) VALUES (%s, %s, %s, NOW(), 'Completado', %s)
                """, (
                    id_reserva,
                    metodo_pago['id_metodo'],
                    reserva['precio_reserva'],
                    referencia_pago
                ))
                print(f"DEBUG: Pago registrado con referencia: {referencia_pago}")
        except Exception as e:
            print(f"DEBUG: No se pudo registrar pago (puede que la tabla no exista): {e}")
            # Continuar sin error, el pago es opcional
        
        # Confirmar transacción
        conn.commit()
        
        print(f"DEBUG: Transacción completada exitosamente para reserva {id_reserva}")
        
        # Mensaje de éxito detallado
        mensaje = f"""
        ✅ <strong>RESERVA CONFIRMADA</strong><br><br>
        • <strong>Reserva:</strong> {reserva['codigo_reserva']}<br>
        • <strong>Pasajero:</strong> {reserva['pasajero_nombre']}<br>
        • <strong>Vuelo:</strong> {reserva['numero_vuelo']}<br>
        • <strong>Ruta:</strong> {reserva['origen']} → {reserva['destino']}<br>
        • <strong>Fecha:</strong> {reserva['fecha']} {reserva['hora_salida']}<br>
        • <strong>Asiento:</strong> {numero_asiento} ({descripcion_asiento})<br>
        • <strong>Boleto:</strong> {codigo_boleto}<br>
        • <strong>Total pagado:</strong> ${reserva['precio_reserva']:,.2f}<br>
        • <strong>Aerolínea:</strong> {info_vuelo['aerolinea'] if info_vuelo else 'N/A'}
        """
        
        flash(mensaje, 'success')
        
    except Exception as e:
        conn.rollback()
        error_msg = f'❌ Error al procesar el pago: {str(e)}'
        print(f"DEBUG ERROR: {error_msg}")
        import traceback
        traceback.print_exc()  # Imprimir traza completa para debugging
        flash(error_msg, 'danger')
    
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('reservas'))

# =============================================
# CANCELAR RESERVA
# =============================================

@app.route('/reservas/cancelar/<int:id_reserva>', methods=['POST'])
def cancelar_reserva(id_reserva):
    print(f"DEBUG: Intentando cancelar reserva ID: {id_reserva}")
    
    conn = get_db_connection()
    if not conn:
        flash('❌ Error de conexión a la base de datos', 'danger')
        return redirect(url_for('reservas'))
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 1. Obtener información completa de la reserva
        cursor.execute("""
            SELECT r.*, e.nombre as estado_nombre, e.permite_pago,
                   v.numero_vuelo, p.nombre as pasajero_nombre,
                   r.codigo_reserva, r.id_vuelo, r.id_tipo_asiento,
                   r.precio_reserva
            FROM Reservas r
            JOIN EstadosReserva e ON r.id_estado = e.id_estado
            JOIN Vuelos v ON r.id_vuelo = v.id_vuelo
            JOIN Pasajeros p ON r.id_pasajero = p.id_pasajero
            WHERE r.id_reserva = %s
        """, (id_reserva,))
        
        reserva = cursor.fetchone()
        
        if not reserva:
            flash('❌ Reserva no encontrada', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('reservas'))
        
        print(f"DEBUG: Reserva encontrada - ID: {reserva['id_reserva']}, "
              f"Estado: {reserva['estado_nombre']}, "
              f"Código: {reserva['codigo_reserva']}")
        
        # 2. Verificar si se puede cancelar (solo pendientes o confirmadas)
        if reserva['id_estado'] not in [1, 2]:  # 1=Pendiente, 2=Confirmada
            flash(f'❌ No se puede cancelar una reserva con estado: {reserva["estado_nombre"]}', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('reservas'))
        
        # 3. Actualizar estado de reserva a "Cancelada" (id_estado = 3)
        cursor.execute("""
            UPDATE Reservas 
            SET id_estado = 3  -- Cancelada
            WHERE id_reserva = %s
        """, (id_reserva,))
        
        print(f"DEBUG: Estado de reserva actualizado a Cancelada")
        
        # 4. Si la reserva estaba confirmada, liberar asiento
        if reserva['id_estado'] == 2:  # Confirmada
            print(f"DEBUG: Reserva confirmada - liberando asiento")
            
            # Verificar y liberar asiento con bloqueo
            cursor.execute("""
                SELECT asientos_disponibles, asientos_reservados 
                FROM AsientosDisponibles 
                WHERE id_vuelo = %s AND id_tipo_asiento = %s
                FOR UPDATE
            """, (reserva['id_vuelo'], reserva['id_tipo_asiento']))
            
            disponibilidad = cursor.fetchone()
            print(f"DEBUG: Disponibilidad actual - Disponibles: {disponibilidad['asientos_disponibles']}, "
                  f"Reservados: {disponibilidad['asientos_reservados']}")
            
            # Liberar asiento
            cursor.execute("""
                UPDATE AsientosDisponibles 
                SET asientos_disponibles = asientos_disponibles + 1,
                    asientos_reservados = asientos_reservados - 1,
                    fecha_actualizacion = NOW()
                WHERE id_vuelo = %s AND id_tipo_asiento = %s
            """, (reserva['id_vuelo'], reserva['id_tipo_asiento']))
            
            # 5. Cancelar boleto asociado si existe
            cursor.execute("""
                UPDATE Boletos 
                SET estado = 'Cancelado'
                WHERE id_reserva = %s AND estado = 'Activo'
            """, (id_reserva,))
            
            # Verificar cuántos boletos se cancelaron
            cursor.execute("SELECT ROW_COUNT() as filas_afectadas")
            resultado = cursor.fetchone()
            print(f"DEBUG: Boletos cancelados: {resultado['filas_afectadas']}")
            
            # 6. Reembolsar pago si existe (tabla Pagos)
            try:
                cursor.execute("""
                    UPDATE Pagos 
                    SET estado = 'Reembolsado'
                    WHERE id_reserva = %s AND estado = 'Completado'
                """, (id_reserva,))
                
                cursor.execute("SELECT ROW_COUNT() as filas_afectadas")
                pagos_reembolsados = cursor.fetchone()
                print(f"DEBUG: Pagos reembolsados: {pagos_reembolsados['filas_afectadas']}")
            except Exception as e:
                print(f"DEBUG: No se pudo actualizar pagos (puede que la tabla no exista): {e}")
        
        # Confirmar transacción
        conn.commit()
        
        print(f"DEBUG: Cancelación completada exitosamente para reserva {id_reserva}")
        
        # Mensaje según el estado
        if reserva['id_estado'] == 1:  # Pendiente
            mensaje = f'✅ Reserva {reserva["codigo_reserva"]} cancelada correctamente'
        else:  # Confirmada
            mensaje = f'✅ Reserva {reserva["codigo_reserva"]} cancelada correctamente. Se ha liberado el asiento y se aplicará reembolso de ${reserva["precio_reserva"]:,.2f}'
        
        flash(mensaje, 'success')
        
    except Exception as e:
        conn.rollback()
        error_msg = f'❌ Error al cancelar la reserva: {str(e)}'
        print(f"DEBUG ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        flash(error_msg, 'danger')
    
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('reservas'))

# =============================================
# VER BOLETO
# =============================================

@app.route('/reservas/boleto/<int:id_reserva>')
def ver_boleto_reserva(id_reserva):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT b.*, r.codigo_reserva,
               v.numero_vuelo, v.fecha, v.hora_salida, v.hora_llegada,
               co.nombre as origen, cd.nombre as destino,
               p.nombre as pasajero, p.edad,
               t.descripcion as tipo_asiento,
               a.nombre as aerolinea,
               fa.nombre as fabricante, ta.modelo as modelo_avion
        FROM Boletos b
        JOIN Reservas r ON b.id_reserva = r.id_reserva
        JOIN Vuelos v ON b.id_vuelo = v.id_vuelo
        JOIN Ciudades co ON v.id_ciudad_origen = co.id_ciudad
        JOIN Ciudades cd ON v.id_ciudad_destino = cd.id_ciudad
        JOIN Pasajeros p ON b.id_pasajero = p.id_pasajero
        JOIN TiposAsiento t ON b.id_tipo_asiento = t.id_tipo_asiento
        JOIN Aerolineas a ON v.id_aerolinea = a.id_aerolinea
        JOIN TiposAvion ta ON v.id_tipo_avion = ta.id_tipo_avion
        JOIN FabricantesAvion fa ON ta.id_fabricante = fa.id_fabricante
        WHERE b.id_reserva = %s AND b.estado = 'Activo'
    """, (id_reserva,))
    
    boleto = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not boleto:
        flash('❌ No se encontró boleto activo para esta reserva', 'danger')
        return redirect(url_for('reservas'))
    
    return render_template('ver_boleto.html', boleto=boleto)

# =============================================
# BOLETOS
# =============================================
#en desuso
'''
@app.route('/boletos')
def boletos():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.id_boleto, b.codigo_boleto, b.fecha_compra, b.precio_final,
               b.estado, b.numero_asiento,
               v.numero_vuelo, p.nombre as pasajero,
               t.descripcion as tipo_asiento
        FROM Boletos b
        JOIN Vuelos v ON b.id_vuelo = v.id_vuelo
        JOIN Pasajeros p ON b.id_pasajero = p.id_pasajero
        JOIN TiposAsiento t ON b.id_tipo_asiento = t.id_tipo_asiento
        ORDER BY b.fecha_compra DESC
    """)
    boletos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('boletos.html', boletos=boletos)'''

# =============================================
# DISPONIBILIDAD
# =============================================
#desuso
'''
@app.route('/disponibilidad')
def disponibilidad():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM VistaDisponibilidadCompleta
        WHERE fecha >= CURDATE()
        AND turista_disponibles + ejecutiva_disponibles + primera_disponibles > 0
        ORDER BY fecha, hora_salida
    """)
    vuelos_disponibles = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('disponibilidad.html', vuelos=vuelos_disponibles)'''

# =============================================
# REPORTES
# =============================================

@app.route('/reportes')
def reportes():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Estadísticas generales
    cursor.execute("SELECT COUNT(*) as total FROM Pasajeros WHERE activo = TRUE")
    total_pasajeros = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM Vuelos WHERE estado = 'Programado'")
    vuelos_programados = cursor.fetchone()['total']
    
    # CAMBIO AQUÍ: De "total_boletos" a "reservas_confirmadas"
    cursor.execute("SELECT COUNT(*) as total FROM Reservas WHERE id_estado = 2")  # Confirmadas
    reservas_confirmadas = cursor.fetchone()['total']
    
    # CAMBIO AQUÍ: De ingresos de boletos a ingresos de reservas confirmadas
    cursor.execute("SELECT SUM(precio_reserva) as total FROM Reservas WHERE id_estado = 2")
    ingresos_totales = cursor.fetchone()['total'] or 0
    
    # Vuelos más vendidos (basado en reservas, no boletos)
    cursor.execute("""
        SELECT v.numero_vuelo, 
               COUNT(r.id_reserva) as reservas_vendidas,
               SUM(r.precio_reserva) as ingresos
        FROM Vuelos v
        LEFT JOIN Reservas r ON v.id_vuelo = r.id_vuelo AND r.id_estado = 2  # Solo confirmadas
        GROUP BY v.id_vuelo
        ORDER BY reservas_vendidas DESC
        LIMIT 10
    """)
    vuelos_populares = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('reportes.html',
                         total_pasajeros=total_pasajeros,
                         vuelos_programados=vuelos_programados,
                         reservas_confirmadas=reservas_confirmadas,  # Cambiado de total_boletos
                         ingresos_totales=ingresos_totales,
                         vuelos_populares=vuelos_populares)

@app.route('/reportes/reservas')
def reportes_reservas():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Estadísticas generales (MODIFICADO para usar nombres que coincidan con la plantilla)
    cursor.execute("SELECT COUNT(*) as total FROM Reservas")
    total_reservas = cursor.fetchone()['total']
    
    cursor.execute("SELECT SUM(precio_reserva) as total FROM Reservas WHERE id_estado = 2")
    ingresos_totales = cursor.fetchone()['total'] or 0
    
    cursor.execute("SELECT COUNT(*) as total FROM Reservas WHERE id_estado = 2")
    reservas_confirmadas = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM Reservas WHERE id_estado = 1")
    reservas_pendientes = cursor.fetchone()['total']
    
    # Crear diccionario de stats (MODIFICADO para coincidir con nombres en plantilla)
    stats = {
        'total_reservas': total_reservas,
        'confirmadas': reservas_confirmadas,  # Cambiado de 'reservas_confirmadas'
        'pendientes': reservas_pendientes,    # Cambiado de 'reservas_pendientes'
        'ingresos_totales': ingresos_totales
    }
    
    # NUEVO: Reservas por Aerolínea (que la plantilla espera)
    cursor.execute("""
        SELECT a.nombre as aerolinea, 
               COUNT(r.id_reserva) as total_reservas,
               SUM(r.precio_reserva) as ingresos
        FROM Reservas r
        JOIN Vuelos v ON r.id_vuelo = v.id_vuelo
        JOIN Aerolineas a ON v.id_aerolinea = a.id_aerolinea
        GROUP BY a.id_aerolinea, a.nombre
        ORDER BY total_reservas DESC
    """)
    por_aerolinea = cursor.fetchall()
    
    # NUEVO: Últimas Reservas (que la plantilla espera)
    cursor.execute("""
        SELECT r.id_reserva, r.precio_reserva,
               p.nombre as pasajero,
               e.nombre as estado
        FROM Reservas r
        JOIN Pasajeros p ON r.id_pasajero = p.id_pasajero
        JOIN EstadosReserva e ON r.id_estado = e.id_estado
        ORDER BY r.fecha_reserva DESC
        LIMIT 10
    """)
    ultimas_reservas = cursor.fetchall()
    
    # Estadísticas de reservas por estado (opcional - si quieres mantenerlas)
    cursor.execute("""
        SELECT e.nombre as estado, COUNT(*) as cantidad,
               SUM(r.precio_reserva) as valor_total
        FROM Reservas r
        JOIN EstadosReserva e ON r.id_estado = e.id_estado
        GROUP BY e.id_estado, e.nombre
        ORDER BY cantidad DESC
    """)
    reservas_por_estado = cursor.fetchall()
    
    # Reservas por tipo de asiento (opcional - si quieres mantenerlas)
    cursor.execute("""
        SELECT t.descripcion as tipo_asiento, COUNT(*) as cantidad,
               AVG(r.precio_reserva) as precio_promedio
        FROM Reservas r
        JOIN TiposAsiento t ON r.id_tipo_asiento = t.id_tipo_asiento
        WHERE r.id_estado = 2  -- Solo confirmadas
        GROUP BY t.id_tipo_asiento, t.descripcion
        ORDER BY cantidad DESC
    """)
    reservas_por_asiento = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('reportes_reservas.html',
                         stats=stats,
                         por_aerolinea=por_aerolinea,
                         ultimas_reservas=ultimas_reservas,
                         reservas_por_estado=reservas_por_estado,
                         reservas_por_asiento=reservas_por_asiento)
# =============================================
# EJECUCIÓN
# =============================================

if __name__ == '__main__':
    app.run(debug=True)
