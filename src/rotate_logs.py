import os
import shutil
from datetime import datetime

RUTA_LOG = "/var/log/sysmonitor/sysmonitor.log"
CARPETA_ARCHIVO = "/var/log/sysmonitor/archivo"

def rotar_log():
    """Archiva el log actual con timestamp y crea uno nuevo vacío."""
    if not os.path.exists(RUTA_LOG):
        print(f"No existe {RUTA_LOG}, nada que rotar.")
        return

    if os.path.getsize(RUTA_LOG) == 0:
        print("El log está vacío, no hace falta rotar.")
        return

    os.makedirs(CARPETA_ARCHIVO, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = os.path.join(CARPETA_ARCHIVO, f"sysmonitor_{timestamp}.log")

    shutil.move(RUTA_LOG, destino)

    # Crear un archivo de log nuevo, vacío
    open(RUTA_LOG, "a").close()

    print(f"Log rotado correctamente: {destino}")

if __name__ == "__main__":
    rotar_log()