import re

class BootManager:

    def decidir_boot(self, xml):
        # Buscamos si de verdad hay una ruta de un archivo .iso montada en el XML
        iso_montado = re.search(r"<source file=['\"]([^'\"]+\.iso)['\"]", xml)
        
        if iso_montado:
            return "iso"
        
        # Si no hay ningún .iso montado, arrancamos desde el disco duro
        return "disk"