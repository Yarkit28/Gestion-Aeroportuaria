-- =============================================
-- SCRIPT DE REINICIO COMPLETO - ESTRUCTURA FINAL
-- =============================================

-- 2. CREAR NUEVA BASE DE DATOS
CREATE DATABASE aeropuerto;
USE aeropuerto;

-- =============================================
-- TABLAS BÁSICAS DEL SISTEMA
-- =============================================

-- 1. AEROLÍNEAS
CREATE TABLE Aerolineas (
    id_aerolinea INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    pais_origen VARCHAR(100),
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    activa BOOLEAN DEFAULT TRUE
);

-- 2. FABRICANTES DE AVIONES (NUEVA - SEPARADA DE TIPOS)
CREATE TABLE FabricantesAvion (
    id_fabricante INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    multiplicador_precio DECIMAL(3,2) NOT NULL DEFAULT 1.00,
    descripcion TEXT
);

-- 3. TIPOS DE AVIÓN (MEJORADA)
CREATE TABLE TiposAvion (
    id_tipo_avion INT AUTO_INCREMENT PRIMARY KEY,
    modelo VARCHAR(100) NOT NULL,
    id_fabricante INT NOT NULL,
    capacidad_total INT NOT NULL,
    capacidad_turista INT NOT NULL,
    capacidad_ejecutiva INT NOT NULL,
    capacidad_primera_clase INT NOT NULL,
    anio_fabricacion INT,
    FOREIGN KEY (id_fabricante) REFERENCES FabricantesAvion(id_fabricante),
    CHECK (capacidad_total = capacidad_turista + capacidad_ejecutiva + capacidad_primera_clase)
);

-- 4. PILOTOS
CREATE TABLE Pilotos (
    id_piloto INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    edad INT NOT NULL CHECK (edad >= 21),
    experiencia_anios INT NOT NULL CHECK (experiencia_anios >= 0),
    id_aerolinea INT,
    licencia VARCHAR(50) UNIQUE,
    activo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (id_aerolinea) REFERENCES Aerolineas(id_aerolinea)
);

-- 5. TIPOS DE ASIENTO
CREATE TABLE TiposAsiento (
    id_tipo_asiento INT AUTO_INCREMENT PRIMARY KEY,
    descripcion VARCHAR(50) NOT NULL UNIQUE,
    multiplicador_precio DECIMAL(3,2) NOT NULL DEFAULT 1.00
);

-- 6. CIUDADES (NUEVA - PARA NORMALIZAR)
CREATE TABLE Ciudades (
    id_ciudad INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    pais VARCHAR(100) NOT NULL DEFAULT 'México',
    codigo_aeropuerto VARCHAR(3) UNIQUE
);

-- 7. PRECIOS POR RUTA
CREATE TABLE PreciosRecorrido (
    id_recorrido INT AUTO_INCREMENT PRIMARY KEY,
    id_ciudad_origen INT NOT NULL,
    id_ciudad_destino INT NOT NULL,
    precio_base DECIMAL(10,2) NOT NULL,
    duracion_estimada_min INT NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    UNIQUE KEY unique_recorrido (id_ciudad_origen, id_ciudad_destino),
    FOREIGN KEY (id_ciudad_origen) REFERENCES Ciudades(id_ciudad),
    FOREIGN KEY (id_ciudad_destino) REFERENCES Ciudades(id_ciudad),
    CHECK (id_ciudad_origen != id_ciudad_destino)
);

-- =============================================
-- TABLAS TRANSACCIONALES PRINCIPALES
-- =============================================

-- 8. VUELOS (ESTRUCTURA FINAL MEJORADA)
CREATE TABLE Vuelos (
    id_vuelo INT AUTO_INCREMENT PRIMARY KEY,
    numero_vuelo VARCHAR(10) NOT NULL UNIQUE,
    id_aerolinea INT NOT NULL,
    id_piloto INT,
    id_tipo_avion INT NOT NULL,
    id_ciudad_origen INT NOT NULL,
    id_ciudad_destino INT NOT NULL,
    fecha DATE NOT NULL,
    hora_salida TIME NOT NULL,
    hora_llegada TIME NOT NULL,
    tipo_vuelo ENUM('Nacional') NOT NULL DEFAULT 'Nacional',
    precio_base DECIMAL(10,2) NOT NULL,
    estado ENUM('Programado', 'En curso', 'Completado', 'Cancelado') DEFAULT 'Programado',
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_aerolinea) REFERENCES Aerolineas(id_aerolinea),
    FOREIGN KEY (id_piloto) REFERENCES Pilotos(id_piloto),
    FOREIGN KEY (id_tipo_avion) REFERENCES TiposAvion(id_tipo_avion),
    FOREIGN KEY (id_ciudad_origen) REFERENCES Ciudades(id_ciudad),
    FOREIGN KEY (id_ciudad_destino) REFERENCES Ciudades(id_ciudad),
    CHECK (hora_llegada > hora_salida),
    INDEX idx_fecha_hora (fecha, hora_salida),
    INDEX idx_ruta (id_ciudad_origen, id_ciudad_destino)
);

