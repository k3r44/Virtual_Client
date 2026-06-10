import libvirt
import subprocess
import psutil
import os
import re  # 🔥 Agregado para el hachazo del XML
import xml.etree.ElementTree as ET

class LibvirtManager:

    def __init__(self):

        self.conn = libvirt.open("qemu:///system")

        if self.conn is None:
            raise Exception("No se pudo conectar con libvirt")

    def listar_vms(self):

        domains = self.conn.listAllDomains()

        estados = {
            libvirt.VIR_DOMAIN_RUNNING: "Encendida",
            libvirt.VIR_DOMAIN_SHUTOFF: "Apagada",
            libvirt.VIR_DOMAIN_PAUSED: "Pausada",
        }

        vms = []

        for domain in domains:

            estado, _ = domain.state()
            xml = domain.XMLDesc()

            ram = re.search(r"<memory.*?>(\d+)</memory>", xml)
            vcpu = re.search(r"<vcpu.*?>(\d+)</vcpu>", xml)
            
            # ==========================================
            # LECTURA DEL DISCO (Tamaño real en GB)
            # ==========================================
            disk_match = re.search(r"file='(.*\.qcow2|.*\.img|.*\.vmdk)'", xml)
            tamano_disco = "N/A"
            
            if disk_match:
                ruta_disco = disk_match.group(1)
                try:
                    # blockInfo devuelve (capacidad, reserva, fisico) en bytes
                    info_disco = domain.blockInfo(ruta_disco)
                    # Convertimos de bytes a Gigabytes
                    tamano_disco = int(info_disco[0] / (1024**3))
                except Exception:
                    tamano_disco = "Desconocido"
            
            # ==========================================
            # LECTURA DEL ISO (Real o Histórico)
            # ==========================================
            iso_val = "Sin ISO"
            
            # 1. Intentamos leer un CD real conectado
            iso_match = re.search(r"<source file=['\"]([^'\"]+\.iso)['\"]", xml)
            if iso_match:
                iso_val = iso_match.group(1)
            else:
                # 2. Si no hay CD, leemos nuestra memoria inyectada
                desc_match = re.search(r"<description>ISO_ORIGINAL:(.*?)</description>", xml)
                if desc_match:
                    iso_val = desc_match.group(1)

            vms.append({
                "nombre": domain.name(),
                "estado": estados.get(estado, "Desconocido"),
                "ram": int(ram.group(1)) // 1024 if ram else "N/A",
                "cpu": int(vcpu.group(1)) if vcpu else "N/A",
                "disco": tamano_disco, 
                "iso": iso_val, 
            })

        return vms

    def iniciar_vm(self, nombre):

        domain = self.conn.lookupByName(nombre)

        if not domain.isActive():
            print(f"[{nombre}] Modificando XML para expulsar ISO y arrancar del disco...")
            
            # 🪓 EL HACHAZO AL XML 🪓
            xml_actual = domain.XMLDesc(0)
            
            # 1. Vaciamos la lectora de CD (borramos la ruta del archivo .iso)
            xml_limpio = re.sub(r"<source file=['\"][^'\"]+\.iso['\"]/?>", "", xml_actual)
            
            # 2. Quitamos la prioridad de boot por CD si existe
            xml_limpio = re.sub(r"<boot dev='cdrom'/>\s*", "", xml_limpio)
            
            # 3. Guardamos la configuración de forma permanente en libvirt
            self.conn.defineXML(xml_limpio)
            
            # Refrescamos el objeto domain con los nuevos cambios
            domain = self.conn.lookupByName(nombre)
            
            # ¡Ahora sí, enciende!
            domain.create()
            print(f"[{nombre}] Encendida y booteando desde DISCO.")
        else:
            print(f"[{nombre}] Ya estaba encendida. Conectando...")

        # abrir viewer
        subprocess.Popen([
            "virt-viewer",
            "--attach",
            nombre,
            "--wait"
        ])

    def apagar_vm(self, nombre):

        domain = self.conn.lookupByName(nombre)

        if not domain.isActive():
            print("La VM ya está apagada")
            return

        domain.shutdown()

        print(f"{nombre} apagada correctamente")

    def obtener_recursos_host(self):

        ram_total_gb = round(
            psutil.virtual_memory().total / (1024 ** 3),
            2
        )

        cpus_totales = psutil.cpu_count()

        ram_maxima_gb = ram_total_gb * 0.5

        cpus_maximas = max(1, cpus_totales // 2)

        return {
            "ram_total": ram_total_gb,
            "cpus_totales": cpus_totales,
            "ram_maxima": ram_maxima_gb,
            "cpus_maximas": cpus_maximas
        }

    def forzar_apagado(self, nombre):

        domain = self.conn.lookupByName(nombre)

        if not domain.isActive():

            print("La VM ya está apagada")
            return

        domain.destroy()

        print(f"{nombre} apagada forzosamente")

    def crear_vm(
        self,
        nombre,
        ram,
        vcpus,
        disco,
        iso_path,
        os_variant
    ):

        comando = [
            "virt-install",
            "--name", nombre,
            "--memory", str(ram),
            "--vcpus", str(vcpus),
            "--disk", f"size={disco}",
            "--cdrom", iso_path,
            "--os-variant", os_variant,
            "--graphics", "spice",
            "--network", "default",
            "--noautoconsole"
        ]

        resultado = subprocess.run(comando)

        if resultado.returncode != 0:
            print("Error al crear VM")
            return

        # ==========================================
        # 🔥 TRUCO MÁGICO: Inyectar la descripción en el XML
        # ==========================================
        try:
            domain = self.conn.lookupByName(nombre)
            # Primero leemos el XML actual
            xml = domain.XMLDesc(0) 
            
            tree = ET.fromstring(xml)
            
            # Creamos una nueva etiqueta <description> con la ruta del ISO
            desc_element = ET.Element("description")
            desc_element.text = f"ISO_ORIGINAL:{iso_path}"
            
            # Insertamos la descripción justo al principio del XML (dentro de <domain>)
            tree.insert(0, desc_element)
            
            # Convertimos de nuevo a texto y guardamos los cambios en libvirt
            nuevo_xml = ET.tostring(tree, encoding="unicode")
            self.conn.defineXML(nuevo_xml)
            print(f"Metadatos inyectados correctamente a {nombre}")
            
        except Exception as e:
            print(f"Error inyectando metadatos: {e}")
        # ==========================================

        subprocess.Popen([
            "virt-viewer",
            "--attach",
            nombre
        ])

        print(f"VM {nombre} creada correctamente")

    def tiene_sistema_instalado(self, nombre):
        try:
            domain = self.conn.lookupByName(nombre)
            xml = domain.XMLDesc()

            # si tiene disco y no tiene cdrom activo, asumimos instalado
            if "<disk type='file'" in xml and "<cdrom" not in xml:
                return True

            return False

        except Exception as e:
            print(f"Error verificando boot: {e}")
            return False
    
    def eliminar_vm(self, nombre):

        try:
            domain = self.conn.lookupByName(nombre)

            print(f"Eliminando VM: {nombre}")

            # 1. Apagar si está activa
            if domain.isActive():
                domain.destroy()

            # 2. Obtener XML
            xml = domain.XMLDesc()
            tree = ET.fromstring(xml)

            disk_paths = []

            # 3. Extraer discos
            for disk in tree.findall(".//disk"):

                source = disk.find("source")

                if source is not None and "file" in source.attrib:

                    path = source.attrib["file"]

                    disk_paths.append(path)

            # 4. Eliminar VM del hypervisor
            domain.undefine()

            print(f"VM {nombre} eliminada de libvirt")

            # 5. BORRADO SEGURO DE DISCOS
            for path in disk_paths:

                try:

                    # 🔥 PROTECCIÓN 1: evitar rutas peligrosas
                    if not path:
                        print("Ruta vacía, ignorada")
                        continue

                    # 🔥 PROTECCIÓN 2: solo discos dentro de libvirt
                    if "/var/lib/libvirt/images" not in path:
                        print(f"⚠️ Disco fuera de zona segura, omitido: {path}")
                        continue

                    # 🔥 PROTECCIÓN 3: evitar borrar ISO
                    if path.endswith(".iso"):
                        print(f"⚠️ ISO ignorada (no se borra): {path}")
                        continue

                    # 🔥 BORRADO REAL
                    if os.path.exists(path):
                        os.remove(path)
                        print(f"Disco eliminado: {path}")
                    else:
                        print(f"Disco no encontrado: {path}")

                except Exception as e:
                    print(f"Error eliminando disco {path}: {e}")

            print(f"VM {nombre} eliminada completamente")

        except libvirt.libvirtError:
            print(f"La VM {nombre} no existe")

        except Exception as e:
            print(f"Error eliminando VM: {e}")

    def limpiar_discos_huerfanos(self):

        usados = set()

        # 1. detectar discos usados por VMs
        for dom in self.conn.listAllDomains():

            xml = dom.XMLDesc()
            tree = ET.fromstring(xml)

            for disk in tree.findall(".//disk"):
                source = disk.find("source")

                if source is not None and "file" in source.attrib:
                    usados.add(source.attrib["file"])

        # 2. recorrer TODOS los pools (no solo default)
        pools = self.conn.listAllStoragePools()

        for pool in pools:

            pool.refresh()

            try:
                for vol in pool.listAllVolumes():

                    path = vol.path()

                    # seguridad: solo qcow2 (discos de VM)
                    if path.endswith(".qcow2") and path not in usados:

                        print(f"🧹 Eliminando huérfano: {path}")
                        vol.delete()

            except Exception as e:
                print(f"Error en pool {pool.name()}: {e}")