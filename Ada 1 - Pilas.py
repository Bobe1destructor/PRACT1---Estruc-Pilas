"""
ADA1 - Pilas (Unidad 3 - Estructuras Lineales)  |  Interfaz web (HTML) + lógica en Python

TODA la lógica está en Python:
  - Clase Pila
  - Evaluación de expresiones posfija / prefija usando una pila
  - Torres de Hanoi (3 a 8 discos) usando la clase Pila, con modo manual y automático

El HTML/CSS/JS de este archivo solo se encarga de MOSTRAR la interfaz (con transiciones
y animaciones) y de pedirle a Python los resultados. Python levanta un pequeño servidor
local con la biblioteca estándar (http.server), así que no hay que instalar nada.

Uso:
    python ada1_pilas_web.py                 (abre el navegador automáticamente)
    python ada1_pilas_web.py --puerto 9000   (usar otro puerto)
    python ada1_pilas_web.py --no-navegador  (no abrir el navegador)

Para cerrar el programa: Ctrl + C en la terminal.
"""

import argparse
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


# ===========================================================================
# CLASE PILA (estructura LIFO: el último en entrar es el primero en salir)
# ===========================================================================
class Pila:
    def __init__(self):
        self._items = []

    def push(self, elemento):
        """Inserta un elemento en la cima de la pila."""
        self._items.append(elemento)

    def pop(self):
        """Elimina y devuelve el elemento de la cima."""
        if self.esta_vacia():
            raise IndexError("La pila está vacía (subdesbordamiento)")
        return self._items.pop()

    def peek(self):
        """Devuelve el elemento de la cima sin eliminarlo."""
        if self.esta_vacia():
            raise IndexError("La pila está vacía")
        return self._items[-1]

    def esta_vacia(self):
        return len(self._items) == 0

    def tamano(self):
        return len(self._items)

    def elementos(self):
        """Copia de los elementos, de la base a la cima."""
        return list(self._items)

    def __str__(self):
        return str(self._items)


# ===========================================================================
# LÓGICA 1: EVALUADOR DE EXPRESIONES POSFIJA / PREFIJA
# ===========================================================================
OPERADORES = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": lambda a, b: a / b,
    "^": lambda a, b: a ** b,
}


def es_numero(token):
    try:
        float(token)
        return True
    except ValueError:
        return False


def formatear(numero):
    """Muestra 14.0 como 14 y deja los decimales cuando existen."""
    return str(int(numero)) if numero == int(numero) else str(round(numero, 6))


def aplicar(operador, a, b):
    """Aplica 'a operador b' controlando división entre cero y desbordes."""
    try:
        return OPERADORES[operador](a, b)
    except ZeroDivisionError:
        raise ValueError("División entre cero")
    except OverflowError:
        raise ValueError("El resultado es demasiado grande")


def registrar(pasos, accion, pila, indice, detalle):
    """Guarda en la traza: la acción, el token leído, una explicación y cómo quedó la pila."""
    if pasos is not None:
        pasos.append({"accion": accion, "indice": indice, "detalle": detalle,
                      "pila": [formatear(x) for x in pila.elementos()]})


def procesar_token(token, indice, pila, pasos, prefija):
    """
    Un paso del algoritmo (igual para ambas notaciones):
      - número   -> push
      - operador -> pop de dos operandos, se calcula y el resultado se mete (push).
    Solo cambia el orden de los pop: en posfija el primer pop es el operando derecho (b);
    en prefija el primer pop es el izquierdo (a).
    """
    nombre = "prefija" if prefija else "posfija"
    if es_numero(token):
        pila.push(float(token))
        registrar(pasos, f"push {formatear(float(token))}", pila, indice,
                  f"Se lee {token}: es un número, entra a la pila (push).")
    elif token in OPERADORES:
        if pila.tamano() < 2:
            raise ValueError(f"Expresión {nombre} inválida: faltan operandos")
        if prefija:
            a = pila.pop()
            b = pila.pop()
            sacados = f"{formatear(a)} y {formatear(b)}"
        else:
            b = pila.pop()
            a = pila.pop()
            sacados = f"{formatear(b)} y {formatear(a)}"
        r = aplicar(token, a, b)
        pila.push(r)
        operacion = f"{formatear(a)} {token} {formatear(b)} = {formatear(r)}"
        registrar(pasos, operacion, pila, indice,
                  f"Se lee «{token}»: pop de {sacados}, se calcula {operacion} y se hace push de {formatear(r)}.")
    else:
        raise ValueError(f"Símbolo no reconocido: '{token}'")


def evaluar_posfija(expresion, pasos=None):
    """
    Notación posfija: los operadores van después de los operandos.
    Ejemplo: 3 4 + 2 *  ->  (3 + 4) * 2 = 14
    Se recorre de izquierda a derecha.
    """
    pila = Pila()
    for indice, token in enumerate(expresion.split()):
        procesar_token(token, indice, pila, pasos, prefija=False)
    if pila.tamano() != 1:
        raise ValueError("Expresión posfija inválida: sobran operandos")
    return pila.pop()


def evaluar_prefija(expresion, pasos=None):
    """
    Notación prefija: los operadores van antes de los operandos.
    Ejemplo: * + 3 4 2  ->  (3 + 4) * 2 = 14
    Se recorre de derecha a izquierda.
    """
    pila = Pila()
    tokens = expresion.split()
    for indice in range(len(tokens) - 1, -1, -1):
        procesar_token(tokens[indice], indice, pila, pasos, prefija=True)
    if pila.tamano() != 1:
        raise ValueError("Expresión prefija inválida: sobran operandos")
    return pila.pop()


def evaluar(tipo, expresion):
    """Evalúa y devuelve un diccionario listo para convertirse en JSON."""
    expresion = (expresion or "").strip()
    if not expresion:
        return {"ok": False, "error": "Escribe una expresión.", "pasos": [], "tokens": []}
    if tipo not in ("posfija", "prefija"):
        return {"ok": False, "error": "Tipo de notación inválido.", "pasos": [], "tokens": []}

    pasos = []
    try:
        if tipo == "posfija":
            valor = evaluar_posfija(expresion, pasos)
        else:
            valor = evaluar_prefija(expresion, pasos)
    except ValueError as error:
        return {"ok": False, "error": str(error), "pasos": pasos, "tokens": expresion.split()}
    return {"ok": True, "resultado": formatear(valor), "pasos": pasos,
            "tokens": expresion.split()}