-- 9. ESCALAS
CREATE TABLE Escalas (
    id_escala INT AUTO_INCREMENT PRIMARY KEY,
    id_vuelo INT NOT NULL,
    id_ciudad_escala INT NOT NULL,
    orden INT NOT NULL,
    duracion_min INT NOT NULL,
    notas TEXT,
    FOREIGN KEY (id_vuelo) REFERENCES Vuelos(id_vuelo) ON DELETE CASCADE,
    FOREIGN KEY (id_ciudad_escala) REFERENCES Ciudades(id_ciudad),
    UNIQUE KEY unique_escala_orden (id_vuelo, orden),
    CHECK (orden > 0),
    CHECK (duracion_min > 0)
);

-- 10. PASAJEROS (CON SOPORTE PARA RGPD)
CREATE TABLE Pasajeros (
    id_pasajero INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    edad INT NOT NULL CHECK (edad >= 0),
    email VARCHAR(100) UNIQUE,
    telefono VARCHAR(20),
    tipo_pasajero ENUM('Niño','Adulto','Adulto Mayor') GENERATED ALWAYS AS (
        CASE
            WHEN edad < 12 THEN 'Niño'
            WHEN edad BETWEEN 12 AND 59 THEN 'Adulto'
            ELSE 'Adulto Mayor'
        END
    ) STORED,
    activo BOOLEAN DEFAULT TRUE,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_eliminacion DATETIME NULL,
    INDEX idx_nombre (nombre),
    INDEX idx_activo (activo)
);

-- 11. ASIENTOS DISPONIBLES (POR VUELO Y TIPO)
CREATE TABLE AsientosDisponibles (
    id_disponibilidad INT AUTO_INCREMENT PRIMARY KEY,
    id_vuelo INT NOT NULL,
    id_tipo_asiento INT NOT NULL,
    asientos_totales INT NOT NULL,
    asientos_disponibles INT NOT NULL,
    asientos_reservados INT DEFAULT 0,
    fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_vuelo) REFERENCES Vuelos(id_vuelo) ON DELETE CASCADE,
    FOREIGN KEY (id_tipo_asiento) REFERENCES TiposAsiento(id_tipo_asiento),
    UNIQUE KEY unique_vuelo_asiento (id_vuelo, id_tipo_asiento),
    CHECK (asientos_disponibles >= 0),
    CHECK (asientos_totales = asientos_disponibles + asientos_reservados),
    INDEX idx_disponibilidad (asientos_disponibles)
);

-- =============================================
-- SISTEMA DE RESERVAS Y PAGOS
-- =============================================

-- 12. ESTADOS DE RESERVA
CREATE TABLE EstadosReserva (
    id_estado INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT,
    permite_pago BOOLEAN DEFAULT FALSE
);

-- 13. MÉTODOS DE PAGO
CREATE TABLE MetodosPago (
    id_metodo INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT,
    activo BOOLEAN DEFAULT TRUE,
    comision_porcentaje DECIMAL(5,2) DEFAULT 0
);

-- 14. RESERVAS
CREATE TABLE Reservas (
    id_reserva INT AUTO_INCREMENT PRIMARY KEY,
    id_vuelo INT NOT NULL,
    id_pasajero INT NOT NULL,
    id_tipo_asiento INT NOT NULL,
    id_estado INT DEFAULT 1,
    fecha_reserva DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_expiracion DATETIME,
    precio_reserva DECIMAL(10,2) NOT NULL,
    codigo_reserva VARCHAR(20) UNIQUE NOT NULL,
    notas TEXT,
    FOREIGN KEY (id_vuelo) REFERENCES Vuelos(id_vuelo),
    FOREIGN KEY (id_pasajero) REFERENCES Pasajeros(id_pasajero),
    FOREIGN KEY (id_tipo_asiento) REFERENCES TiposAsiento(id_tipo_asiento),
    FOREIGN KEY (id_estado) REFERENCES EstadosReserva(id_estado),
    INDEX idx_fecha_expiracion (fecha_expiracion),
    INDEX idx_codigo_reserva (codigo_reserva),
    INDEX idx_reserva_estado (id_estado, fecha_reserva)
);

