"""
API de Mobs de Minecraft
Administra un catalogo de criaturas (mobs) de Minecraft: su tipo de
comportamiento, puntos de vida, dano de ataque y la dimension donde aparecen.
"""
from flask import Flask, jsonify, request, send_from_directory
import sqlite3
import jwt, datetime
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave-secreta-creeper'
app.json.ensure_ascii = False
USUARIOS = {'profe': 'cloud2026'}

DB_NAME = 'minecraft.db'

TIPOS_PERMITIDOS = ['pasivo', 'neutral', 'hostil', 'jefe']
DIMENSIONES_PERMITIDAS = ['overworld', 'nether', 'end']
VIDA_MAXIMA = 1024  # limite de vida de una entidad en Minecraft


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS mobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        tipo TEXT NOT NULL,
        vida INTEGER NOT NULL,
        dano INTEGER NOT NULL,
        dimension TEXT NOT NULL)''')
    conn.commit()
    conn.close()


def validar_mob(data):
    """Devuelve una lista de errores. Si esta vacia, el mob es valido."""
    if not isinstance(data, dict):
        return ['El cuerpo de la peticion debe ser un JSON valido']

    errores = []
    nombre = data.get('nombre')
    tipo = data.get('tipo')
    vida = data.get('vida')
    dano = data.get('dano')
    dimension = data.get('dimension')

    # Campos obligatorios y tipos de datos
    if not isinstance(nombre, str) or not nombre.strip():
        errores.append("'nombre' es obligatorio y debe ser texto")
    if not isinstance(tipo, str):
        errores.append("'tipo' es obligatorio y debe ser texto")
    if not isinstance(vida, int) or isinstance(vida, bool):
        errores.append("'vida' es obligatoria y debe ser un numero entero")
    if not isinstance(dano, int) or isinstance(dano, bool):
        errores.append("'dano' es obligatorio y debe ser un numero entero")
    if not isinstance(dimension, str):
        errores.append("'dimension' es obligatoria y debe ser texto")
    if errores:
        return errores

    # Reglas propias de Minecraft
    if tipo.lower() not in TIPOS_PERMITIDOS:
        errores.append(f"'tipo' debe ser uno de: {', '.join(TIPOS_PERMITIDOS)}")
    if dimension.lower() not in DIMENSIONES_PERMITIDAS:
        errores.append(f"'dimension' debe ser una de: {', '.join(DIMENSIONES_PERMITIDAS)}")
    if vida <= 0 or vida > VIDA_MAXIMA:
        errores.append(f"'vida' debe estar entre 1 y {VIDA_MAXIMA}")
    if dano < 0:
        errores.append("'dano' no puede ser negativo")
    if tipo.lower() == 'pasivo' and dano != 0:
        errores.append("Un mob 'pasivo' no ataca, su 'dano' debe ser 0")
    if tipo.lower() == 'hostil' and dano == 0:
        errores.append("Un mob 'hostil' debe tener 'dano' mayor que 0")
    return errores


init_db()  # crea la tabla al arrancar (con python main.py o con flask run)


def limpiar_mob(data):
    return (data['nombre'].strip(), data['tipo'].lower(), data['vida'],
            data['dano'], data['dimension'].lower())


def token_required(f):
    @wraps(f)
    def decorador(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token no proporcionado'}), 401
        try:
            jwt.decode(token.replace('Bearer ', ''), app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except Exception:
            return jsonify({'error': 'Token invalido'}), 401
        return f(*args, **kwargs)
    return decorador


@app.route('/')
def bienvenida():
    return jsonify({
        'mensaje': 'Bienvenido a la API de Mobs de Minecraft',
        'interfaz': 'Abrir /panel en el navegador',
        'rutas': {
            'POST /login': 'Obtener token (usuario, clave)',
            'GET /mobs': 'Listar mobs (filtros opcionales ?tipo=&dimension=)',
            'GET /mobs/<id>': 'Consultar un mob',
            'POST /mobs': 'Crear mob (requiere token)',
            'PUT /mobs/<id>': 'Actualizar mob (requiere token)',
            'DELETE /mobs/<id>': 'Eliminar mob (requiere token)'
        }
    })


@app.route('/panel')
def panel():
    # Interfaz web que consume esta misma API
    return send_from_directory('static', 'index.html')


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    if data.get('usuario') in USUARIOS and USUARIOS[data['usuario']] == data.get('clave'):
        token = jwt.encode({
            'usuario': data['usuario'],
            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token}), 200
    return jsonify({'error': 'Usuario o clave incorrectos'}), 401


@app.route('/mobs', methods=['GET'])
def listar_mobs():
    consulta = 'SELECT * FROM mobs WHERE 1=1'
    parametros = []
    tipo = request.args.get('tipo')
    dimension = request.args.get('dimension')
    if tipo:
        consulta += ' AND tipo = ?'
        parametros.append(tipo.lower())
    if dimension:
        consulta += ' AND dimension = ?'
        parametros.append(dimension.lower())

    conn = get_db()
    filas = conn.execute(consulta, parametros).fetchall()
    conn.close()
    return jsonify([dict(fila) for fila in filas]), 200


@app.route('/mobs/<int:mob_id>', methods=['GET'])
def obtener_mob(mob_id):
    conn = get_db()
    fila = conn.execute('SELECT * FROM mobs WHERE id = ?', (mob_id,)).fetchone()
    conn.close()
    if fila is None:
        return jsonify({'error': f'Mob con id {mob_id} no encontrado'}), 404
    return jsonify(dict(fila)), 200


@app.route('/mobs', methods=['POST'])
@token_required
def crear_mob():
    data = request.get_json(silent=True)
    errores = validar_mob(data)
    if errores:
        return jsonify({'error': 'Datos invalidos', 'detalles': errores}), 400

    conn = get_db()
    try:
        cur = conn.execute(
            'INSERT INTO mobs (nombre, tipo, vida, dano, dimension) VALUES (?, ?, ?, ?, ?)',
            limpiar_mob(data)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Datos invalidos', 'detalles': [f"Ya existe un mob llamado '{data['nombre'].strip()}'"]}), 400
    mob = dict(conn.execute('SELECT * FROM mobs WHERE id = ?', (cur.lastrowid,)).fetchone())
    conn.close()
    return jsonify({'mensaje': 'Mob creado', 'mob': mob}), 201


@app.route('/mobs/<int:mob_id>', methods=['PUT'])
@token_required
def actualizar_mob(mob_id):
    data = request.get_json(silent=True)
    errores = validar_mob(data)
    if errores:
        return jsonify({'error': 'Datos invalidos', 'detalles': errores}), 400

    conn = get_db()
    try:
        cur = conn.execute(
            'UPDATE mobs SET nombre = ?, tipo = ?, vida = ?, dano = ?, dimension = ? WHERE id = ?',
            (*limpiar_mob(data), mob_id)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Datos invalidos', 'detalles': [f"Ya existe otro mob llamado '{data['nombre'].strip()}'"]}), 400

    if cur.rowcount == 0:
        conn.close()
        return jsonify({'error': f'Mob con id {mob_id} no encontrado'}), 404
    mob = dict(conn.execute('SELECT * FROM mobs WHERE id = ?', (mob_id,)).fetchone())
    conn.close()
    return jsonify({'mensaje': 'Mob actualizado', 'mob': mob}), 200


@app.route('/mobs/<int:mob_id>', methods=['DELETE'])
@token_required
def eliminar_mob(mob_id):
    conn = get_db()
    cur = conn.execute('DELETE FROM mobs WHERE id = ?', (mob_id,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        return jsonify({'error': f'Mob con id {mob_id} no encontrado'}), 404
    return jsonify({'mensaje': 'Mob eliminado', 'id': mob_id}), 200


@app.errorhandler(404)
def ruta_no_encontrada(e):
    return jsonify({'error': 'Ruta no encontrada'}), 404


@app.errorhandler(405)
def metodo_no_permitido(e):
    return jsonify({'error': 'Metodo HTTP no permitido en esta ruta'}), 405


if __name__ == '__main__':
    # host 0.0.0.0 permite que otros equipos de la red (el docente) consuman la API
    app.run(host='0.0.0.0', port=5000, debug=True)
