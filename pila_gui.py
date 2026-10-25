"""
Pila (stack) con interfaz minimalista en Tkinter.
Capacidad máxima: 8 elementos. TOPE = 0 -> pila vacía.

- Insertar / Eliminar de forma manual.
- "Siguiente" ejecuta, una por una, las operaciones a-i del problema.
"""

import tkinter as tk

CAPACIDAD = 8

# Paleta minimalista
BG, SLOT, LINEA = "#111111", "#1c1c1c", "#333333"
TEXTO, APAGADO = "#eeeeee", "#6b6b6b"
ACENTO, ERROR = "#4ade80", "#f87171"
FUENTE = ("Segoe UI", 11)

# Operaciones del problema: (inciso, acción, valor / variable destino)
PASOS = [
    ("a", "insertar", "X"), ("b", "insertar", "Y"),
    ("c", "eliminar", "Z"), ("d", "eliminar", "T"),
    ("e", "eliminar", "U"), ("f", "insertar", "V"),
    ("g", "insertar", "W"), ("h", "eliminar", "p"),
    ("i", "insertar", "R"),
]


class Pila:
    def __init__(self, capacidad=CAPACIDAD):
        self.capacidad = capacidad
        self.datos = [None] * capacidad
        self.tope = 0

    def insertar(self, elemento):
        if self.tope == self.capacidad:
            return False                      # desbordamiento
        self.datos[self.tope] = elemento
        self.tope += 1
        return True

    def eliminar(self):
        if self.tope == 0:
            return None                       # subdesbordamiento
        self.tope -= 1
        elemento, self.datos[self.tope] = self.datos[self.tope], None
        return elemento


class App:
    def __init__(self, root):
        self.root = root
        root.title("Pila")
        root.configure(bg=BG)
        root.resizable(False, False)

        self.pila = Pila()
        self.paso = 0

        # Dibujo de la pila
        self.canvas = tk.Canvas(root, width=260, height=8 * 38 + 20,
                                bg=BG, highlightthickness=0)
        self.canvas.pack(padx=24, pady=(20, 8))

        # Entrada + botones
        fila = tk.Frame(root, bg=BG)
        fila.pack(padx=24, pady=4)
        self.entrada = tk.Entry(fila, width=8, font=FUENTE, bg=SLOT, fg=TEXTO,
                                insertbackground=TEXTO, relief="flat",
                                justify="center", highlightthickness=1,
                                highlightbackground=LINEA, highlightcolor=ACENTO)
        self.entrada.pack(side="left", ipady=4, padx=(0, 8))
        self.entrada.bind("<Return>", lambda e: self.insertar())
        self.entrada.focus()
        self._boton(fila, "Insertar", self.insertar).pack(side="left", padx=2)
        self._boton(fila, "Eliminar", self.eliminar).pack(side="left", padx=2)

        # Mensaje de estado
        self.mensaje = tk.Label(root, text="", font=FUENTE, bg=BG, fg=APAGADO)
        self.mensaje.pack(pady=(10, 4))

        # Modo paso a paso (incisos a-i)
        fila2 = tk.Frame(root, bg=BG)
        fila2.pack(padx=24, pady=(4, 20))
        self.btn_paso = self._boton(fila2, "", self.siguiente)
        self.btn_paso.pack(side="left", padx=2)
        self._boton(fila2, "Reiniciar", self.reiniciar).pack(side="left", padx=2)

        self.dibujar()
        self._actualizar_boton_paso()

    # ---------- utilidades de interfaz ----------
    def _boton(self, padre, texto, comando):
        return tk.Button(padre, text=texto, command=comando, font=FUENTE,
                         bg=SLOT, fg=TEXTO, activebackground=LINEA,
                         activeforeground=TEXTO, relief="flat", bd=0,
                         padx=12, pady=5, cursor="hand2")

    def _decir(self, texto, color=APAGADO):
        self.mensaje.config(text=texto, fg=color)

    def dibujar(self):
        c = self.canvas
        c.delete("all")
        alto, x0, x1 = 38, 60, 180
        for pos in range(CAPACIDAD, 0, -1):             # 8 arriba, 1 abajo
            y0 = (CAPACIDAD - pos) * alto + 8
            y1 = y0 + alto - 4
            valor = self.pila.datos[pos - 1]
            lleno = valor is not None
            c.create_text(x0 - 14, (y0 + y1) / 2, text=str(pos),
                          fill=APAGADO, font=("Segoe UI", 9))
            c.create_rectangle(x0, y0, x1, y1, outline=ACENTO if pos == self.pila.tope else LINEA,
                               fill=SLOT, width=2 if pos == self.pila.tope else 1)
            if lleno:
                c.create_text((x0 + x1) / 2, (y0 + y1) / 2, text=str(valor),
                              fill=TEXTO, font=("Segoe UI", 13, "bold"))
            if pos == self.pila.tope:
                c.create_text(x1 + 12, (y0 + y1) / 2, text="◄ TOPE",
                              anchor="w", fill=ACENTO, font=("Segoe UI", 10, "bold"))
        if self.pila.tope == 0:
            c.create_text(x1 + 12, (CAPACIDAD - 1) * alto + 8 + (alto - 4) / 2,
                          text="TOPE = 0", anchor="w", fill=ACENTO,
                          font=("Segoe UI", 10, "bold"))

    # ---------- operaciones ----------
    def _insertar(self, valor):
        if self.pila.insertar(valor):
            self._decir(f"Insertar {valor}  ·  TOPE = {self.pila.tope}")
        else:
            self._decir(f"Desbordamiento: la pila está llena ({CAPACIDAD})", ERROR)

    def _eliminar(self, destino=None):
        sacado = self.pila.eliminar()
        if sacado is None:
            self._decir("Subdesbordamiento: la pila está vacía", ERROR)
        else:
            extra = f" → {destino}" if destino else ""
            self._decir(f"Eliminó {sacado}{extra}  ·  TOPE = {self.pila.tope}")

    def insertar(self):
        valor = self.entrada.get().strip()
        if not valor:
            self._decir("Escribe un valor para insertar")
            return
        self._insertar(valor)
        self.entrada.delete(0, "end")
        self.dibujar()

    def eliminar(self):
        self._eliminar()
        self.dibujar()

    def siguiente(self):
        if self.paso >= len(PASOS):
            return
        inciso, accion, valor = PASOS[self.paso]
        if accion == "insertar":
            self._insertar(valor)
        else:
            self._eliminar(valor)
        self.mensaje.config(text=f"{inciso})  " + self.mensaje.cget("text"))
        self.paso += 1
        self.dibujar()
        self._actualizar_boton_paso()

    def reiniciar(self):
        self.pila = Pila()
        self.paso = 0
        self._decir("")
        self.dibujar()
        self._actualizar_boton_paso()

    def _actualizar_boton_paso(self):
        if self.paso < len(PASOS):
            inciso, accion, valor = PASOS[self.paso]
            nombre = "Insertar" if accion == "insertar" else "Eliminar"
            self.btn_paso.config(text=f"Siguiente: {inciso}) {nombre} {valor}",
                                 state="normal")
        else:
            self.btn_paso.config(text="Fin (a–i)", state="disabled")


if __name__ == "__main__":
    ventana = tk.Tk()
    App(ventana)
    ventana.mainloop()