-- 15. PAGOS
CREATE TABLE Pagos (
    id_pago INT AUTO_INCREMENT PRIMARY KEY,
    id_reserva INT NOT NULL,
    id_metodo INT NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    fecha_pago DATETIME DEFAULT CURRENT_TIMESTAMP,
    estado ENUM('Pendiente', 'Completado', 'Fallido', 'Reembolsado') DEFAULT 'Pendiente',
    referencia VARCHAR(100) UNIQUE,
    detalles TEXT,
    FOREIGN KEY (id_reserva) REFERENCES Reservas(id_reserva),
    FOREIGN KEY (id_metodo) REFERENCES MetodosPago(id_metodo),
    INDEX idx_estado_pago (estado, fecha_pago),
    INDEX idx_referencia (referencia)
);

-- 16. BOLETOS (CONFIRMADOS)
CREATE TABLE Boletos (
    id_boleto INT AUTO_INCREMENT PRIMARY KEY,
    id_reserva INT NOT NULL,
    id_vuelo INT NOT NULL,
    id_pasajero INT NOT NULL,
    id_tipo_asiento INT NOT NULL,
    precio_base DECIMAL(10,2) NOT NULL,
    precio_final DECIMAL(10,2) NOT NULL,
    fecha_compra DATETIME DEFAULT CURRENT_TIMESTAMP,
    estado ENUM('Activo', 'Usado', 'Cancelado', 'Reembolsado') DEFAULT 'Activo',
    codigo_boleto VARCHAR(20) UNIQUE NOT NULL,
    numero_asiento VARCHAR(10),
    notas TEXT,
    FOREIGN KEY (id_reserva) REFERENCES Reservas(id_reserva),
    FOREIGN KEY (id_vuelo) REFERENCES Vuelos(id_vuelo),
    FOREIGN KEY (id_pasajero) REFERENCES Pasajeros(id_pasajero),
    FOREIGN KEY (id_tipo_asiento) REFERENCES TiposAsiento(id_tipo_asiento),
    INDEX idx_estado_boleto (estado),
    INDEX idx_codigo_boleto (codigo_boleto),
    INDEX idx_boleto_fecha (fecha_compra, id_vuelo)
);

-- =============================================
-- TABLAS DE AUDITORÍA Y HISTÓRICO
-- =============================================

-- 17. PASAJEROS ELIMINADOS (AUDITORÍA RGPD)
CREATE TABLE PasajerosEliminados (
    id_auditoria INT AUTO_INCREMENT PRIMARY KEY,
    id_pasajero_original INT NOT NULL,
    nombre_original VARCHAR(100),
    fecha_eliminacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_boletos_cancelados INT DEFAULT 0,
    total_reservas_canceladas INT DEFAULT 0,
    ingresos_descontados DECIMAL(10,2) DEFAULT 0,
    motivo VARCHAR(255),
    ejecutado_por VARCHAR(100) DEFAULT 'SISTEMA',
    INDEX idx_fecha_eliminacion (fecha_eliminacion)
);

-- 18. RESERVAS EXPIRADAS
CREATE TABLE ReservasExpiradas (
    id_auditoria INT AUTO_INCREMENT PRIMARY KEY,
    id_reserva INT,
    id_vuelo INT,
    id_pasajero INT,
    id_tipo_asiento INT,
    precio_reserva DECIMAL(10,2),
    fecha_reserva DATETIME,
    fecha_expiracion DATETIME,
    fecha_eliminacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    motivo VARCHAR(100),
    INDEX idx_fecha_eliminacion (fecha_eliminacion)
);

-- 19. LOG DE CAMBIOS EN VUELOS
CREATE TABLE LogCambiosVuelos (
    id_log INT AUTO_INCREMENT PRIMARY KEY,
    id_vuelo INT NOT NULL,
    campo_modificado VARCHAR(50),
    valor_anterior TEXT,
    valor_nuevo TEXT,
    fecha_cambio DATETIME DEFAULT CURRENT_TIMESTAMP,
    modificado_por VARCHAR(100),
    FOREIGN KEY (id_vuelo) REFERENCES Vuelos(id_vuelo),
    INDEX idx_fecha_cambio (fecha_cambio)
);