# ===========================================================================
# LÓGICA 2: TORRES DE HANOI (cada torre es una Pila)
# ===========================================================================
def generar_movimientos(posicion, k, destino):
    """
    Generador recursivo de movimientos (torre origen, torre destino) para llevar los discos
    1..k a la torre 'destino', partiendo de cualquier posición válida
    (posicion[d] = torre donde está el disco d). Desde la posición inicial es el algoritmo clásico:
      1) mover k-1 discos a la torre auxiliar, 2) mover el disco k a destino,
      3) mover los k-1 discos sobre él.
    """
    if k == 0:
        return
    actual = posicion[k]
    if actual == destino:                       # el disco k ya está en su sitio
        yield from generar_movimientos(posicion, k - 1, destino)
    else:
        auxiliar = 3 - actual - destino         # la torre que no es origen ni destino
        yield from generar_movimientos(posicion, k - 1, auxiliar)
        yield (actual, destino)
        posicion[k] = destino
        yield from generar_movimientos(posicion, k - 1, destino)


class JuegoHanoi:
    MINIMO_DISCOS = 3
    MAXIMO_DISCOS = 8

    def __init__(self, n=3):
        self.reiniciar(n)

    def reiniciar(self, n):
        if not (self.MINIMO_DISCOS <= n <= self.MAXIMO_DISCOS):
            raise ValueError(f"El número de discos debe estar entre "
                             f"{self.MINIMO_DISCOS} y {self.MAXIMO_DISCOS}")
        self.n = n
        self.torres = [Pila(), Pila(), Pila()]
        for disco in range(n, 0, -1):            # del más grande (n) al más pequeño (1)
            self.torres[0].push(disco)
        self.generador = None                    # se crea al pedir el primer paso automático
        self.movimientos = 0
        self.terminado = False

    def _ejecutar(self, origen, destino):
        """Mueve el disco de la cima de 'origen' a 'destino' validando las reglas."""
        if self.torres[origen].esta_vacia():
            raise ValueError(f"La torre {'ABC'[origen]} está vacía")
        disco = self.torres[origen].peek()
        if not self.torres[destino].esta_vacia() and self.torres[destino].peek() < disco:
            raise ValueError(f"Movimiento no permitido: el disco {disco} no puede ir "
                             f"sobre el disco {self.torres[destino].peek()}")
        self.torres[destino].push(self.torres[origen].pop())
        self.movimientos += 1
        self.terminado = self.torres[2].tamano() == self.n
        return {"disco": disco, "origen": origen, "destino": destino}

    def paso(self):
        """Siguiente movimiento de la solución automática (desde la posición actual)."""
        if self.generador is None:
            posicion = {d: i for i, t in enumerate(self.torres) for d in t.elementos()}
            self.generador = generar_movimientos(posicion, self.n, 2)
        movimiento = next(self.generador, None)
        if movimiento is None:
            self.terminado = self.torres[2].tamano() == self.n
            return None
        return self._ejecutar(*movimiento)

    def mover(self, origen, destino):
        """Movimiento manual del jugador: origen y destino son 0, 1 o 2 (A, B, C)."""
        if self.terminado:
            raise ValueError("Ya está resuelto. Pulsa Reiniciar para jugar de nuevo.")
        if origen not in (0, 1, 2) or destino not in (0, 1, 2) or origen == destino:
            raise ValueError("Elige dos torres distintas (A, B o C)")
        movimiento = self._ejecutar(origen, destino)
        self.generador = None                    # la posición cambió: la solución se recalcula
        return movimiento

    def estado(self):
        return {
            "n": self.n,
            "torres": [t.elementos() for t in self.torres],
            "movimientos": self.movimientos,
            "minimo": 2 ** self.n - 1,
            "terminado": self.terminado,
        }


JUEGO = JuegoHanoi(3)
CERROJO = threading.Lock()


# ===========================================================================
# SERVIDOR LOCAL (biblioteca estándar)
# ===========================================================================
class Manejador(BaseHTTPRequestHandler):
    def log_message(self, formato, *args):      # silenciar el registro en consola
        pass

    def _responder(self, cuerpo, tipo="application/json; charset=utf-8", codigo=200):
        if isinstance(cuerpo, (dict, list)):
            cuerpo = json.dumps(cuerpo, ensure_ascii=False)
        datos = cuerpo.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(datos)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(datos)

    def _leer_json(self):
        largo = int(self.headers.get("Content-Length") or 0)
        if largo == 0:
            return {}
        return json.loads(self.rfile.read(largo).decode("utf-8"))

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._responder(HTML, "text/html; charset=utf-8")
        elif self.path == "/api/hanoi/estado":
            with CERROJO:
                self._responder({"ok": True, "estado": JUEGO.estado()})
        elif self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
        else:
            self._responder({"ok": False, "error": "No encontrado"}, codigo=404)

    def do_POST(self):
        try:
            datos = self._leer_json()
            if self.path == "/api/evaluar":
                self._responder(evaluar(datos.get("tipo"), datos.get("expresion")))
            elif self.path == "/api/hanoi/reiniciar":
                with CERROJO:
                    JUEGO.reiniciar(int(datos.get("n", 3)))
                    self._responder({"ok": True, "estado": JUEGO.estado()})
            elif self.path == "/api/hanoi/mover":
                with CERROJO:
                    movimiento = JUEGO.mover(int(datos.get("origen")), int(datos.get("destino")))
                    self._responder({"ok": True, "movimiento": movimiento, "estado": JUEGO.estado()})
            elif self.path == "/api/hanoi/paso":
                with CERROJO:
                    movimiento = JUEGO.paso()
                    self._responder({"ok": True, "movimiento": movimiento,
                                     "estado": JUEGO.estado()})
            else:
                self._responder({"ok": False, "error": "No encontrado"}, codigo=404)
        except (ValueError, TypeError, json.JSONDecodeError) as error:
            self._responder({"ok": False, "error": str(error)}, codigo=400)


