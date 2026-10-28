# Arcana — API

> *Donde cada tirada se convierte en leyenda.*

**Arcana** es una tienda de juegos de mesa y de rol que además es punto de encuentro de su comunidad. Vende juegos, manuales y accesorios, y organiza en su local torneos, partidas de rol y noches de juegos. Cada evento deja su **tabla de ganadores** y sus **leyendas**: crónicas de lo que pasó en la mesa, que forman el salón de la fama de la tienda.

Este repositorio contiene la **API REST** de Arcana, construida con Django y Django REST Framework, que consume el frontend [`boardgame-roleplay-hub-web`](https://github.com/ValenBelone7/boardgame-roleplay-hub-web).

> Evaluación Final Integradora 2026 — Ingeniería de Software (ITEC).

## Índice

- [Objetivo](#objetivo)
- [Capturas](#capturas)
- [Stack](#stack)
- [Planificación de la base de datos](#planificación-de-la-base-de-datos)
- [Instalación con uv](#instalación-con-uv)
- [Instalación con Docker](#instalación-con-docker)
- [Datos de ejemplo](#datos-de-ejemplo)
- [Variables de entorno](#variables-de-entorno)
- [Rutas generales](#rutas-generales)
- [Autenticación](#autenticación)
- [Endpoints](#endpoints)
- [Tests](#tests)
- [Flujo de trabajo con Git](#flujo-de-trabajo-con-git)
- [Equipo](#equipo)

## Objetivo

Exponer, a través de una API REST, todo lo que necesita la tienda y su comunidad:

- **Catálogo**: juegos de mesa, juegos de rol, expansiones y accesorios, con sus categorías, editoriales, diseñadores y mecánicas, y las reseñas de los jugadores.
- **Ventas**: pedidos de los usuarios con control de stock.
- **Eventos**: torneos y partidas de rol con inscripción y cupo, la tabla de ganadores de cada evento, un salón de la fama y las leyendas que escribe la comunidad.

## Capturas

Tomadas con los [datos de ejemplo](#datos-de-ejemplo) cargados.

### Página de bienvenida

Vista principal que renderiza un template con un resumen de la tienda: productos, próximos eventos y la leyenda destacada.

![Página de bienvenida de Arcana](docs/capturas/01-bienvenida.png)

### Documentación de la API

Swagger generado con drf-spectacular. Se obtiene un token JWT con un usuario de demo y se carga con el botón **Authorize**.

![Swagger](docs/capturas/02-swagger.png)

![Token JWT obtenido desde Swagger](docs/capturas/03-swagger-token.png)

![Token cargado en Authorize](docs/capturas/04-swagger-authorize.png)

Redoc, con la misma documentación:

![Redoc](docs/capturas/05-redoc.png)

### API navegable: anidado en el listado, plano en el detalle

En el listado (`GET /api/productos/`) las relaciones vienen anidadas y paginadas:

![Listado de productos con relaciones anidadas](docs/capturas/06-list-anidado.png)

En el detalle (`GET /api/productos/9/`) el mismo producto trae las relaciones como ids:

![Detalle de producto con relaciones como ids](docs/capturas/07-retrieve-plano.png)

### Filtros, búsqueda y orden

`/api/productos/?categoria=1&precio__lte=100000&ordering=-precio`: juegos de estrategia de hasta $100.000, del más caro al más barato.

![Productos filtrados y ordenados](docs/capturas/08-filtros.png)

![Panel de filtros de la API navegable](docs/capturas/08b-filtros-panel.png)

### Comunidad: podio y salón de la fama

![Podio de la Copa Arcana de Primavera](docs/capturas/09-podio.png)

![Salón de la fama](docs/capturas/10-salon-de-la-fama.png)

### Ventas: confirmar un pedido

`POST /api/pedidos/4/confirmar/` como `lucia`: controla el stock, lo descuenta y calcula el total.

![Pedido confirmado desde Swagger](docs/capturas/11-confirmar-pedido.png)

### Panel de administración

Productos con filtros, búsqueda y edición en la lista:

![Admin de productos](docs/capturas/12-admin-productos.png)

Pedido con sus ítems y evento con inscripciones y resultados, editables en la misma página:

![Admin de un pedido con ítems](docs/capturas/13-admin-pedido.png)

![Admin de un evento con inscripciones y resultados](docs/capturas/14-admin-evento.png)

### Docker y tests

![Proyecto levantado con Docker Compose](docs/capturas/15-docker.png)

![Tests en verde](docs/capturas/16-tests.png)

## Stack

| Herramienta | Uso |
|---|---|
| Python 3.12 + [uv](https://docs.astral.sh/uv/) | Lenguaje y gestor de entorno y dependencias |
| Django 6.1 | Framework web, ORM y panel de administración |
| Django REST Framework | API REST, ViewSets, serializers, paginación, API navegable |
| djangorestframework-simplejwt | Autenticación por token (JWT) |
| drf-spectacular | Esquema OpenAPI, Swagger y Redoc |
| django-filter | Filtros en los endpoints |
| django-cors-headers | CORS para el frontend |
| python-dotenv | Variables de entorno desde `.env` |
| SQLite | Base de datos |
| Docker + Docker Compose | Contenedor del proyecto |

## Planificación de la base de datos

Antes de desarrollar se planificaron 13 modelos repartidos en 4 apps:

| App | Modelos |
|---|---|
| `usuarios` | Usuario |
| `catalogo` | Categoria, Editorial, Disenador, Mecanica, Producto, Resena |
| `ventas` | Pedido, ItemPedido |
| `eventos` | Evento, Inscripcion, Resultado, Leyenda |

### Diagrama entidad-relación

```mermaid
erDiagram
    USUARIO ||--o{ RESENA : escribe
    USUARIO ||--o{ PEDIDO : realiza
    USUARIO ||--o{ EVENTO : organiza
    USUARIO ||--o{ INSCRIPCION : "se inscribe"
    USUARIO ||--o{ RESULTADO : obtiene
    USUARIO ||--o{ LEYENDA : escribe
    USUARIO |o--o{ LEYENDA : protagoniza

    CATEGORIA ||--o{ PRODUCTO : agrupa
    EDITORIAL |o--o{ PRODUCTO : publica
    PRODUCTO }o--o{ MECANICA : usa
    PRODUCTO }o--o{ DISENADOR : "diseñado por"
    PRODUCTO |o--o{ PRODUCTO : "expansión de"
    PRODUCTO ||--o{ RESENA : recibe

    PEDIDO ||--|{ ITEM_PEDIDO : contiene
    PRODUCTO ||--o{ ITEM_PEDIDO : "se vende en"

    PRODUCTO |o--o{ EVENTO : "se juega en"
    EVENTO ||--o{ INSCRIPCION : tiene
    EVENTO ||--o{ RESULTADO : "tabla de ganadores"
    EVENTO ||--o{ LEYENDA : inspira

    USUARIO {
        int id PK
        string username
        string alias
        date fecha_nacimiento
        bool is_staff
    }
    CATEGORIA {
        int id PK
        string nombre UK
        text descripcion
    }
    EDITORIAL {
        int id PK
        string nombre UK
        string pais
        string sitio_web
    }
    DISENADOR {
        int id PK
        string nombre
        string nacionalidad
    }
    MECANICA {
        int id PK
        string nombre UK
        text descripcion
    }
    PRODUCTO {
        int id PK
        string nombre
        string tipo "JUEGO_MESA, JUEGO_ROL, EXPANSION, ACCESORIO"
        decimal precio
        int stock
        int jugadores_min
        int jugadores_max
        int duracion_minutos
        int edad_minima
        string imagen_url
        bool activo
        datetime fecha_alta
        int categoria_id FK
        int editorial_id FK
        int juego_base_id FK
    }
    RESENA {
        int id PK
        int producto_id FK
        int usuario_id FK
        int puntaje "1 a 5"
        text comentario
        datetime fecha
    }
    PEDIDO {
        int id PK
        int usuario_id FK
        string estado "PENDIENTE, CONFIRMADO, CANCELADO"
        decimal total
        datetime fecha
        datetime fecha_confirmacion
    }
    ITEM_PEDIDO {
        int id PK
        int pedido_id FK
        int producto_id FK
        int cantidad
        decimal precio_unitario
    }
    EVENTO {
        int id PK
        string nombre
        string tipo "TORNEO, PARTIDA_ROL, CAMPANA_ROL, NOCHE_JUEGOS"
        int juego_id FK
        int organizador_id FK
        datetime fecha
        int cupo
        decimal costo_inscripcion
        string estado "PROGRAMADO, EN_CURSO, FINALIZADO, CANCELADO"
    }
    INSCRIPCION {
        int id PK
        int evento_id FK
        int usuario_id FK
        string personaje
        datetime fecha
    }
    RESULTADO {
        int id PK
        int evento_id FK
        int usuario_id FK
        int posicion "1 = campeón"
        int puntos
    }
    LEYENDA {
        int id PK
        int evento_id FK
        int autor_id FK
        int protagonista_id FK
        string titulo
        text relato
        bool destacada
        datetime fecha
    }
```

### Relaciones

| Relación | Tipo | Detalle |
|---|---|---|
| Categoria → Producto | 1 a N | Cada producto pertenece a una categoría (`PROTECT`: no se borra una categoría con productos) |
| Editorial → Producto | 1 a N | Opcional (los accesorios pueden no tener editorial) |
| Producto ↔ Mecanica | N a M | Un juego combina varias mecánicas |
| Producto ↔ Disenador | N a M | Un juego puede tener varios diseñadores |
| Producto → Producto | 1 a N (auto-relación) | `juego_base`: una expansión apunta a su juego base |
| Producto / Usuario → Resena | 1 a N | Una sola reseña por usuario y por producto |
| Usuario → Pedido → ItemPedido | 1 a N | El ítem guarda el `precio_unitario` del momento de la compra |
| Producto → Evento | 1 a N | Juego que se juega en el evento (opcional) |
| Usuario → Evento | 1 a N | Organizador del evento |
| Evento / Usuario → Inscripcion | 1 a N | Un usuario se inscribe una sola vez por evento; en rol puede indicar su personaje |
| Evento / Usuario → Resultado | 1 a N | Tabla de ganadores: un puesto por usuario y un usuario por puesto en cada evento |
| Evento / Usuario → Leyenda | 1 a N | Crónica con autor y, opcionalmente, un protagonista |

## Instalación con uv

Requisitos: [uv](https://docs.astral.sh/uv/getting-started/installation/) instalado.

```bash
git clone git@github.com:ValenBelone7/boardgame-roleplay-hub-django.git
cd boardgame-roleplay-hub-django

# Variables de entorno
cp .env.example .env          # completar SECRET_KEY

# Dependencias (crea el entorno virtual .venv)
uv sync

# Base de datos y superusuario
cd src
uv run manage.py migrate
uv run manage.py loaddata usuarios catalogo ventas eventos   # datos de ejemplo (opcional)
uv run manage.py createsuperuser                              # o usar arcana_admin

# Servidor de desarrollo
uv run manage.py runserver
```

La API queda disponible en `http://127.0.0.1:8000/`.

## Instalación con Docker

Requisitos: Docker y Docker Compose.

```bash
cp .env.example .env          # completar SECRET_KEY
docker compose up --build
```

Las migraciones se aplican solas al iniciar el contenedor. En otra terminal:

```bash
docker compose exec web uv run --no-sync manage.py loaddata usuarios catalogo ventas eventos
docker compose exec web uv run --no-sync manage.py createsuperuser   # opcional
```

La base SQLite se guarda en el volumen `arcana-data`, así que los datos se conservan entre `docker compose down` y `docker compose up`. Para empezar de cero: `docker compose down -v`.

## Datos de ejemplo

El repositorio incluye fixtures con datos de Arcana para probar la API sin cargar nada a mano:

| Fixture | Contenido |
|---|---|
| `usuarios` | 1 administrador y 4 jugadores con alias |
| `catalogo` | 6 categorías, 6 editoriales, 13 diseñadores, 10 mecánicas, 21 productos (juegos de mesa, de rol, 3 expansiones y accesorios, uno dado de baja) y 13 reseñas |
| `ventas` | 4 pedidos: confirmados, cancelado y uno pendiente (carrito) |
| `eventos` | 7 eventos (3 finalizados con podio, 1 campaña de rol en curso y 3 programados), 21 inscripciones, 10 resultados y 5 leyendas |

```bash
cd src
uv run manage.py loaddata usuarios catalogo ventas eventos
```

Los fixtures usan ids fijos: se cargan sobre una base recién migrada. Para volver a empezar,
borrar `src/db.sqlite3` (o `docker compose down -v`) y repetir `migrate` + `loaddata`.

### Usuarios de demo

Todos tienen la contraseña **`arcana2026`**.

| Usuario | Alias | Rol |
|---|---|---|
| `arcana_admin` | Arcana | Staff y superusuario: admin y escritura del catálogo y los eventos |
| `lucia` | Lu la Estratega | Jugadora: 2 títulos, tiene un pedido pendiente |
| `mateo` | Mateo Dados | Jugador |
| `sofia` | Sofi Runas | Jugadora |
| `nicolas` | Nico el Bardo | Jugador |

Las portadas de los productos (`imagen_url`) apuntan a imágenes de Wikipedia y Wikimedia Commons.

## Variables de entorno

| Variable | Ejemplo | Descripción |
|---|---|---|
| `SECRET_KEY` | `"una-clave-larga"` | Clave secreta de Django |
| `DEBUG` | `True` | Modo debug |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,0.0.0.0` | Hosts permitidos, separados por coma |
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Orígenes del frontend habilitados por CORS, separados por coma |
| `SQLITE_PATH` | `/app/data/db.sqlite3` | Opcional. Ruta de la base; por defecto `src/db.sqlite3` (Docker la define sola) |

## Rutas generales

| Ruta | Descripción |
|---|---|
| `/` | Página de bienvenida |
| `/api/` | Raíz de la API navegable |
| `/api/token/` · `/api/token/refresh/` | Obtener y renovar el token JWT |
| `/api/schema/` | Esquema OpenAPI |
| `/api/schema/swagger/` | Documentación Swagger |
| `/api/schema/redoc/` | Documentación Redoc |
| `/api-auth/login/` | Login por sesión de la API navegable |
| `/admin/` | Panel de administración |

## Autenticación

La API acepta dos tipos de autenticación:

| Tipo | Para qué | Cómo |
|---|---|---|
| **JWT** (simplejwt) | Frontend, Swagger y clientes externos | `POST /api/token/` con `username` y `password` devuelve un `access` (dura 2 horas) y un `refresh` (10 días). El `access` se envía en el header `Authorization: Bearer <access>`. Para renovarlo: `POST /api/token/refresh/` con el `refresh` |
| **Sesión** | API navegable y panel de administración | Botón **Log in** de la API navegable (`/api-auth/login/`) o login del `/admin/` |

En Swagger: ejecutar `POST /api/token/`, copiar el `access` y pegarlo en **Authorize**.

```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "lucia", "password": "arcana2026"}'

curl http://127.0.0.1:8000/api/usuarios/me/ -H "Authorization: Bearer <access>"
```

### Permisos

| Quién | Puede |
|---|---|
| Anónimo | Ver el catálogo, los eventos, los resultados y las leyendas; registrarse |
| Usuario logueado | Lo anterior, más armar y confirmar sus pedidos, inscribirse a eventos y escribir reseñas y leyendas (y editar solo las suyas) |
| Staff | Todo: catálogo, eventos y resultados, todos los pedidos y los emails de los usuarios |

Respuestas de error: **401** si falta el token o es inválido, **403** si el usuario no tiene permiso para esa acción y **404** si pide un pedido que no es suyo.

## Endpoints

Todos bajo `/api/`. Los listados están paginados de a 10 (`count`, `next`, `previous` y `results`; la página se elige con `?page=2`). En los recursos con anidados, el **listado** trae las relaciones como objetos y el **detalle** (`/{id}/`) las trae como ids, que es el formato que se usa para escribir.

| Recurso | Métodos | Permisos | Anidado en el listado | Filtros · búsqueda · orden |
|---|---|---|---|---|
| `usuarios/` | GET | Logueado (los emails solo los ve el staff) | — | `search`: username, alias |
| `categorias/` · `editoriales/` · `disenadores/` · `mecanicas/` | CRUD | Staff escribe, todos leen | — | `search`: nombre |
| `productos/` | CRUD | Staff escribe, todos leen | categoría, editorial, mecánicas, diseñadores, juego base | `categoria`, `editorial`, `tipo`, `activo`, `mecanicas`, `precio` (`__gt`, `__lt`, `__gte`, `__lte`), `jugadores_min__lte`, `jugadores_max__gte` · `search`: nombre, editorial, diseñador, mecánica · `ordering`: precio, nombre, fecha_alta |
| `resenas/` | CRUD | Logueado escribe; solo el autor edita la suya | usuario, producto | `producto`, `usuario`, `puntaje` · `ordering`: fecha, puntaje |
| `pedidos/` | GET, POST | Logueado; cada uno ve los suyos (el staff, todos) | usuario, ítems con su producto | `estado` · `ordering`: fecha, total |
| `items-pedido/` | CRUD | Logueado; solo en su pedido pendiente | producto (+ subtotal) | `pedido` |
| `eventos/` | CRUD | Staff escribe, todos leen | juego, organizador (+ cantidad de inscriptos) | `tipo`, `estado`, `juego`, `fecha__gte`, `fecha__lte` · `search`: nombre, juego · `ordering`: fecha, costo_inscripcion |
| `inscripciones/` | GET, DELETE | Logueado; cada uno se da de baja de la suya mientras el evento esté programado | — | `evento`, `usuario` |
| `resultados/` | CRUD | Staff escribe, todos leen | evento, usuario | `evento`, `usuario`, `posicion` · `ordering`: posicion, puntos |
| `leyendas/` | CRUD | Logueado escribe; solo el autor edita la suya | evento, autor, protagonista | `evento`, `destacada`, `autor`, `protagonista` · `search`: titulo, relato · `ordering`: fecha |

### Acciones personalizadas (`@action`)

| Ruta | Método | Qué hace |
|---|---|---|
| `usuarios/registro/` | POST | Crea una cuenta (abierto a todos) |
| `usuarios/me/` | GET | Datos del usuario logueado |
| `productos/{id}/borrado_logico/` | DELETE | Da de baja el producto (`activo = false`) sin borrarlo. Solo staff |
| `productos/{id}/resenas/` | GET | Reseñas del producto, paginadas |
| `pedidos/{id}/confirmar/` | POST | Controla el stock, lo descuenta y calcula el total; si algo falla no descuenta nada |
| `pedidos/{id}/cancelar/` | POST | Cancela el pedido y repone el stock si estaba confirmado |
| `eventos/{id}/inscribirse/` | POST | Inscribe al usuario logueado si el evento está programado y tiene cupo. `personaje` es opcional |
| `eventos/{id}/podio/` | GET | Resultados del evento ordenados por posición |
| `resultados/salon_de_la_fama/` | GET | Ranking de jugadores por títulos y puntos, paginado |

### Flujo de compra

1. `POST /api/pedidos/` (sin body): crea el carrito. Cada usuario tiene un solo pedido pendiente.
2. `POST /api/items-pedido/` con `{"pedido": 4, "producto": 1, "cantidad": 2}`: el precio se copia del catálogo en ese momento. Con `PATCH` se cambia la cantidad y con `DELETE` se quita el ítem.
3. `POST /api/pedidos/4/confirmar/`: descuenta el stock y calcula el total.

## Tests

78 tests con `APITestCase` que cubren permisos, anidados, filtros, acciones y reglas de negocio.

```bash
cd src
uv run manage.py test
```

| App | Tests | Qué cubren |
|---|---|---|
| `usuarios` | 10 | Registro, contraseña hasheada, login con JWT y con sesión, `me`, privacidad de los emails |
| `catalogo` | 23 | Listado anidado y detalle plano, respuestas 401/403/201, filtros, búsqueda, orden, borrado lógico y reseñas |
| `ventas` | 19 | Pedidos privados, carrito único, `confirmar` y `cancelar` con control de stock, reglas de los ítems |
| `eventos` | 26 | Inscripción (cupo, duplicado, estado), bajas, podio, salón de la fama, resultados y leyendas |

Al correr los tests se usa un hasher de contraseñas rápido, así la suite tarda unos 2 segundos.

## Flujo de trabajo con Git

- **Ramas:** `main` guarda solo las versiones entregables y `develop` integra el trabajo. Cada tarea se hace en una rama corta (`feat/`, `fix/`, `docs/`, `test/`, `build/`, `chore/`) que sale de `develop` y vuelve por pull request.
- **Pull requests:** el otro integrante revisa, y se mergea con *merge commit* para conservar los commits de cada rama.
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/es/), en castellano e imperativo. Por ejemplo:
  - `feat(ventas): agrega viewsets de pedidos e items con confirmar y cancelar`
  - `fix(eventos): valida inscripcion en resultados y evento jugado en leyendas`
  - `test(catalogo): cubre productos, filtros, permisos, borrado logico y resenas`
- **Versiones:** `v1.0.0` es la entrega final, mergeada de `develop` a `main`.

| PR | Rama | Qué entregó |
|---|---|---|
| [#1](https://github.com/ValenBelone7/boardgame-roleplay-hub-django/pull/1) | `chore/bootstrap-proyecto` | Proyecto con uv, configuración de DRF, JWT, CORS y documentación, usuario personalizado |
| [#2](https://github.com/ValenBelone7/boardgame-roleplay-hub-django/pull/2) | `feat/modelos-y-admin` | Los 13 modelos y el panel de administración |
| [#3](https://github.com/ValenBelone7/boardgame-roleplay-hub-django/pull/3) | `build/docker` | Dockerfile y Compose con uv |
| [#4](https://github.com/ValenBelone7/boardgame-roleplay-hub-django/pull/4) | `feat/vista-bienvenida` | Página de bienvenida |
| [#5](https://github.com/ValenBelone7/boardgame-roleplay-hub-django/pull/5) | `docs/readme-der` | Planificación de la base de datos (DER) e instalación |
| [#6](https://github.com/ValenBelone7/boardgame-roleplay-hub-django/pull/6) | `feat/serializers` | Serializers planos y anidados de todas las apps |
| [#7](https://github.com/ValenBelone7/boardgame-roleplay-hub-django/pull/7) | `feat/api-catalogo-usuarios` | API del catálogo y de usuarios |
| [#8](https://github.com/ValenBelone7/boardgame-roleplay-hub-django/pull/8) | `feat/api-ventas-eventos` | API de ventas y eventos |
| [#9](https://github.com/ValenBelone7/boardgame-roleplay-hub-django/pull/9) | `feat/fixtures` | Datos de ejemplo |
| [#10](https://github.com/ValenBelone7/boardgame-roleplay-hub-django/pull/10) | `test/api` | Tests de la API |
| [#11](https://github.com/ValenBelone7/boardgame-roleplay-hub-django/pull/11) | `fix/eventos-reglas` | Reglas de resultados, leyendas y organizador |
| [#12](https://github.com/ValenBelone7/boardgame-roleplay-hub-django/pull/12) | `chore/version-1.0.0` | Versión 1.0.0 y CORS para `127.0.0.1:3000` |
| [#13](https://github.com/ValenBelone7/boardgame-roleplay-hub-django/pull/13) | `fix/redoc-version` | Versiones fijas de Swagger UI y Redoc |
| [#14](https://github.com/ValenBelone7/boardgame-roleplay-hub-django/pull/14) | `docs/readme-final` | README final con capturas |

## Equipo

| Integrante | GitHub | Participación |
|---|---|---|
| Valentín Belone | [`ValenBelone7`](https://github.com/ValenBelone7) | Bootstrap, modelos y admin, Docker, bienvenida, README, datos de ejemplo, tests y cierre |
| Tiago Pescara | [`Tiagooo10`](https://github.com/Tiagooo10) | Serializers y API de catálogo, usuarios, ventas y eventos |