-- =============================================
-- DATOS INICIALES (CONFIGURACIÓN)
-- =============================================

-- 1. FABRICANTES DE AVIONES
INSERT INTO FabricantesAvion (nombre, multiplicador_precio, descripcion) VALUES
('Airbus', 0.9, 'Aviones europeos, eficientes en combustible'),
('Boeing', 1.2, 'Aviones estadounidenses, alta capacidad'),
('Embraer', 1.0, 'Aviones brasileños, ideales para rutas regionales');

-- 2. TIPOS DE ASIENTO
INSERT INTO TiposAsiento (descripcion, multiplicador_precio) VALUES
('Turista', 1.00),
('Ejecutiva', 1.50),
('Primera Clase', 2.50);

-- 3. CIUDADES (SOLO NACIONALES - MÉXICO)
INSERT INTO Ciudades (nombre, codigo_aeropuerto) VALUES
('Ciudad de México', 'MEX'),
('Cancún', 'CUN'),
('Guadalajara', 'GDL'),
('Monterrey', 'MTY'),
('Tijuana', 'TIJ'),
('Mérida', 'MID'),
('Los Cabos', 'SJD'),
('Puerto Vallarta', 'PVR'),
('Oaxaca', 'OAX'),
('Huatulco', 'HUX');

-- 4. PRECIOS POR RUTA (EJEMPLOS)
INSERT INTO PreciosRecorrido (id_ciudad_origen, id_ciudad_destino, precio_base, duracion_estimada_min) VALUES
(1, 2, 2500.00, 120),  -- CDMX -> Cancún
(1, 3, 1200.00, 90),   -- CDMX -> Guadalajara
(1, 4, 1500.00, 100),  -- CDMX -> Monterrey
(2, 3, 2800.00, 150),  -- Cancún -> Guadalajara
(2, 4, 3200.00, 180),  -- Cancún -> Monterrey
(3, 4, 1300.00, 110);  -- Guadalajara -> Monterrey

-- 5. ESTADOS DE RESERVA
INSERT INTO EstadosReserva (id_estado, nombre, descripcion, permite_pago) VALUES
(1, 'Pendiente', 'Reserva creada, pendiente de pago', TRUE),
(2, 'Confirmada', 'Reserva pagada y confirmada', FALSE),
(3, 'Cancelada', 'Reserva cancelada', FALSE),
(4, 'Expirada', 'Reserva expirada por falta de pago', FALSE);

-- 6. MÉTODOS DE PAGO
INSERT INTO MetodosPago (nombre, descripcion, comision_porcentaje) VALUES
('Tarjeta de Crédito/Débito', 'Pago con tarjeta bancaria', 3.5),
('Transferencia SPEI', 'Transferencia bancaria electrónica', 0.0),
('PayPal', 'Pago electrónico seguro', 4.0),
('Efectivo en ventanilla', 'Pago físico en aeropuerto', 0.0);

-- 7. AEROLÍNEAS
INSERT INTO Aerolineas (nombre, pais_origen) VALUES
('Aeroméxico', 'México'),
('Volaris', 'México'),
('Viva Aerobus', 'México'),
('Interjet', 'México');

-- =============================================
-- FUNCIONES Y PROCEDIMIENTOS
-- =============================================

-- 1. FUNCIÓN: CALCULAR PRECIO BASE DE VUELO
DELIMITER //

CREATE FUNCTION CalcularPrecioBaseVuelo(
    p_id_ciudad_origen INT,
    p_id_ciudad_destino INT,
    p_id_fabricante INT,
    p_id_tipo_asiento INT
) RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE v_precio_ruta DECIMAL(10,2);
    DECLARE v_multiplicador_fabricante DECIMAL(3,2);
    DECLARE v_multiplicador_asiento DECIMAL(3,2);
    DECLARE v_precio_final DECIMAL(10,2);
    
    -- Obtener precio de la ruta
    SELECT precio_base INTO v_precio_ruta
    FROM PreciosRecorrido 
    WHERE id_ciudad_origen = p_id_ciudad_origen 
      AND id_ciudad_destino = p_id_ciudad_destino
      AND activo = TRUE;
    
    -- Si no existe directo, buscar inverso
    IF v_precio_ruta IS NULL THEN
        SELECT precio_base INTO v_precio_ruta
        FROM PreciosRecorrido 
        WHERE id_ciudad_origen = p_id_ciudad_destino 
          AND id_ciudad_destino = p_id_ciudad_origen
          AND activo = TRUE;
    END IF;
    
    -- Si aún no hay, precio por defecto
    IF v_precio_ruta IS NULL THEN
        SET v_precio_ruta = 1000.00;
    END IF;
    
    -- Obtener multiplicadores
    SELECT multiplicador_precio INTO v_multiplicador_fabricante
    FROM FabricantesAvion WHERE id_fabricante = p_id_fabricante;
    
    SELECT multiplicador_precio INTO v_multiplicador_asiento
    FROM TiposAsiento WHERE id_tipo_asiento = p_id_tipo_asiento;
    
    -- Calcular precio final
    SET v_precio_final = v_precio_ruta * 
                         COALESCE(v_multiplicador_fabricante, 1.0) * 
                         COALESCE(v_multiplicador_asiento, 1.0);
    
    RETURN ROUND(v_precio_final, 2);
