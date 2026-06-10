import os
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QMessageBox,
    QMenuBar,
    QMenu,
    QScrollArea,
)

from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

from core.libvirt_manager import LibvirtManager
from ui.create_vm_window import CreateVMWindow
from ui.dialog_helper import DialogHelper
from ui.vm_card import VMCard


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.manager = LibvirtManager()
        self.selected_vm = None

        self.setWindowTitle("Virtual Client")
        self.resize(950, 600) 

        # 🦇 MODO OSCURO GLOBAL - DEEP DARK ELEGANCE V2 🦇
        self.setStyleSheet("""
            /* 🌌 Fondo principal súper profundo */
            QWidget {
                background-color: #121212; 
                color: #e0e0e0;
                font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            }

            /* 🔘 Botones por defecto (Secundarios: Apagar, Refrescar) */
            QPushButton {
                background-color: #1e1e1e;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 10px 15px;
                font-size: 13px;
                font-weight: 500;
                color: #cccccc;
            }
            QPushButton:hover {
                background-color: #2a2d35;
                border: 1px solid #555555; /* Un brillo gris sutil */
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #333333;
                color: white;
            }

            /* 🔵 Botones Primarios Mate/Pizarra (Crear, Iniciar) */
            QPushButton#btn_primario {
                background-color: #1a3a5f; /* Azul mate, corporativo y sobrio */
                border: 1px solid #2b507d;
                color: #e2e8f0;
                font-weight: bold;
            }
            QPushButton#btn_primario:hover {
                background-color: #244b7a; /* Iluminación sutil */
                border: 1px solid #3b6ea3;
                color: #ffffff;
            }
            QPushButton#btn_primario:pressed {
                background-color: #122b47;
            }

            /* 🔴 Botones de Peligro (Forzar Apagado, Eliminar) */
            QPushButton#btn_peligro {
                background-color: #1e1e1e;
                border: 1px solid #333333;
                color: #cccccc;
            }
            QPushButton#btn_peligro:hover {
                background-color: #3d1414; /* Rojo sangre apagado, elegante */
                border: 1px solid #8c2323;
                color: #ffcccc;
            }
            QPushButton#btn_peligro:pressed {
                background-color: #5a1818;
                color: #ffffff;
            }

            /* 📜 Scrollbar invisible y refinado */
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #333333;
                min-height: 30px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #555555;
            }
            
            /* 🗄️ Menú superior limpio */
            QMenuBar {
                background-color: #181818;
                border-bottom: 1px solid #222222;
                padding: 4px;
            }
            QMenuBar::item:selected {
                background-color: #2a2d35;
            }
            QMenu {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #333333;
            }
            QMenu::item:selected {
                background-color: #1a3a5f;
            }
        """)

        self.init_ui()
        self.cargar_vms()

    def init_ui(self):

        layout_principal = QVBoxLayout()
        layout_principal.setContentsMargins(0, 0, 0, 0)

        # MENU
        menu_bar = QMenuBar(self)
        menu_herramientas = QMenu("Herramientas", self)

        accion_limpiar = QAction("Limpiar discos huérfanos", self)
        accion_refrescar = QAction("Refrescar VMs", self)

        accion_limpiar.triggered.connect(self.limpiar_discos)
        accion_refrescar.triggered.connect(self.cargar_vms)

        menu_herramientas.addAction(accion_limpiar)
        menu_herramientas.addAction(accion_refrescar)
        menu_bar.addMenu(menu_herramientas)

        layout_principal.addWidget(menu_bar)

        # CONTENIDO
        contenido = QHBoxLayout()
        contenido.setContentsMargins(25, 20, 25, 25) 
        contenido.setSpacing(24)

        # IZQUIERDA (HEADER COMPUESTO + VM CARDS)
        panel_izquierdo = QVBoxLayout()
        panel_izquierdo.setSpacing(16)

        # 🚀 HITO 4 FINAL: CABECERA CON RELLENO HORIZONTAL DE BALANCEO
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)

        fila_titulo = QHBoxLayout()
        fila_titulo.setSpacing(12)

        # Contenedor izquierdo para Título + Píldora
        bloque_izquierdo_titulo = QHBoxLayout()
        bloque_izquierdo_titulo.setSpacing(12)
        bloque_izquierdo_titulo.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)

        titulo = QLabel("Máquinas Virtuales")
        titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        
        self.lbl_contadores = QLabel()
        self.lbl_contadores.setStyleSheet("""
            font-size: 11px; 
            font-weight: bold;
            color: #888888; 
            background-color: #1a1a1a;
            border: 1px solid #282828;
            border-radius: 12px;
            padding: 3px 10px;
            margin-bottom: 2px;
        """)
        
        bloque_izquierdo_titulo.addWidget(titulo)
        bloque_izquierdo_titulo.addWidget(self.lbl_contadores)

        # 🎯 EL DETALLE DE RELLENO: Status del Servicio al extremo derecho
        lbl_status_servicio = QLabel("● QEMU/KVM Conectado")
        lbl_status_servicio.setStyleSheet("""
            font-size: 11px;
            font-weight: bold;
            color: #2ecc71;
            background-color: rgba(46, 204, 113, 0.06);
            border: 1px solid rgba(46, 204, 113, 0.2);
            border-radius: 4px;
            padding: 4px 10px;
            margin-bottom: 2px;
        """)
        lbl_status_servicio.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Añadimos los elementos a la fila usando un Stretch en medio para empujar el status a la derecha
        fila_titulo.addLayout(bloque_izquierdo_titulo)
        fila_titulo.addStretch() # Esto absorbe el espacio vacío indeseado
        fila_titulo.addWidget(lbl_status_servicio)

        subtitulo = QLabel("Panel local de gestión de hipervisor e instancias QEMU/KVM")
        subtitulo.setStyleSheet("font-size: 12px; color: #555555;")

        header_layout.addLayout(fila_titulo)
        header_layout.addWidget(subtitulo)
        
        panel_izquierdo.addLayout(header_layout)

        # Área de Scroll de Tarjetas
        self.scroll = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout()

        self.scroll_widget.setLayout(self.scroll_layout)
        self.scroll.setWidget(self.scroll_widget)
        self.scroll.setWidgetResizable(True)

        panel_izquierdo.addWidget(self.scroll)

        # DERECHA (BOTONES ALINEADOS)
        panel_derecho = QVBoxLayout()
        panel_derecho.setSpacing(12) 
        panel_derecho.setContentsMargins(0, 48, 0, 0)

        # Instanciamos con iconografía Unicode
        self.boton_refrescar = QPushButton("↻  Refrescar")
        self.boton_crear = QPushButton("＋  Crear VM")
        self.boton_iniciar = QPushButton("►  Iniciar VM")
        self.boton_apagar = QPushButton("■  Apagar VM")
        self.boton_forzar = QPushButton("▲  Forzar Apagado")
        self.boton_eliminar = QPushButton("✕  Eliminar VM")

        # Asignamos los estilos correspondientes
        self.boton_crear.setObjectName("btn_primario")
        self.boton_iniciar.setObjectName("btn_primario")
        self.boton_forzar.setObjectName("btn_peligro")
        self.boton_eliminar.setObjectName("btn_peligro")

        # Conexiones
        self.boton_refrescar.clicked.connect(self.cargar_vms)
        self.boton_crear.clicked.connect(self.abrir_crear_vm)
        self.boton_iniciar.clicked.connect(self.iniciar_vm)
        self.boton_apagar.clicked.connect(self.apagar_vm)
        self.boton_forzar.clicked.connect(self.forzar_apagado)
        self.boton_eliminar.clicked.connect(self.eliminar_vm)

        # Agregamos al panel
        panel_derecho.addWidget(self.boton_refrescar)
        panel_derecho.addWidget(self.boton_crear)
        panel_derecho.addWidget(self.boton_iniciar)
        panel_derecho.addWidget(self.boton_apagar)
        panel_derecho.addWidget(self.boton_forzar)
        panel_derecho.addWidget(self.boton_eliminar)

        panel_derecho.addStretch()

        contenido.addLayout(panel_izquierdo, 3)
        contenido.addLayout(panel_derecho, 1)

        layout_principal.addLayout(contenido)
        self.setLayout(layout_principal)

    # =========================
    # FUNCIONES
    # =========================

    def limpiar_discos(self):
        try:
            self.manager.limpiar_discos_huerfanos()
            DialogHelper.info(self, "Limpieza", "Discos huérfanos eliminados correctamente")
        except Exception as e:
            DialogHelper.error(self, "Error en limpieza", str(e))

    def cargar_vms(self):
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

        vms = self.manager.listar_vms()

        total_vms = len(vms)
        encendidas = 0

        for vm in vms:
            if vm.get("estado") == "Encendida":
                encendidas += 1

            card = VMCard(vm)
            card.mousePressEvent = lambda e, name=vm["nombre"], c=card: self.seleccionar_vm(name, c)
            self.scroll_layout.addWidget(card)

        # Renderizamos los contadores en la cabecera dinámica
        self.lbl_contadores.setText(f"{total_vms} en total  •  {encendidas} Encendidas")

        self.scroll_layout.addStretch()

    def seleccionar_vm(self, nombre, tarjeta_clickeada=None):
        self.selected_vm = nombre

        if tarjeta_clickeada:
            for i in range(self.scroll_layout.count()):
                item = self.scroll_layout.itemAt(i)
                if item is not None:
                    widget = item.widget()
                    if hasattr(widget, 'set_seleccionada'):
                        widget.set_seleccionada(False)

            tarjeta_clickeada.set_seleccionada(True)

    def obtener_vm_seleccionada(self):
        if not self.selected_vm:
            DialogHelper.warning(self, "Error", "Seleccione una VM")
            return None
        return self.selected_vm

    # =========================
    # ACCIONES
    # =========================

    def iniciar_vm(self):
        nombre = self.obtener_vm_seleccionada()
        if nombre is None:
            return

        try:
            self.manager.iniciar_vm(nombre)
            DialogHelper.info(self, "OK", f"{nombre} iniciada correctamente")
            self.cargar_vms() 
        except Exception as e:
            DialogHelper.error(self, "Error al iniciar VM", str(e))

    def apagar_vm(self):
        nombre = self.obtener_vm_seleccionada()
        if nombre is None:
            return

        try:
            self.manager.apagar_vm(nombre)
            DialogHelper.info(self, "OK", f"{nombre} apagada correctamente")
            self.cargar_vms() 
        except Exception as e:
            DialogHelper.error(self, "Error al apagar VM", str(e))

    def forzar_apagado(self):
        nombre = self.obtener_vm_seleccionada()
        if nombre is None:
            return

        try:
            self.manager.forzar_apagado(nombre)
            DialogHelper.info(self, "OK", f"{nombre} forzada a apagado")
            self.cargar_vms() 
        except Exception as e:
            DialogHelper.error(self, "Error al forzar apagado", str(e))

    def eliminar_vm(self):
        nombre = self.obtener_vm_seleccionada()
        if nombre is None:
            return

        respuesta = DialogHelper.confirm(
            self,
            "Eliminar VM",
            f"¿Seguro que quieres eliminar {nombre}?"
        )

        if respuesta == QMessageBox.StandardButton.No:
            return

        try:
            self.manager.eliminar_vm(nombre)
            DialogHelper.info(self, "Éxito", f"{nombre} eliminada correctamente")
            self.selected_vm = None 
            self.cargar_vms() 
        except Exception as e:
            DialogHelper.error(self, "Error eliminando VM", str(e))

    def abrir_crear_vm(self):
        try:
            self.ventana_crear = CreateVMWindow()
            self.ventana_crear.show()
        except Exception as e:
            DialogHelper.error(self, "Error abriendo ventana", str(e))