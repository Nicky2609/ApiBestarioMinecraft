# API de Mobs de Minecraft

## Temática
La API administra un catálogo de **mobs (criaturas) de Minecraft**: su nombre, su tipo de
comportamiento, sus puntos de vida, el daño que hacen y la dimensión donde aparecen.
Los datos se guardan en SQLite (`minecraft.db`, se crea sola al arrancar).

## Instalación y ejecución
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
python main.py
```
La API queda en `http://127.0.0.1:5000`. Para que el docente la consuma desde otro equipo
de la misma red, usar `http://<IP-de-tu-PC>:5000` (ver la IP con `ipconfig`).

## Interfaz web
Con el servidor corriendo, abrir **`http://127.0.0.1:5000/panel`** en el navegador.
Es una página estilo Minecraft que consume la misma API con `fetch`. Desde ahí se puede:
- iniciar sesión (obtiene el token JWT)
- listar y filtrar los mobs por tipo o dimensión, y buscarlos por id
- crear, editar y eliminar mobs

Los errores de validación que devuelve la API se muestran en el formulario. Abajo hay una
*consola de peticiones* que muestra cada método, ruta, código HTTP y respuesta JSON.

## Tabla `mobs`
| Campo      | Tipo SQLite | Descripción                                   |
|------------|-------------|-----------------------------------------------|
| id         | INTEGER     | Autoincremental (clave primaria)              |
| nombre     | TEXT        | Nombre del mob, obligatorio y único           |
| tipo       | TEXT        | `pasivo`, `neutral`, `hostil` o `jefe`        |
| vida       | INTEGER     | Puntos de vida (1 a 1024)                      |
| dano       | INTEGER     | Daño de ataque (0 o más)                       |
| dimension  | TEXT        | `overworld`, `nether` o `end`                 |

## Reglas de validación
- Todos los campos son obligatorios; `nombre`, `tipo`, `dimension` deben ser texto y `vida`, `dano` números enteros.
- `tipo` solo puede ser: pasivo, neutral, hostil, jefe.
- `dimension` solo puede ser: overworld, nether, end.
- `vida` debe estar entre 1 y 1024 (límite de vida de una entidad en Minecraft).
- `dano` no puede ser negativo.
- **Regla propia:** un mob `pasivo` no ataca → su `dano` debe ser 0.
- **Regla propia:** un mob `hostil` siempre ataca → su `dano` debe ser mayor que 0.
- No puede haber dos mobs con el mismo nombre.

## Rutas
| Método | Ruta          | Token | Descripción                                           |
|--------|---------------|-------|-------------------------------------------------------|
| GET    | `/`           | No    | Bienvenida y lista de rutas (JSON)                    |
| GET    | `/panel`      | No    | Interfaz web que consume la API                       |
| POST   | `/login`      | No    | Devuelve el token JWT (`{"usuario":"profe","clave":"cloud2026"}`) |
| GET    | `/mobs`       | No    | Lista todos los mobs. Filtros opcionales: `?tipo=hostil&dimension=nether` |
| GET    | `/mobs/<id>`  | No    | Consulta un mob por id                                |
| POST   | `/mobs`       | Sí    | Crea un mob                                           |
| PUT    | `/mobs/<id>`  | Sí    | Actualiza un mob (se envían todos los campos)         |
| DELETE | `/mobs/<id>`  | Sí    | Elimina un mob                                        |

El token se envía en el encabezado: `Authorization: Bearer <token>` (dura 1 hora).

### Ejemplo de cuerpo (POST / PUT)
```json
{ "nombre": "Creeper", "tipo": "hostil", "vida": 20, "dano": 49, "dimension": "overworld" }
```

## Códigos de respuesta
| Código | Cuándo                                                        |
|--------|---------------------------------------------------------------|
| 200    | Consulta, actualización o eliminación correcta                |
| 201    | Mob creado                                                    |
| 400    | Datos inválidos (incluye la lista `detalles` con cada error)  |
| 401    | Token ausente, inválido o expirado / login incorrecto         |
| 404    | El mob con ese id no existe                                   |

## Pruebas en Postman
Importar `Minecraft_Mobs.postman_collection.json`. Ejecutar primero **Login** (guarda el token
automáticamente en la variable `token`) y luego el resto en orden: crear 2 mobs, listar,
consultar, actualizar uno, eliminar otro, listar de nuevo (el otro permanece) y las 3 pruebas
de error. Para comprobar la persistencia: detener el servidor (Ctrl+C), volver a ejecutar
`python main.py` y hacer **Listar mobs**: los datos siguen ahí porque están en `minecraft.db`.