END //

DELIMITER ;

-- 2. PROCEDIMIENTO: ELIMINAR PASAJERO COMPLETO
DELIMITER //

CREATE PROCEDURE EliminarPasajeroCompleto(
    IN  p_id_pasajero INT,
    OUT p_mensaje VARCHAR(500)
)
BEGIN
    DECLARE v_nombre_original VARCHAR(100);
    DECLARE v_total_boletos INT DEFAULT 0;
    DECLARE v_total_reservas INT DEFAULT 0;
    DECLARE v_ingresos_descontados DECIMAL(10,2) DEFAULT 0;
    DECLARE v_sqlstate CHAR(5);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS CONDITION 1 v_sqlstate = RETURNED_SQLSTATE;
        ROLLBACK;
        SET p_mensaje = CONCAT('❌ Error SQLSTATE: ', v_sqlstate);
    END;

    START TRANSACTION;

    -- Obtener información del pasajero
    SELECT 
        p.nombre,
        COUNT(DISTINCT b.id_boleto),
        COUNT(DISTINCT r.id_reserva),
        COALESCE(SUM(b.precio_final), 0) + COALESCE(SUM(r.precio_reserva), 0)
    INTO 
        v_nombre_original,
        v_total_boletos,
        v_total_reservas,
        v_ingresos_descontados
    FROM Pasajeros p
    LEFT JOIN Boletos b ON p.id_pasajero = b.id_pasajero AND b.estado = 'Activo'
    LEFT JOIN Reservas r ON p.id_pasajero = r.id_pasajero AND r.id_estado IN (1, 2)
    WHERE p.id_pasajero = p_id_pasajero
    GROUP BY p.id_pasajero;

    -- Verificar existencia
    IF v_nombre_original IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Pasajero no encontrado';
    END IF;

    -- Cancelar boletos activos
    UPDATE Boletos
    SET 
        estado = 'Cancelado',
        precio_final = 0,
        notas = CONCAT('Cancelado por eliminación de pasajero: ', NOW())
    WHERE id_pasajero = p_id_pasajero
      AND estado = 'Activo';

    -- Cancelar reservas activas
    UPDATE Reservas
    SET 
        id_estado = 3, -- Cancelada
        precio_reserva = 0,
        notas = CONCAT('Cancelada por eliminación de pasajero: ', NOW())
    WHERE id_pasajero = p_id_pasajero
      AND id_estado IN (1, 2);

    -- Revertir pagos completados
    UPDATE Pagos p
    JOIN Reservas r ON p.id_reserva = r.id_reserva
    SET 
        p.estado = 'Reembolsado',
        p.detalles = CONCAT('Reembolsado por eliminación de pasajero: ', NOW())
    WHERE r.id_pasajero = p_id_pasajero
      AND p.estado = 'Completado';

    -- Anonimizar pasajero
    UPDATE Pasajeros
    SET 
        nombre = CONCAT('Usuario_Eliminado_', LPAD(p_id_pasajero, 6, '0')),
        email = NULL,
        telefono = NULL,
        edad = 0,
        activo = FALSE,
        fecha_eliminacion = NOW()
    WHERE id_pasajero = p_id_pasajero;

    -- Registrar auditoría
    INSERT INTO PasajerosEliminados (
        id_pasajero_original,
        nombre_original,
        fecha_eliminacion,
        total_boletos_cancelados,
        total_reservas_canceladas,
        ingresos_descontados,
        motivo
    ) VALUES (
        p_id_pasajero,
        v_nombre_original,
        NOW(),
        v_total_boletos,
        v_total_reservas,
        v_ingresos_descontados,
        'Eliminación completa solicitada'
    );

    COMMIT;

    -- Mensaje final
    SET p_mensaje = CONCAT(
        '✅ Pasajero "', v_nombre_original, '" eliminado correctamente. ',
        'Boletos cancelados: ', v_total_boletos, '. ',
        'Reservas canceladas: ', v_total_reservas, '. ',
        'Ingresos descontados: $', ROUND(v_ingresos_descontados, 2)
    );

