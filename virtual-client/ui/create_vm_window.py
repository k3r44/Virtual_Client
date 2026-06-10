from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QMessageBox,
    QSpinBox,
    QFileDialog
)
import os

from core.libvirt_manager import LibvirtManager

class CreateVMWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.manager = LibvirtManager()

        self.setWindowTitle("Crear VM")
        self.resize(400, 450)

        # 🦇 MODO OSCURO PARA LA VENTANA Y SUS NOTIFICACIONES 🦇
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #cccccc;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #ffffff;
                font-weight: bold;
                margin-top: 5px;
            }
            /* Inputs de texto y números */
            QLineEdit, QSpinBox, QComboBox {
                background-color: #2d2d30;
                border: 1px solid #3f3f46;
                border-radius: 4px;
                padding: 6px;
                color: #ffffff;
                selection-background-color: #007acc;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border: 1px solid #007acc;
                background-color: #1e1e1e;
            }
            /* Botones */
            QPushButton {
                background-color: #2d2d30;
                border: 1px solid #3f3f46;
                border-radius: 5px;
                padding: 8px 12px;
                color: #ffffff;
                font-weight: bold;
                margin-top: 5px;
            }
            QPushButton:hover {
                background-color: #3e3e42;
                border: 1px solid #007acc;
            }
            QPushButton:pressed {
                background-color: #007acc;
                color: white;
            }
            /* Estilos específicos para las notificaciones (QMessageBox) */
            QMessageBox {
                background-color: #1e1e1e;
            }
            QMessageBox QLabel {
                color: #cccccc;
                font-weight: normal; /* Para que el texto del mensaje no sea negrita */
            }
            QMessageBox QPushButton {
                min-width: 80px;
            }
        """)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # NOMBRE
        layout.addWidget(QLabel("Nombre VM"))
        self.input_nombre = QLineEdit()
        layout.addWidget(self.input_nombre)

        # RAM
        layout.addWidget(QLabel("RAM MB"))
        self.input_ram = QSpinBox()
        self.input_ram.setMinimum(1024)
        self.input_ram.setMaximum(8192)
        self.input_ram.setValue(4096)
        layout.addWidget(self.input_ram)

        # CPUs
        layout.addWidget(QLabel("vCPUs"))
        self.input_cpu = QSpinBox()
        self.input_cpu.setMinimum(1)
        self.input_cpu.setMaximum(6)
        self.input_cpu.setValue(2)
        layout.addWidget(self.input_cpu)

        # DISCO
        layout.addWidget(QLabel("Disco GB"))
        self.input_disco = QSpinBox()
        self.input_disco.setMinimum(20)
        self.input_disco.setMaximum(200)
        self.input_disco.setValue(50)
        layout.addWidget(self.input_disco)

        # ISO
        layout.addWidget(QLabel("Imagen ISO"))
        self.input_iso = QLineEdit()
        layout.addWidget(self.input_iso)

        self.boton_buscar_iso = QPushButton("Buscar ISO")
        self.boton_buscar_iso.clicked.connect(self.buscar_iso)
        layout.addWidget(self.boton_buscar_iso)

        # BOTON CREAR
        self.boton_crear = QPushButton("Crear VM")
        # Le damos un colorcito especial al botón principal para que resalte
        self.boton_crear.setStyleSheet("""
            QPushButton {
                background-color: #007acc; 
                border: none;
            }
            QPushButton:hover {
                background-color: #0098ff;
            }
        """)
        self.boton_crear.clicked.connect(self.crear_vm)
        layout.addWidget(self.boton_crear)

        self.setLayout(layout)

    def buscar_iso(self):
        archivo, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar ISO",
            "/home/hector/imagenesIso",
            "ISO Files (*.iso)"
        )
        if archivo:
            self.input_iso.setText(archivo)

    def cargar_isos(self):
        carpeta_isos = "/home/hector/imagenesIso"
        archivos = os.listdir(carpeta_isos)
        for archivo in archivos:
            if archivo.endswith(".iso"):
                self.combo_iso.addItem(archivo)

    def crear_vm(self):
        # 1. Obtenemos nombre e ISO y les quitamos los espacios en blanco extra
        nombre = self.input_nombre.text().strip()
        iso_path = self.input_iso.text().strip()

        # 🛑 CADENERO 1: Validar el nombre
        if not nombre:
            QMessageBox.warning(
                self, 
                "Faltan datos", 
                "¡Oye! Tienes que ponerle un nombre a la máquina virtual."
            )
            return

        # 🛑 CADENERO 2: Validar la ISO
        if not iso_path:
            QMessageBox.warning(
                self, 
                "Faltan datos", 
                "¡No puedes instalar aire, bro! Selecciona una imagen ISO primero."
            )
            return

        # Si pasa los cadeneros, sigue con la recolección de los demás datos
        ram = self.input_ram.value()
        cpu = self.input_cpu.value()
        disco = self.input_disco.value()
        
        iso_lower = iso_path.lower()

        # Lógica de variante de OS
        if "win" in iso_lower:
            os_variant = "win10"
        elif "mint" in iso_lower:
            os_variant = "ubuntu22.04"
        else:
            os_variant = "fedora39"

        # Mandar a crear la VM
        self.manager.crear_vm(
            nombre,
            ram,
            cpu,
            disco,
            iso_path,
            os_variant
        )

        # Confirmación de éxito
        QMessageBox.information(
            self,
            "Éxito",
            "VM creada correctamente"
        )
        self.close()