# ApiBestarioMinecraft · API de Mobs de Minecraft (versión segura, MongoDB)

## Temática
La API administra un catálogo de **mobs (criaturas) de Minecraft**: nombre, tipo de
comportamiento, vida, daño y dimensión donde aparecen. Incluye un **simulador de combate**.
Los datos se guardan en **MongoDB** (colección `mobs`).

## Instalación y ejecución
Necesitas Python y un MongoDB (local: *MongoDB Community Server*, o en la nube: *MongoDB Atlas*).

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt

python crear_env.py             # crea .env con secretos aleatorios y MUESTRA la clave de "profe" una sola vez
python migrar_sqlite_a_mongo.py # (una vez) copia los mobs de minecraft.db a MongoDB
python main.py
```
- La API queda en `http://127.0.0.1:5000` y la interfaz en `http://127.0.0.1:5000/panel`.
- Con Atlas, pon tu cadena en `MONGO_URI` dentro de `.env`.
- Para que el docente se conecte desde otro equipo, cambia en `.env` `HOST=0.0.0.0` y reinicia;
  él usa `http://<IP-de-tu-PC>:5000`. Vuelve a `127.0.0.1` al terminar.
- En Postman, guarda en la variable `clave` la contraseña que mostró `crear_env.py`.

## Colecciones de MongoDB
| Colección | Qué guarda |
|---|---|
| `mobs` | `_id` (número 1, 2, 3…, se muestra como `id`), `nombre` (único, sin distinguir mayúsculas), `tipo`, `vida`, `dano`, `dimension` |
| `contadores` | Contador atómico para los ids numéricos |
| `usuarios` | Usuario y **hash** de su clave (nunca la clave) |
| `tokens_revocados` | Tokens cerrados con `/logout`; MongoDB los borra solo al vencer |

## Reglas de validación
- Todos los campos son obligatorios; `nombre`, `tipo`, `dimension` son texto y `vida`, `dano` enteros.
- `nombre`: máximo 40 caracteres, sin caracteres de control.
- `tipo`: pasivo, neutral, hostil o jefe. `dimension`: overworld, nether o end.
- `vida` entre 1 y 1024. `dano` entre 0 y 1000.
- **Regla propia:** un mob `pasivo` no ataca → `dano` = 0.
- **Regla propia:** un mob `hostil` siempre ataca → `dano` > 0.
- No puede haber dos mobs con el mismo nombre (ignora mayúsculas).

## Rutas
| Método | Ruta | Token | Descripción |
|---|---|---|---|
| GET | `/` | No | Bienvenida y lista de rutas |
| GET | `/panel` | No | Interfaz web |
| POST | `/login` | No | Devuelve el token JWT (`{"usuario":"profe","clave":"..."}`) |
| POST | `/logout` | Sí | Cierra la sesión e invalida el token |
| GET | `/mobs` | No | Lista mobs. Filtros: `?tipo=hostil&dimension=nether` |
| GET | `/mobs/<id>` | No | Consulta un mob |
| POST | `/mobs` | Sí | Crea un mob |
| PUT | `/mobs/<id>` | Sí | Actualiza un mob (se envían todos los campos) |
| DELETE | `/mobs/<id>` | Sí | Elimina un mob |
| POST | `/combate` | No | Simula un combate: `{"mob1": 1, "mob2": 2}` |

## Simulador de combate
Cada ronda ataca primero el `mob1` y luego el `mob2`; pierde quien llegue a 0 de vida primero.
Si ninguno puede dañar al otro (ambos con daño 0) es empate. Responde con el ganador, las rondas,
la vida restante y una bitácora (máximo 20 eventos). Errores: 400 (ids inválidos o el mismo mob
dos veces) y 404 (algún id no existe). No modifica datos, por eso no pide token.

## Códigos de respuesta
200 OK · 201 creado · 400 datos inválidos · 401 token ausente, falso, vencido o revocado
(o clave incorrecta) · 404 no encontrado · 405 método no permitido · 413 cuerpo muy grande ·
429 demasiados intentos · 503 MongoDB no disponible.

## Seguridad
Ver `AUDITORIA_SEGURIDAD.md` (hallazgos, pruebas y medidas aplicadas).

## Colaboradores

Esta lista **se actualiza sola**: muestra a todas las personas que han hecho al menos un commit
en el repositorio, con su foto de GitHub y un enlace a su perfil.

[![Colaboradores](https://contrib.rocks/image?repo=Nicky2609/ApiBestarioMinecraft)](https://github.com/Nicky2609/ApiBestarioMinecraft/graphs/contributors)

| Integrante | GitHub | Rol |
|---|---|---|
| Nicky | [@Nicky2609](https://github.com/Nicky2609) | Autor del repositorio |

> Cuando un compañero se una, se añade una fila a la tabla con su usuario de GitHub.