END //

DELIMITER ;

-- 3. PROCEDIMIENTO: RESERVAR ASIENTOS
DELIMITER //

CREATE PROCEDURE ReservarAsientos(
    IN p_id_vuelo INT,
    IN p_id_tipo_asiento INT,
    IN p_cantidad INT,
    OUT p_exito BOOLEAN,
    OUT p_mensaje VARCHAR(255)
)
BEGIN
    DECLARE v_disponibles INT DEFAULT 0;
    
    -- Bloquear registro para evitar condiciones de carrera
    SELECT asientos_disponibles INTO v_disponibles
    FROM AsientosDisponibles 
    WHERE id_vuelo = p_id_vuelo AND id_tipo_asiento = p_id_tipo_asiento
    FOR UPDATE;
    
    IF v_disponibles IS NULL THEN
        SET p_exito = FALSE;
        SET p_mensaje = '❌ Tipo de asiento no disponible para este vuelo';
    ELSEIF v_disponibles >= p_cantidad AND p_cantidad > 0 THEN
        -- Actualizar disponibilidad
        UPDATE AsientosDisponibles 
        SET 
            asientos_disponibles = asientos_disponibles - p_cantidad,
            asientos_reservados = asientos_reservados + p_cantidad,
            fecha_actualizacion = CURRENT_TIMESTAMP
        WHERE id_vuelo = p_id_vuelo AND id_tipo_asiento = p_id_tipo_asiento;
        
        SET p_exito = TRUE;
        SET p_mensaje = CONCAT('✅ Se reservaron ', p_cantidad, 
                              ' asiento(s). Quedan ', (v_disponibles - p_cantidad), 
                              ' disponibles.');
    ELSE
        SET p_exito = FALSE;
        SET p_mensaje = CONCAT('❌ No hay suficientes asientos disponibles. ',
                              'Disponibles: ', v_disponibles, 
                              ', Solicitados: ', p_cantidad);
    END IF;
END //

DELIMITER ;

-- =============================================
-- TRIGGERS
-- =============================================

-- 1. TRIGGER: INICIALIZAR ASIENTOS AL CREAR VUELO
DELIMITER //

CREATE TRIGGER InicializarAsientosNuevoVuelo
AFTER INSERT ON Vuelos
FOR EACH ROW
BEGIN
    DECLARE v_capacidad_turista INT;
    DECLARE v_capacidad_ejecutiva INT;
    DECLARE v_capacidad_primera INT;
    
    -- Obtener capacidades del avión
    SELECT 
        capacidad_turista,
        capacidad_ejecutiva,
        capacidad_primera_clase
    INTO 
        v_capacidad_turista,
        v_capacidad_ejecutiva,
        v_capacidad_primera
    FROM TiposAvion 
    WHERE id_tipo_avion = NEW.id_tipo_avion;
    
    -- Insertar disponibilidad para cada tipo de asiento
    -- Turista (id_tipo_asiento = 1)
    INSERT INTO AsientosDisponibles (id_vuelo, id_tipo_asiento, asientos_totales, asientos_disponibles)
    VALUES (NEW.id_vuelo, 1, v_capacidad_turista, v_capacidad_turista);
    
    -- Ejecutiva (id_tipo_asiento = 2)
    INSERT INTO AsientosDisponibles (id_vuelo, id_tipo_asiento, asientos_totales, asientos_disponibles)
    VALUES (NEW.id_vuelo, 2, v_capacidad_ejecutiva, v_capacidad_ejecutiva);
    
    -- Primera Clase (id_tipo_asiento = 3)
    INSERT INTO AsientosDisponibles (id_vuelo, id_tipo_asiento, asientos_totales, asientos_disponibles)
    VALUES (NEW.id_vuelo, 3, v_capacidad_primera, v_capacidad_primera);
END //

DELIMITER ;

-- 2. TRIGGER: CALCULAR PRECIO AL CREAR VUELO
DELIMITER //

