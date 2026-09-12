import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from daemon import evaluar_alerta, cargar_config, enviar_alerta_discord
from unittest.mock import patch, mock_open


def test_sin_alertas_cuando_todo_esta_bajo_el_umbral():
    metricas = {"cpu": 10, "memoria": 20, "disco": 30}
    umbrales = {"cpu": 85, "memoria": 85, "disco": 85}

    resultado = evaluar_alerta(metricas, umbrales)

    assert resultado == []


def test_alerta_cuando_cpu_supera_el_umbral():
    metricas = {"cpu": 90, "memoria": 20, "disco": 30}
    umbrales = {"cpu": 85, "memoria": 85, "disco": 85}

    resultado = evaluar_alerta(metricas, umbrales)

    assert resultado == ["cpu"]


def test_alerta_cuando_varias_metricas_superan_el_umbral():
    metricas = {"cpu": 90, "memoria": 95, "disco": 30}
    umbrales = {"cpu": 85, "memoria": 85, "disco": 85}

    resultado = evaluar_alerta(metricas, umbrales)

    assert resultado == ["cpu", "memoria"]


def test_alerta_en_el_limite_exacto_del_umbral():
    metricas = {"cpu": 85, "memoria": 20, "disco": 30}
    umbrales = {"cpu": 85, "memoria": 85, "disco": 85}

    resultado = evaluar_alerta(metricas, umbrales)

    assert resultado == ["cpu"]


def test_cargar_config_lee_yaml_correctamente():
    contenido_yaml = """
umbrales:
  cpu: 85
  memoria: 85
  disco: 85
logging:
  ruta: "/var/log/sysmonitor/sysmonitor.log"
intervalo_segundos: 5
"""
    with patch("builtins.open", mock_open(read_data=contenido_yaml)):
        config = cargar_config("config_falsa.yaml")

    assert config["umbrales"]["cpu"] == 85
    assert config["logging"]["ruta"] == "/var/log/sysmonitor/sysmonitor.log"
    assert config["intervalo_segundos"] == 5


def test_enviar_alerta_discord_llama_a_requests_post(monkeypatch):
    llamadas = {}

    def fake_post(url, json, timeout):
        llamadas["url"] = url
        llamadas["json"] = json
        llamadas["timeout"] = timeout

        class FakeResponse:
            def raise_for_status(self):
                pass

        return FakeResponse()

    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/fake")
    monkeypatch.setattr("daemon.requests.post", fake_post)

    metricas = {"cpu": 90, "memoria": 20, "disco": 30, "timestamp": "2026-01-01T00:00:00"}
    enviar_alerta_discord(metricas, ["cpu"])

    assert llamadas["url"] == "https://discord.com/api/webhooks/fake"
    assert "cpu" in llamadas["json"]["content"]


def test_enviar_alerta_discord_sin_webhook_configurado(monkeypatch, capsys):
    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)

    metricas = {"cpu": 90, "memoria": 20, "disco": 30, "timestamp": "2026-01-01T00:00:00"}
    enviar_alerta_discord(metricas, ["cpu"])

    salida = capsys.readouterr().out
    assert "no se envía alerta" in salida