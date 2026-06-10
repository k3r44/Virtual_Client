import os
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt

class VMCard(QFrame):

    def __init__(self, vm):
        super().__init__()
        
        self.setObjectName("VMCardMain")
        self.setFixedHeight(115)
        
        # ✨ EL DETALLE DE EXPERIENCIA: Cambia el cursor a una mano interactiva al pasar por encima
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout_principal = QVBoxLayout()
        layout_principal.setContentsMargins(16, 12, 16, 12)
        layout_principal.setSpacing(8)

        # =========================
        # PROCESAMIENTO DE DATOS
        # =========================
        nombre = vm.get("nombre", "Desconocido")
        estado = vm.get("estado", "Desconocido")
        ram = vm.get("ram", "N/A")
        cpu = vm.get("cpu", "N/A")
        
        disco_val = vm.get("disco", "N/A")
        if isinstance(disco_val, int):
            disco_str = f"{disco_val} GB"
        else:
            disco_str = str(disco_val)
        
        iso_raw = vm.get("iso", "N/A")
        iso = os.path.basename(iso_raw) if iso_raw and iso_raw != "N/A" else "Sin ISO"

        # =========================
        # CABECERA (Anclada a la izquierda)
        # =========================
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        self.icono_punto = QLabel("●")
        color_estado = "#2ecc71" if estado == "Encendida" else "#e74c3c"
        self.icono_punto.setStyleSheet(f"color: {color_estado}; font-size: 13px; font-weight: bold; background: transparent;")
        
        self.titulo = QLabel(nombre)
        self.titulo.setStyleSheet("font-weight: bold; font-size: 15px; color: #ffffff; background: transparent;")
        
        bg_estado = "rgba(46, 204, 113, 0.08)" if estado == "Encendida" else "rgba(231, 76, 60, 0.08)"
        self.estado = QLabel(estado)
        self.estado.setStyleSheet(f"""
            font-weight: bold; 
            font-size: 11px; 
            color: {color_estado}; 
            background-color: {bg_estado};
            border: 1px solid {color_estado};
            border-radius: 4px;
            padding: 2px 8px;
        """)
        
        header_layout.addWidget(self.icono_punto)
        header_layout.addWidget(self.titulo)
        header_layout.addWidget(self.estado)
        header_layout.addStretch()

        # =========================
        # RECURSOS (Píldoras / Badges)
        # =========================
        recursos_layout = QHBoxLayout()
        recursos_layout.setSpacing(6)
        
        self.ram = QLabel(f"RAM  {ram} MB")
        self.cpu = QLabel(f"CPU  {cpu} vCPU")
        self.disco = QLabel(f"DISCO  {disco_str}")
        
        for badge in (self.ram, self.cpu, self.disco):
            badge.setObjectName("Badge")
        
        recursos_layout.addWidget(self.ram)
        recursos_layout.addWidget(self.cpu)
        recursos_layout.addWidget(self.disco)
        recursos_layout.addStretch()

        # =========================
        # ISO (Sutil y minimalista)
        # =========================
        self.iso = QLabel(f"•  ISO: {iso}")
        self.iso.setStyleSheet("color: #555555; font-size: 11px; padding-left: 2px; background: transparent;")

        # =========================
        # ENSAMBLAR COMPONENTES
        # =========================
        layout_principal.addLayout(header_layout)
        layout_principal.addLayout(recursos_layout)
        layout_principal.addWidget(self.iso)

        self.setLayout(layout_principal)

        # Estado inicial por defecto
        self.esta_seleccionada = False
        self.actualizar_estilo_base()

    def set_seleccionada(self, seleccionada):
        """Cambia el estado interno y fuerza el refreshed de la hoja de estilos"""
        self.esta_seleccionada = seleccionada
        self.actualizar_estilo_base()

    def actualizar_estilo_base(self):
        """Maneja las hojas de estilo de manera atómica para asegurar que el hover funcione siempre"""
        if self.esta_seleccionada:
            self.setStyleSheet("""
                QFrame#VMCardMain {
                    border: 2px solid #007acc;
                    border-radius: 8px;
                    background-color: #1e1e21; /* Tono sutilmente más claro que da contraste de foco */
                }
                QLabel#Badge {
                    background-color: #121212;
                    border: 1px solid #444444;
                    border-radius: 4px;
                    padding: 3px 8px;
                    font-size: 11px;
                    font-weight: bold;
                    color: #ffffff; /* Brillo total a las píldoras activas */
                }
            """)
        else:
            # Al estructurarlo así, el motor de estilos de Qt no se rompe con los clics externos
            self.setStyleSheet("""
                QFrame#VMCardMain {
                    border: 1px solid #222222;
                    border-radius: 8px;
                    background-color: #161616;
                }
                QFrame#VMCardMain:hover {
                    border: 1px solid #444444;
                    background-color: #1b1b1d; /* Iluminación limpia al pasar el cursor */
                }
                QLabel#Badge {
                    background-color: #0f0f0f;
                    border: 1px solid #242424;
                    border-radius: 4px;
                    padding: 3px 8px;
                    font-size: 11px;
                    font-weight: bold;
                    color: #777777;
                }
            """)