CREATE TRIGGER CalcularPrecioVuelo
BEFORE INSERT ON Vuelos
FOR EACH ROW
BEGIN
    DECLARE v_id_fabricante INT;
    
    -- Obtener fabricante del avión
    SELECT id_fabricante INTO v_id_fabricante
    FROM TiposAvion WHERE id_tipo_avion = NEW.id_tipo_avion;
    
    -- Calcular precio base para asiento turista
    SET NEW.precio_base = CalcularPrecioBaseVuelo(
        NEW.id_ciudad_origen,
        NEW.id_ciudad_destino,
        v_id_fabricante,
        1  -- Turista como base
    );
END //

DELIMITER ;

-- 3. TRIGGER: LOG DE CAMBIOS EN VUELOS
DELIMITER //

CREATE TRIGGER LogCambiosVuelosTrigger
AFTER UPDATE ON Vuelos
FOR EACH ROW
BEGIN
    -- Registrar cambios en precio
    IF OLD.precio_base != NEW.precio_base THEN
        INSERT INTO LogCambiosVuelos (id_vuelo, campo_modificado, valor_anterior, valor_nuevo)
        VALUES (NEW.id_vuelo, 'precio_base', OLD.precio_base, NEW.precio_base);
    END IF;
    
    -- Registrar cambios en estado
    IF OLD.estado != NEW.estado THEN
        INSERT INTO LogCambiosVuelos (id_vuelo, campo_modificado, valor_anterior, valor_nuevo)
        VALUES (NEW.id_vuelo, 'estado', OLD.estado, NEW.estado);
    END IF;
    
    -- Registrar cambios en horarios
    IF OLD.hora_salida != NEW.hora_salida OR OLD.hora_llegada != NEW.hora_llegada THEN
        INSERT INTO LogCambiosVuelos (id_vuelo, campo_modificado, valor_anterior, valor_nuevo)
        VALUES (NEW.id_vuelo, 'horarios', 
                CONCAT(OLD.hora_salida, '-', OLD.hora_llegada),
                CONCAT(NEW.hora_salida, '-', NEW.hora_llegada));
    END IF;
END //

DELIMITER ;

-- =============================================
-- VISTAS ÚTILES
-- =============================================

-- 1. VISTA: DISPONIBILIDAD COMPLETA
CREATE OR REPLACE VIEW VistaDisponibilidadCompleta AS
SELECT 
    v.id_vuelo,
    v.numero_vuelo,
    a.nombre as aerolinea,
    co.nombre as origen,
    cd.nombre as destino,
    v.fecha,
    v.hora_salida,
    v.hora_llegada,
    ta.modelo as modelo_avion,
    fa.nombre as fabricante,
    v.precio_base,
    v.estado as estado_vuelo,
    COALESCE(ad_turista.asientos_disponibles, 0) as turista_disponibles,
    COALESCE(ad_ejecutiva.asientos_disponibles, 0) as ejecutiva_disponibles,
    COALESCE(ad_primera.asientos_disponibles, 0) as primera_disponibles,
    ROUND(v.precio_base * ta_ejecutiva.multiplicador_precio, 2) as precio_ejecutiva,
    ROUND(v.precio_base * ta_primera.multiplicador_precio, 2) as precio_primera
FROM Vuelos v
JOIN Aerolineas a ON v.id_aerolinea = a.id_aerolinea
JOIN Ciudades co ON v.id_ciudad_origen = co.id_ciudad
JOIN Ciudades cd ON v.id_ciudad_destino = cd.id_ciudad
JOIN TiposAvion ta ON v.id_tipo_avion = ta.id_tipo_avion
JOIN FabricantesAvion fa ON ta.id_fabricante = fa.id_fabricante
LEFT JOIN AsientosDisponibles ad_turista ON v.id_vuelo = ad_turista.id_vuelo AND ad_turista.id_tipo_asiento = 1
LEFT JOIN AsientosDisponibles ad_ejecutiva ON v.id_vuelo = ad_ejecutiva.id_vuelo AND ad_ejecutiva.id_tipo_asiento = 2
LEFT JOIN AsientosDisponibles ad_primera ON v.id_vuelo = ad_primera.id_vuelo AND ad_primera.id_tipo_asiento = 3
JOIN TiposAsiento ta_ejecutiva ON ta_ejecutiva.id_tipo_asiento = 2
JOIN TiposAsiento ta_primera ON ta_primera.id_tipo_asiento = 3
WHERE v.fecha >= CURDATE()
  AND v.estado = 'Programado'
ORDER BY v.fecha, v.hora_salida;