# ===========================================================================
# PÁGINA HTML (solo interfaz: la lógica vive en Python)
# ===========================================================================
HTML = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ADA1 · Pilas</title>
<style>
  :root{
    --bg:#f3f5fb; --card:#ffffff; --tx:#1b2033; --mut:#6b7390; --bd:#e4e8f4;
    --ac:#4f46e5; --ac2:#7c3aed; --chip:#eef0ff; --ok:#16a34a; --err:#dc2626;
    --sombra:0 10px 40px rgba(31,41,90,.10);
  }
  @media (prefers-color-scheme: dark){
    :root{ --bg:#0f1220; --card:#181c30; --tx:#eef0fb; --mut:#98a0c0; --bd:#262b47;
           --chip:#23284a; --sombra:0 10px 40px rgba(0,0,0,.45); }
  }
  *{ box-sizing:border-box; }
  body{
    margin:0; min-height:100vh; display:flex; justify-content:center; padding:32px 16px;
    font-family: system-ui, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color:var(--tx);
    background: radial-gradient(900px 500px at 0% -10%, rgba(99,102,241,.18), transparent 60%),
                radial-gradient(800px 500px at 100% 0%, rgba(168,85,247,.14), transparent 60%),
                var(--bg);
  }
  .app{ width:min(880px,100%); }
  header{ text-align:center; margin-bottom:22px; animation:bajar .7s cubic-bezier(.2,.8,.2,1) both; }
  header h1{
    margin:0; font-size:2.4rem; letter-spacing:-.02em;
    background:linear-gradient(135deg,var(--ac),var(--ac2)); -webkit-background-clip:text;
    background-clip:text; color:transparent;
  }
  header p{ margin:6px 0 0; color:var(--mut); }

  /* ---------- Pestañas con indicador deslizante ---------- */
  .tabs{
    position:relative; display:grid; grid-template-columns:1fr 1fr; padding:4px; margin-bottom:18px;
    background:var(--card); border:1px solid var(--bd); border-radius:16px; box-shadow:var(--sombra);
  }
  .indicador{
    position:absolute; top:4px; bottom:4px; left:4px; width:calc((100% - 8px) / 2);
    border-radius:12px; background:linear-gradient(135deg,var(--ac),var(--ac2));
    transform:translateX(calc(var(--i,0) * 100%));
    transition:transform .5s cubic-bezier(.65,0,.25,1);
    box-shadow:0 6px 18px rgba(79,70,229,.35);
  }
  .tab{
    position:relative; z-index:1; border:0; background:transparent; padding:12px 8px; cursor:pointer;
    font:inherit; font-weight:600; color:var(--mut); border-radius:12px; transition:color .35s;
  }
  .tab.activa{ color:#fff; }

  /* ---------- Paneles con transición ---------- */
  .paneles{ display:grid; }
  .panel{
    grid-area:1/1; background:var(--card); border:1px solid var(--bd); border-radius:20px;
    box-shadow:var(--sombra); padding:26px;
    opacity:0; visibility:hidden; pointer-events:none; transform:translateX(60px) scale(.98);
    transition:opacity .45s ease, transform .55s cubic-bezier(.2,.8,.2,1), visibility 0s linear .55s;
  }
  .panel[data-estado="antes"]{ transform:translateX(-60px) scale(.98); }
  .panel[data-estado="activo"]{
    opacity:1; visibility:visible; pointer-events:auto; transform:none;
    transition:opacity .5s ease .12s, transform .6s cubic-bezier(.2,.8,.2,1) .12s, visibility 0s;
  }
  .panel h2{ margin:0 0 4px; font-size:1.35rem; }
  .sub{ margin:0 0 18px; color:var(--mut); font-size:.95rem; line-height:1.45; }

  /* ---------- Controles ---------- */
  .fila{ display:flex; flex-wrap:wrap; gap:10px; align-items:center; }
  .btn{
    border:0; border-radius:12px; padding:10px 16px; font:inherit; font-weight:600; cursor:pointer;
    background:var(--chip); color:var(--tx);
    transition:transform .15s, box-shadow .2s, opacity .2s;
  }
  .btn:hover:not(:disabled){ transform:translateY(-2px); box-shadow:0 6px 16px rgba(79,70,229,.2); }
  .btn:active:not(:disabled){ transform:translateY(0) scale(.97); }
  .btn:disabled{ opacity:.45; cursor:not-allowed; }
  .btn.primario{ background:linear-gradient(135deg,var(--ac),var(--ac2)); color:#fff; }
  .btn.mini{ padding:6px 12px; font-size:.85rem; font-weight:500; }

  .segmento{ display:inline-flex; background:var(--chip); border-radius:12px; padding:4px; position:relative; }
  .segmento input{ position:absolute; opacity:0; pointer-events:none; }
  .segmento label{
    padding:8px 18px; border-radius:9px; cursor:pointer; font-weight:600; color:var(--mut);
    transition:background .3s, color .3s, box-shadow .3s;
  }
  .segmento input:checked + label{ background:var(--card); color:var(--ac); box-shadow:0 2px 8px rgba(0,0,0,.12); }

  .explica{
    margin:14px 0; padding:12px 14px; border-radius:12px; background:var(--chip);
    color:var(--mut); font-size:.92rem; line-height:1.45; transition:opacity .3s;
  }
  .entrada{
    width:100%; margin:6px 0 12px; padding:14px 16px; font:600 1.15rem ui-monospace, Consolas, monospace;
    color:var(--tx); background:var(--bg); border:2px solid var(--bd); border-radius:14px; outline:none;
    transition:border-color .25s, box-shadow .25s;
  }
  .entrada:focus{ border-color:var(--ac); box-shadow:0 0 0 4px rgba(79,70,229,.15); }
  .ejemplos{ margin-top:12px; }
  .ejemplos span{ color:var(--mut); font-size:.85rem; }

  /* ---------- Resultado y traza ---------- */
  .resultado{
    margin:18px 0 6px; padding:16px 20px; border-radius:16px; border:1px solid var(--bd);
    display:flex; align-items:baseline; justify-content:space-between; gap:12px;
    animation:pop .5s cubic-bezier(.2,1.4,.4,1) both;
  }
  .resultado small{ color:var(--mut); font-weight:600; text-transform:uppercase; letter-spacing:.08em; }
  .resultado strong{ font-size:2rem; }
  .resultado.vacio strong{ color:var(--mut); }
  .resultado.ok{ background:rgba(22,163,74,.1); border-color:rgba(22,163,74,.35); }
  .resultado.ok strong{ color:var(--ok); }
  .resultado.err{ background:rgba(220,38,38,.09); border-color:rgba(220,38,38,.35); animation:tiembla .45s both; }
  .resultado.err strong{ color:var(--err); font-size:1.1rem; }

  .traza-titulo{ margin:18px 0 8px; color:var(--mut); font-size:.85rem; font-weight:600; letter-spacing:.04em; text-transform:uppercase; }
  .paso{
    display:grid; grid-template-columns:34px minmax(110px,190px) 1fr; gap:10px; align-items:center;
    padding:8px 0; border-bottom:1px dashed var(--bd);
    animation:entra .45s ease both; animation-delay:calc(var(--k) * 90ms);
  }
  .num{ width:26px; height:26px; border-radius:50%; background:var(--chip); color:var(--ac);
        display:grid; place-items:center; font-size:.8rem; font-weight:700; }
  .accion{ font-family:ui-monospace, Consolas, monospace; font-weight:600; }
  .pila{ display:flex; flex-wrap:wrap; gap:6px; align-items:center; }
  .chip{ padding:4px 12px; border-radius:10px; background:var(--chip); font-family:ui-monospace, Consolas, monospace; font-weight:600; }
  .chip.cima{ background:linear-gradient(135deg,var(--ac),var(--ac2)); color:#fff; }
  .vacia{ color:var(--mut); font-size:.85rem; }

  /* ---------- Torres de Hanoi ---------- */
  .stepper{ display:inline-flex; align-items:center; gap:10px; }
  .stepper b{ min-width:2ch; text-align:center; font-size:1.2rem; }
  .vel{ display:flex; align-items:center; gap:8px; color:var(--mut); font-size:.9rem; }
  .vel input{ accent-color:var(--ac); }

  .escenario{
    --dur:225ms; position:relative; height:330px; margin:18px 0 12px; overflow:hidden;
    border-radius:16px; border:1px solid var(--bd); background:linear-gradient(var(--card), var(--chip));
  }
  .base{ position:absolute; left:3%; right:3%; bottom:20px; height:14px; border-radius:8px; background:#64708f; }
  .varilla{ position:absolute; bottom:34px; width:8px; height:262px; margin-left:-4px; border-radius:6px 6px 0 0; background:#8d6e63; }
  .etq{ position:absolute; bottom:0; transform:translateX(-50%); font-weight:700; color:var(--mut); line-height:20px; }
  .disco{
    position:absolute; height:24px; transform:translateX(-50%); border-radius:8px; color:#fff;
    display:flex; align-items:center; justify-content:center; font-weight:700; font-size:.8rem;
    box-shadow:0 3px 8px rgba(0,0,0,.22), inset 0 -3px 0 rgba(0,0,0,.12);
    transition:left var(--dur) ease-in-out, bottom var(--dur) ease-in-out;
  }
  .estado{ display:flex; flex-wrap:wrap; gap:8px 24px; align-items:center; justify-content:space-between; }
  .estado b{ font-size:1.15rem; }
  .estado .mut{ color:var(--mut); font-size:.9rem; }
  .barra{ height:8px; border-radius:6px; background:var(--chip); margin:10px 0 14px; overflow:hidden; }
  .barra i{ display:block; height:100%; width:0; background:linear-gradient(90deg,var(--ac),var(--ac2)); transition:width .4s ease; }
  .badge{
    padding:4px 14px; border-radius:20px; font-weight:700; background:rgba(22,163,74,.15); color:var(--ok);
    opacity:0; transform:scale(.7); transition:opacity .4s, transform .5s cubic-bezier(.2,1.6,.4,1);
  }
  .badge.visible{ opacity:1; transform:none; }
  .pilas{ display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }
  .pilas div{ padding:10px 12px; border-radius:12px; background:var(--chip); font-size:.9rem; color:var(--mut); }
  .pilas code{ display:block; margin-top:2px; color:var(--tx); font-weight:600; word-break:break-word; }

  .ejemplos{ margin-top:12px; animation:entra .4s both; }
  .disco.nuevo{ animation:aparece .5s ease both; }
  .sim{ display:grid; grid-template-columns:1fr 150px; gap:16px; margin-top:18px; align-items:start; }
  .tokens{ display:flex; flex-wrap:wrap; gap:6px; min-height:34px; }
  .tok{ padding:6px 12px; border-radius:10px; background:var(--chip); font:600 1rem ui-monospace,Consolas,monospace; transition:all .3s; }
  .tok.hecho{ opacity:.35; }
  .tok.actual{ background:linear-gradient(135deg,var(--ac),var(--ac2)); color:#fff; transform:translateY(-3px) scale(1.1); }
  .paso-actual{ margin:12px 0 0; padding:12px 14px; border-radius:12px; background:var(--chip); color:var(--mut); font-size:.92rem; line-height:1.45; animation:pop .35s both; }
  .paso-actual b{ color:var(--ac); }
  .pila-v{ display:flex; flex-direction:column-reverse; gap:6px; min-height:140px; padding:8px; border:2px solid var(--bd); border-top:0; border-bottom:6px solid var(--ac); border-radius:0 0 12px 12px; }
  .pila-v:empty::before{ content:'vacía'; margin:auto; color:var(--mut); font-size:.85rem; }
  .pila-v .chip{ text-align:center; padding:8px; }
  .pila-t{ text-align:center; color:var(--mut); font-size:.75rem; letter-spacing:.08em; text-transform:uppercase; margin:2px 0; }
  .chip.nuevo{ animation:caer .45s cubic-bezier(.2,1.2,.4,1) both; }
  .zona{ position:absolute; top:0; bottom:0; width:33.3333%; z-index:10; cursor:pointer; border-radius:14px; transition:background .2s, box-shadow .2s; }
  .zona:hover{ background:rgba(79,70,229,.07); }
  .zona.sel{ background:rgba(79,70,229,.12); box-shadow:inset 0 0 0 2px var(--ac); }
  .escenario.bloqueado .zona{ cursor:not-allowed; }
  .aviso{ margin:0 0 12px; font-size:.92rem; color:var(--mut); min-height:1.3em; }
  .aviso.err{ color:var(--err); font-weight:600; }
  .disco.mal{ animation:rechazo .45s both; }
  @keyframes caer{ from{ opacity:0; transform:translateY(-34px); } to{ opacity:1; transform:none; } }
  @keyframes rechazo{ 0%,100%{ margin-left:0; } 20%{ margin-left:-10px; } 40%{ margin-left:10px; } 60%{ margin-left:-6px; } 80%{ margin-left:6px; } }
  @media (max-width:560px){ .sim{ grid-template-columns:1fr; } }

  footer{ margin-top:18px; text-align:center; color:var(--mut); font-size:.82rem; }

  @keyframes bajar{ from{ opacity:0; transform:translateY(-14px); } to{ opacity:1; transform:none; } }
  @keyframes entra{ from{ opacity:0; transform:translateX(-14px); } to{ opacity:1; transform:none; } }
  @keyframes pop{ from{ opacity:0; transform:scale(.9); } to{ opacity:1; transform:none; } }
  @keyframes aparece{ from{ opacity:0; } to{ opacity:1; } }
  @keyframes tiembla{ 0%{transform:translateX(0)} 20%{transform:translateX(-8px)} 40%{transform:translateX(8px)}
                      60%{transform:translateX(-5px)} 80%{transform:translateX(5px)} 100%{transform:none} }
  @media (max-width:560px){
    .paso{ grid-template-columns:30px 1fr; } .paso .pila{ grid-column:1 / -1; }
    .pilas{ grid-template-columns:1fr; }
  }
  @media (prefers-reduced-motion: reduce){
    *{ animation-duration:.01ms !important; transition-duration:.01ms !important; }
  }
</style>
</head>
<body>
<main class="app">
  <header>
    <h1>Pilas</h1>
    <p>ADA1 · Unidad 3 – Estructuras lineales</p>
  </header>

  <nav class="tabs" id="tabs">
    <span class="indicador"></span>
    <button class="tab activa" data-i="0">Posfija / Prefija</button>
    <button class="tab" data-i="1">Torres de Hanoi</button>
  </nav>

  <section class="paneles">
    <!-- ===================== PANEL 1: EXPRESIONES ===================== -->
    <article class="panel" id="p0" data-estado="activo">
      <h2>Evaluador de expresiones</h2>
      <p class="sub">Separa cada número y operador con espacios. Operadores válidos: + − * / ^</p>

      <div class="segmento">
        <input type="radio" name="tipo" id="t-pos" value="posfija" checked><label for="t-pos">Posfija</label>
        <input type="radio" name="tipo" id="t-pre" value="prefija"><label for="t-pre">Prefija</label>
      </div>
      <div class="explica" id="explica"></div>

      <input class="entrada" id="expr" autocomplete="off" spellcheck="false">
      <div class="fila">
        <button class="btn primario" id="btnAuto">Resolver automático</button>
        <button class="btn primario" id="btnPasos">Paso a paso</button>
        <button class="btn" id="btnEval">Evaluar</button>
        <button class="btn" id="btnLimpiar">Limpiar</button>
      </div>
      <div class="fila ejemplos" id="ejemplos"></div>

      <div class="sim">
        <div>
          <div class="tokens" id="tokens"></div>
          <div class="paso-actual" id="pasoActual"></div>
          <div class="resultado vacio" id="resultado"><small>Resultado</small><strong>—</strong></div>
        </div>
        <div><div class="pila-t">cima</div><div class="pila-v" id="pilaViva"></div><div class="pila-t">base</div></div>
      </div>
      <div class="traza-titulo">Historial de pasos (base → cima)</div>
      <div id="traza"></div>
    </article>

    <!-- ===================== PANEL 2: HANOI ===================== -->
    <article class="panel" id="p1" data-estado="despues">
      <h2>Torres de Hanoi</h2>
      <p class="sub">Cada torre es una <b>Pila</b> en Python. Solo se mueve el disco de la cima y nunca uno grande sobre uno pequeño.</p>

      <div class="fila">
        <div class="stepper">
          <span class="mut">Discos</span>
          <button class="btn mini" id="menos">−</button>
          <b id="nDiscos">3</b>
          <button class="btn mini" id="mas">+</button>
        </div>
        <button class="btn primario" id="btnResolver">Resolver</button>
        <button class="btn" id="btnPaso">Siguiente paso</button>
        <button class="btn" id="btnReiniciar">Reiniciar</button>
        <label class="vel">Velocidad <input type="range" id="vel" min="1" max="10" value="4"></label>
      </div>

      <div class="escenario" id="escenario">
        <div class="base"></div>
        <div class="varilla" style="left:16.6667%"></div>
        <div class="varilla" style="left:50%"></div>
        <div class="varilla" style="left:83.3333%"></div>
        <span class="etq" style="left:16.6667%">A</span>
        <span class="etq" style="left:50%">B</span>
        <span class="etq" style="left:83.3333%">C</span>
        <div class="zona" data-i="0" style="left:0"></div>
        <div class="zona" data-i="1" style="left:33.3333%"></div>
        <div class="zona" data-i="2" style="left:66.6667%"></div>
      </div>
      <div class="aviso" id="aviso"></div>

      <div class="estado">
        <span>Movimientos: <b id="contador">0</b> <span class="mut">(mínimo <span id="minimo">7</span>)</span></span>
        <span class="mut" id="ultimo">Sin movimientos todavía</span>
        <span class="badge" id="resuelto">¡Resuelto!</span>
      </div>
      <div class="barra"><i id="progreso"></i></div>

      <div class="pilas">
        <div>Pila A (base → cima)<code id="pila0">[]</code></div>
        <div>Pila B (base → cima)<code id="pila1">[]</code></div>
        <div>Pila C (base → cima)<code id="pila2">[]</code></div>
      </div>
    </article>
  </section>

  <footer>La lógica (Pila, evaluadores y Hanoi) se ejecuta en Python; esta página solo la muestra.</footer>
</main>

<script>
const $ = (s, r = document) => r.querySelector(s);
const crea = (tag, cls, txt) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (txt !== undefined) e.textContent = txt;
  return e;
};
const espera = ms => new Promise(r => setTimeout(r, ms));

async function api(ruta, datos) {
  const op = datos === undefined ? {} : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(datos)
  };
  const r = await fetch(ruta, op);
  return r.json();
}

/* ------------------------- Pestañas con transición ------------------------- */
const tabs = $('#tabs');
function irA(i) {
  document.querySelectorAll('.tab').forEach((t, k) => t.classList.toggle('activa', k === i));
  tabs.style.setProperty('--i', i);
  document.querySelectorAll('.panel').forEach((p, k) => {
    p.dataset.estado = k === i ? 'activo' : (k < i ? 'antes' : 'despues');
  });
}
document.querySelectorAll('.tab').forEach(t => t.addEventListener('click', () => irA(Number(t.dataset.i))));

/* --------------------------- Panel 1: expresiones --------------------------- */
const EXPLICA = {
  posfija: 'Posfija: se recorre de izquierda a derecha. Cada número entra a la pila (push); ' +
           'cada operador saca dos operandos (pop), calcula y mete el resultado.',
  prefija: 'Prefija: se recorre de derecha a izquierda. Cada número entra a la pila (push); ' +
           'cada operador saca dos operandos (el primer pop es el izquierdo), calcula y mete el resultado.'
};
const EJEMPLOS = {
  posfija: ['3 4 + 2 *', '5 1 2 + 4 * + 3 -', '2 3 ^ 4 +', '10 2 8 * + 3 -'],
  prefija: ['* + 3 4 2', '- + 5 * + 1 2 4 3', '+ ^ 2 3 4', '- + 10 * 2 8 3']
};
const tipoActual = () => document.querySelector('input[name=tipo]:checked').value;
let sesion = null, autoCorre = false, cicloAuto = 0;

function reanimar(e) { e.style.animation = 'none'; void e.offsetWidth; e.style.animation = ''; }
function mostrarResultado(v) {
  const r = $('#resultado'); r.className = 'resultado ok';
  r.replaceChildren(crea('small', null, 'Resultado'), crea('strong', null, v)); reanimar(r);
}
function mostrarError(m) {
  const r = $('#resultado'); r.className = 'resultado err';
  r.replaceChildren(crea('small', null, 'Error'), crea('strong', null, m)); reanimar(r);
}
function renderEjemplos() {
  const c = $('#ejemplos');
  c.replaceChildren(crea('span', null, 'Ejemplos de ' + tipoActual() + ':'));
  EJEMPLOS[tipoActual()].forEach(txt => {
    const b = crea('button', 'btn mini', txt);
    b.addEventListener('click', () => { $('#expr').value = txt; reiniciarSesion(); $('#expr').focus(); });
    c.append(b);
  });
  reanimar(c);
}
function actualizarTipo() {
  const e = $('#explica'); e.style.opacity = 0;
  setTimeout(() => { e.textContent = EXPLICA[tipoActual()]; e.style.opacity = 1; }, 150);
  $('#expr').placeholder = 'Ejemplo: ' + EJEMPLOS[tipoActual()][0];
  renderEjemplos(); reiniciarSesion();
}
function limpiarVista() {
  $('#tokens').replaceChildren(); $('#traza').replaceChildren(); $('#pilaViva').replaceChildren();
  const r = $('#resultado'); r.className = 'resultado vacio';
  r.replaceChildren(crea('small', null, 'Resultado'), crea('strong', null, '—'));
  $('#pasoActual').textContent = 'Escribe una expresión (o elige un ejemplo) y usa «Resolver automático» o «Paso a paso».';
}
function reiniciarSesion() { autoCorre = false; cicloAuto++; sesion = null; limpiarVista(); setBotonesExpr(); }

function setBotonesExpr() {
  const s = sesion, enCurso = s && !s.fin && s.i > 0;
  $('#btnAuto').textContent = autoCorre ? 'Pausar' : (enCurso ? 'Continuar automático' : 'Resolver automático');
  $('#btnPasos').textContent = enCurso ? `Siguiente paso (${s.i}/${s.pasos.length})` : 'Paso a paso';
}
function marcarTokens(s, actual) {
  [...$('#tokens').children].forEach((el, i) => {
    el.classList.toggle('actual', i === actual);
    el.classList.toggle('hecho', s.tipo === 'posfija' ? i < actual : i > actual);
  });
}
function mostrarPaso(s, k, retraso) {
  const p = s.pasos[k];
  const fila = crea('div', 'paso'); fila.style.setProperty('--k', retraso);
  fila.append(crea('span', 'num', k + 1), crea('span', 'accion', p.accion));
  const pila = crea('span', 'pila');
  if (!p.pila.length) pila.append(crea('em', 'vacia', 'vacía'));
  const pv = $('#pilaViva'); pv.replaceChildren();
  p.pila.forEach((v, j) => {
    const ultimo = j === p.pila.length - 1;
    const c = crea('span', 'chip' + (ultimo ? ' cima' : ''), v); pila.append(c);
    pv.append(crea('span', 'chip' + (ultimo ? ' cima nuevo' : ''), v));
  });
  fila.append(pila); $('#traza').append(fila);
  marcarTokens(s, p.indice);
  const pa = $('#pasoActual');
  pa.replaceChildren(crea('b', null, `Paso ${k + 1} de ${s.pasos.length} · `), document.createTextNode(p.detalle));
  reanimar(pa);
}
function avanzar(escalonado) {
  const s = sesion; if (!s || s.fin) return;
  if (s.i < s.pasos.length) { mostrarPaso(s, s.i, escalonado ? s.i : 0); s.i++; }
  if (s.i >= s.pasos.length) { s.fin = true; s.ok ? mostrarResultado(s.resultado) : mostrarError(s.error); }
  setBotonesExpr();
}
async function iniciarSesion() {
  const tipo = tipoActual(), expr = $('#expr').value;
  limpiarVista();
  try {
    const r = await api('/api/evaluar', { tipo, expresion: expr });
    sesion = { tipo, expr, pasos: r.pasos || [], tokens: r.tokens || [], ok: r.ok,
               resultado: r.resultado, error: r.error, i: 0, fin: false };
  } catch (e) { sesion = null; mostrarError('No se pudo conectar con el programa de Python.'); return false; }
  $('#tokens').replaceChildren(...sesion.tokens.map(t => crea('span', 'tok', t)));
  setBotonesExpr(); return true;
}
async function pasoAPaso() {
  autoCorre = false; cicloAuto++;
  if (!sesion || sesion.fin) { if (!(await iniciarSesion())) return; }
  avanzar(false);
}
async function auto() {
  if (autoCorre) { autoCorre = false; cicloAuto++; setBotonesExpr(); return; }
  if (!sesion || sesion.fin) { if (!(await iniciarSesion())) return; }
  autoCorre = true; const mio = ++cicloAuto; setBotonesExpr();
  while (autoCorre && mio === cicloAuto && sesion && !sesion.fin) {
    avanzar(false);
    if (!sesion || sesion.fin) break;
    await espera(850);
  }
  if (mio === cicloAuto) { autoCorre = false; setBotonesExpr(); }
}
async function evaluarYa() {
  autoCorre = false; cicloAuto++;
  if (!(await iniciarSesion())) return;
  while (sesion && !sesion.fin) avanzar(true);
}
document.querySelectorAll('input[name=tipo]').forEach(r => r.addEventListener('change', actualizarTipo));
$('#btnAuto').addEventListener('click', auto);
$('#btnPasos').addEventListener('click', pasoAPaso);
$('#btnEval').addEventListener('click', evaluarYa);
$('#btnLimpiar').addEventListener('click', () => { $('#expr').value = ''; reiniciarSesion(); $('#expr').focus(); });
$('#expr').addEventListener('input', reiniciarSesion);
$('#expr').addEventListener('keydown', e => { if (e.key === 'Enter') evaluarYa(); });

/* ----------------------------- Panel 2: Hanoi ------------------------------ */
const ALTO = 26, BASE = 34, LIFT = 270;
const AVISO_BASE = 'Modo manual: toca una torre para levantar su disco de arriba y luego toca la torre donde quieres ponerlo.';
let S = { n: 3, torres: [[], [], []], movimientos: 0, minimo: 7, terminado: false };
let discos = {}, origenSel = null;
let corriendo = false, ocupado = false, ciclo = 0, tarea = Promise.resolve();

const centro = i => (2 * i + 1) / 6 * 100;
const nivelY = n => BASE + n * ALTO;
const anchoPct = d => S.n === 1 ? 28 : 9 + (d - 1) * (28 - 9) / (S.n - 1);
const color = d => `hsl(${230 - (d - 1) * (210 / Math.max(S.n - 1, 1))} 78% 56%)`;
const duracion = () => Math.round(900 / Number($('#vel').value));
const fijarDur = ms => $('#escenario').style.setProperty('--dur', ms + 'ms');
function aviso(txt, err = false) { const a = $('#aviso'); a.textContent = txt; a.classList.toggle('err', err); }
function marcarZona(i) { document.querySelectorAll('.zona').forEach((z, k) => z.classList.toggle('sel', k === i)); }

function render() {
  const st = $('#escenario');
  st.querySelectorAll('.disco').forEach(d => d.remove());
  discos = {}; origenSel = null; marcarZona(-1);
  S.torres.forEach((torre, i) => torre.forEach((d, nivel) => {
    const el = crea('div', 'disco nuevo', d);
    el.addEventListener('animationend', () => el.classList.remove('nuevo'), { once: true });
    el.style.left = centro(i) + '%';
    el.style.bottom = nivelY(nivel) + 'px';
    el.style.width = anchoPct(d) + '%';
    el.style.background = color(d);
    st.append(el); discos[d] = el;
  }));
}
function setBotones() {
  $('#btnResolver').textContent = corriendo ? 'Pausar' : 'Resolver';
  $('#btnPaso').disabled = corriendo || ocupado;
  $('#menos').disabled = corriendo || S.n <= 3;
  $('#mas').disabled = corriendo || S.n >= 8;
  $('#escenario').classList.toggle('bloqueado', corriendo || ocupado);
}
function actualizarEstado(e, m) {
  S = e;
  $('#nDiscos').textContent = e.n;
  $('#contador').textContent = e.movimientos;
  $('#minimo').textContent = e.minimo;
  $('#progreso').style.width = Math.min(100, 100 * e.movimientos / e.minimo) + '%';
  if (m) $('#ultimo').textContent = `Disco ${m.disco}: ${'ABC'[m.origen]} → ${'ABC'[m.destino]}`;
  else if (e.movimientos === 0) $('#ultimo').textContent = 'Sin movimientos todavía';
  e.torres.forEach((t, i) => { $('#pila' + i).textContent = '[' + t.join(', ') + ']'; });
  $('#resuelto').classList.toggle('visible', e.terminado);
  setBotones();
}

/* --- movimiento automático / siguiente paso (la solución la calcula Python) --- */
async function animar(m, estado) {
  const el = discos[m.disco], d = duracion();
  fijarDur(d); el.style.zIndex = 5;
  el.style.bottom = LIFT + 'px';                              await espera(d + 30);   // subir
  el.style.left = centro(m.destino) + '%';                    await espera(d + 30);   // cruzar
  el.style.bottom = nivelY(estado.torres[m.destino].length - 1) + 'px'; await espera(d + 30);   // bajar
  el.style.zIndex = '';
}
async function paso() {
  const r = await api('/api/hanoi/paso', {});
  if (!r.ok) return r;
  if (r.movimiento) await animar(r.movimiento, r.estado);
  actualizarEstado(r.estado, r.movimiento);
  return r;
}
async function soltarSeleccion() { if (origenSel !== null) { deseleccionar(); await espera(280); } }
async function reiniciar(n) {
  corriendo = false; ciclo++;
  await tarea.catch(() => {});
  const r = await api('/api/hanoi/reiniciar', { n });
  if (!r.ok) return;
  S = r.estado; render(); actualizarEstado(S, null); aviso(AVISO_BASE);
}
async function alternarResolver() {
  if (corriendo) { corriendo = false; setBotones(); return; }
  if (S.terminado) await reiniciar(S.n);
  corriendo = true; setBotones();
  const mio = ciclo;
  tarea = (async () => {
    try {
      await soltarSeleccion();
      while (corriendo && mio === ciclo) {
        const r = await paso();
        if (!r.ok || !r.movimiento || r.estado.terminado) break;
      }
    } catch (e) { /* el servidor dejó de responder */ }
    if (mio === ciclo) { corriendo = false; setBotones(); }
  })();
}
function pasoManual() {
  if (corriendo || ocupado || S.terminado) return;
  ocupado = true; setBotones();
  tarea = (async () => { await soltarSeleccion(); await paso(); })()
    .catch(() => {}).finally(() => { ocupado = false; setBotones(); });
}

/* --- modo manual: elegir torre origen y luego torre destino --- */
function seleccionar(i) {
  origenSel = i; marcarZona(i);
  const tope = S.torres[i][S.torres[i].length - 1];
  fijarDur(180); discos[tope].style.zIndex = 5; discos[tope].style.bottom = LIFT + 'px';
  aviso(`Disco ${tope} levantado de la torre ${'ABC'[i]}. Elige la torre destino (o toca la misma para soltarlo).`);
}
function deseleccionar() {
  if (origenSel === null) return;
  const t = S.torres[origenSel], el = discos[t[t.length - 1]];
  origenSel = null; marcarZona(-1);
  if (el) { el.style.bottom = nivelY(t.length - 1) + 'px'; setTimeout(() => { el.style.zIndex = ''; }, 250); }
  aviso(AVISO_BASE);
}
async function moverManual(o, d) {
  const t = S.torres[o], disco = t[t.length - 1], el = discos[disco];
  const r = await api('/api/hanoi/mover', { origen: o, destino: d });
  origenSel = null; marcarZona(-1);
  if (!r.ok) {                                         // movimiento ilegal: el disco regresa
    aviso(r.error, true);
    el.classList.add('mal'); await espera(450); el.classList.remove('mal');
    el.style.bottom = nivelY(t.length - 1) + 'px'; await espera(260); el.style.zIndex = '';
    return;
  }
  const dur = duracion(); fijarDur(dur);
  el.style.left = centro(d) + '%';                                           await espera(dur + 30);
  el.style.bottom = nivelY(r.estado.torres[d].length - 1) + 'px';            await espera(dur + 30);
  el.style.zIndex = '';
  actualizarEstado(r.estado, r.movimiento);
  aviso(r.estado.terminado ? '¡Lo lograste! Todos los discos están en la torre C.' : AVISO_BASE);
}
function clickTorre(i) {
  if (corriendo || ocupado) return;
  if (S.terminado) { aviso('Ya está resuelto. Pulsa Reiniciar para jugar de nuevo.', true); return; }
  if (origenSel === null) {
    if (!S.torres[i].length) { aviso(`La torre ${'ABC'[i]} está vacía: elige una torre que tenga discos.`, true); return; }
    seleccionar(i);
  } else if (origenSel === i) {
    deseleccionar();
  } else {
    const o = origenSel;
    ocupado = true; setBotones();
    tarea = moverManual(o, i).catch(() => {}).finally(() => { ocupado = false; setBotones(); });
  }
}
document.querySelectorAll('.zona').forEach(z => z.addEventListener('click', () => clickTorre(Number(z.dataset.i))));
$('#btnResolver').addEventListener('click', alternarResolver);
$('#btnPaso').addEventListener('click', pasoManual);
$('#btnReiniciar').addEventListener('click', () => reiniciar(S.n));
$('#menos').addEventListener('click', () => reiniciar(S.n - 1));
$('#mas').addEventListener('click', () => reiniciar(S.n + 1));

/* ------------------------------- Arranque --------------------------------- */
actualizarTipo();
api('/api/hanoi/estado').then(r => {
  if (r.ok) { S = r.estado; render(); actualizarEstado(S, null); aviso(AVISO_BASE); }
});
</script>
</body>
</html>
"""


# ===========================================================================
# PROGRAMA PRINCIPAL
# ===========================================================================
def main():
    parser = argparse.ArgumentParser(description="ADA1 - Pilas (interfaz web)")
    parser.add_argument("--puerto", type=int, default=8765, help="puerto local (por defecto 8765)")
    parser.add_argument("--no-navegador", action="store_true", help="no abrir el navegador")
    args = parser.parse_args()

    try:
        servidor = ThreadingHTTPServer(("127.0.0.1", args.puerto), Manejador)
    except OSError:                                   # puerto ocupado: usar uno libre
        servidor = ThreadingHTTPServer(("127.0.0.1", 0), Manejador)

    url = f"http://127.0.0.1:{servidor.server_address[1]}/"
    print(f"ADA1 - Pilas corriendo en {url}")
    print("Presiona Ctrl + C para cerrar.")
    if not args.no_navegador:
        threading.Timer(0.6, webbrowser.open, args=(url,)).start()

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrando...")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
