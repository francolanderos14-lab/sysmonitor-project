import psutil
import json
import yaml
import requests
import os
import sys
import argparse
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def cargar_config(ruta="config.yaml"):
    """Carga el archivo de configuración YAML."""
    try:
        with open(ruta, "r") as archivo:
            return yaml.safe_load(archivo)
    except FileNotFoundError:
        print(f"Error: no se encontró el archivo de configuración '{ruta}'.")
        sys.exit(1)
    except yaml.YAMLError as error:
        print(f"Error: el archivo de configuración tiene sintaxis inválida: {error}")
        sys.exit(1)

def obtener_metricas():
    """Lee las métricas clave del sistema: CPU, memoria y disco."""
    try:
        cpu = psutil.cpu_percent(interval=1)
        memoria = psutil.virtual_memory().percent
        disco = psutil.disk_usage('/').percent

        return {
            "timestamp": datetime.now().isoformat(),
            "cpu": cpu,
            "memoria": memoria,
            "disco": disco
        }
    except Exception as error:
        print(f"Error al leer métricas del sistema: {error}")
        return None

def evaluar_alerta(metricas, umbrales):
    """Revisa si alguna métrica superó su umbral crítico específico."""
    alertas = []
    for clave in ("cpu", "memoria", "disco"):
        if metricas[clave] >= umbrales[clave]:
            alertas.append(clave)
    return alertas

def enviar_alerta_discord(metricas, alertas):
    """Envía una notificación a Discord vía webhook si hay alertas activas."""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    if not webhook_url:
        print("Advertencia: DISCORD_WEBHOOK_URL no configurada, no se envía alerta.")
        return

    mensaje = {
        "content": (
            f"🚨 **ALERTA SysMonitor** 🚨\n"
            f"Métricas críticas: {', '.join(alertas)}\n"
            f"CPU: {metricas['cpu']}% | Memoria: {metricas['memoria']}% | Disco: {metricas['disco']}%\n"
            f"Timestamp: {metricas['timestamp']}"
        )
    }

    try:
        respuesta = requests.post(webhook_url, json=mensaje, timeout=5)
        respuesta.raise_for_status()
        print("Alerta enviada a Discord correctamente.")
    except requests.exceptions.RequestException as error:
        print(f"Error al enviar alerta a Discord: {error}")

def registrar_log(metricas, alertas, ruta_log):
    """Imprime y guarda el log en formato JSON."""
    entrada = {
        **metricas,
        "alertas": alertas,
        "estado": "CRITICO" if alertas else "OK"
    }
    print(json.dumps(entrada, indent=2))

    try:
        with open(ruta_log, "a") as archivo:
            archivo.write(json.dumps(entrada) + "\n")
    except OSError as error:
        print(f"Error al escribir el log en '{ruta_log}': {error}")

def ejecutar_ciclo():
    """Ejecuta una pasada completa: métricas, evaluación, log y alerta."""
    config = cargar_config()
    metricas = obtener_metricas()

    if metricas is None:
        print("No se pudieron obtener métricas, se aborta este ciclo.")
        return

    alertas = evaluar_alerta(metricas, config["umbrales"])
    registrar_log(metricas, alertas, config["logging"]["ruta"])

    if alertas:
        enviar_alerta_discord(metricas, alertas)

    return config

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SysMonitor: daemon de monitoreo de CPU, memoria y disco."
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Ejecuta una sola pasada de monitoreo y termina."
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Ejecuta en bucle continuo, respetando el intervalo de config.yaml."
    )

    args = parser.parse_args()

    if args.loop:
        print("Iniciando SysMonitor en modo bucle. Ctrl+C para detener.")
        try:
            while True:
                config = ejecutar_ciclo()
                intervalo = config["intervalo_segundos"] if config else 5
                time.sleep(intervalo)
        except KeyboardInterrupt:
            print("\nSysMonitor detenido por el usuario.")
    else:
        # --once o sin flags: comportamiento por defecto es correr una vez
        ejecutar_ciclo()