-- 2. VISTA: RESUMEN DE VENTAS
CREATE OR REPLACE VIEW VistaResumenVentas AS
SELECT 
    v.id_vuelo,
    v.numero_vuelo,
    v.fecha,
    COUNT(DISTINCT b.id_boleto) as boletos_vendidos,
    COUNT(DISTINCT r.id_reserva) as reservas_activas,
    SUM(CASE WHEN b.estado = 'Activo' THEN b.precio_final ELSE 0 END) as ingresos_confirmados,
    SUM(CASE WHEN r.id_estado = 1 THEN r.precio_reserva ELSE 0 END) as ingresos_pendientes,
    AVG(b.precio_final) as precio_promedio,
    MAX(v.precio_base) as precio_base_turista
FROM Vuelos v
LEFT JOIN Boletos b ON v.id_vuelo = b.id_vuelo
LEFT JOIN Reservas r ON v.id_vuelo = r.id_vuelo AND r.id_estado = 1
WHERE v.fecha >= CURDATE()
GROUP BY v.id_vuelo, v.numero_vuelo, v.fecha;

-- 3. VISTA: PASAJEROS ACTIVOS
CREATE OR REPLACE VIEW VistaPasajerosActivos AS
SELECT 
    id_pasajero,
    nombre,
    edad,
    tipo_pasajero,
    email,
    telefono,
    fecha_registro,
    (SELECT COUNT(*) FROM Boletos b WHERE b.id_pasajero = p.id_pasajero AND b.estado = 'Activo') as boletos_activos,
    (SELECT COUNT(*) FROM Reservas r WHERE r.id_pasajero = p.id_pasajero AND r.id_estado IN (1, 2)) as reservas_activas,
    (SELECT SUM(precio_final) FROM Boletos b WHERE b.id_pasajero = p.id_pasajero AND b.estado = 'Activo') as total_gastado
FROM Pasajeros p
WHERE activo = TRUE
ORDER BY fecha_registro DESC;

-- =============================================
-- VERIFICACIÓN FINAL
-- =============================================

SELECT '===============================================' as separador;
SELECT '✅ BASE DE DATOS CREADA EXITOSAMENTE' as mensaje;
SELECT '===============================================' as separador;


-- =============================================
-- INSERTAR PILOTOS
-- =============================================

INSERT INTO Pilotos (nombre, edad, experiencia_anios, id_aerolinea, licencia, activo) VALUES
('Juan Pérez Martínez', 35, 10, 1, 'PIL-MEX-001', TRUE),
('María González López', 42, 15, 2, 'PIL-MEX-002', TRUE),
('Carlos Rodríguez Sánchez', 28, 5, 3, 'PIL-MEX-003', TRUE);

-- =============================================
-- INSERTAR TIPOS DE AVIONES
-- =============================================

-- Nota: Estos tipos de avión deben referenciar fabricantes existentes.
-- Asumo que los IDs de fabricantes son: 1=Airbus, 2=Boeing, 3=Embraer
-- según los datos iniciales en tu script.

INSERT INTO TiposAvion (modelo, id_fabricante, capacidad_total, capacidad_turista, capacidad_ejecutiva, capacidad_primera_clase, anio_fabricacion) VALUES
('A320', 1, 180, 150, 20, 10, 2020),      -- Airbus A320
('737-800', 2, 189, 160, 24, 5, 2019),   -- Boeing 737-800
('E190', 3, 114, 100, 14, 0, 2021);      -- Embraer E190

-- =============================================
-- VERIFICACIÓN
-- =============================================

-- Verificar pilotos insertados
SELECT 'PILOTOS INSERTADOS:' as verificacion;
SELECT p.id_piloto, p.nombre, p.edad, p.experiencia_anios, 
       a.nombre as aerolinea, p.licencia, p.activo
FROM Pilotos p
LEFT JOIN Aerolineas a ON p.id_aerolinea = a.id_aerolinea
ORDER BY p.id_piloto;

-- Verificar tipos de avión insertados
SELECT 'TIPOS DE AVIÓN INSERTADOS:' as verificacion;
SELECT ta.id_tipo_avion, ta.modelo, fa.nombre as fabricante,
       ta.capacidad_total, ta.capacidad_turista, 
       ta.capacidad_ejecutiva, ta.capacidad_primera_clase,
       ta.anio_fabricacion
FROM TiposAvion ta
JOIN FabricantesAvion fa ON ta.id_fabricante = fa.id_fabricante
ORDER BY ta.id_tipo_avion;

use aeropuerto;
DESCRIBE Reservas;