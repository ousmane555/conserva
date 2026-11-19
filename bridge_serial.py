"""Pont local : Arduino USB série -> Supabase -> application CONSERVA."""

from __future__ import annotations

import argparse
import getpass
import json
import re
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import serial
from serial.tools import list_ports

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.js"
RPC_NAME = "enregistrer_mesure"


def load_config() -> tuple[str, str, int]:
    """Lit les paramètres publics du projet depuis config.js."""
    try:
        text = CONFIG_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Impossible de lire {CONFIG_PATH}: {exc}") from exc

    def value(name: str) -> str:
        match = re.search(rf"\b{name}\s*:\s*['\"]([^'\"]*)['\"]", text)
        return match.group(1).strip() if match else ""

    project_url = value("SUPABASE_URL").rstrip("/")
    api_key = value("SUPABASE_ANON_KEY")
    baud_match = re.search(r"\bSERIAL_BAUD\s*:\s*(\d+)", text)
    baud_rate = int(baud_match.group(1)) if baud_match else 9600

    if not project_url.startswith("https://") or not api_key:
        raise RuntimeError("Renseignez SUPABASE_URL et la clé publishable/anon dans config.js.")
    return project_url, api_key, baud_rate


def choose_port() -> str:
    ports = list(list_ports.comports())
    if not ports:
        raise RuntimeError("Aucun port série détecté. Branchez la carte et vérifiez son pilote USB.")

    print("Ports série détectés :")
    for index, port in enumerate(ports, start=1):
        print(f"  {index}. {port.device} — {port.description}")
    while True:
        answer = input("Choisissez le numéro du port : ").strip()
        try:
            index = int(answer)
            if 1 <= index <= len(ports):
                return ports[index - 1].device
        except ValueError:
            pass
        print("Choix invalide, entrez un numéro de la liste.")


def send_measurement(
    project_url: str,
    api_key: str,
    sensor_key: str,
    temperature: float,
    humidity: float,
) -> None:
    url = f"{project_url}/rest/v1/rpc/{RPC_NAME}"
    body = json.dumps(
        {
            "p_cle": sensor_key,
            "p_temperature": temperature,
            "p_humidite": humidity,
        }
    ).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={"apikey": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=12) as response:
        if response.status not in (200, 201, 204):
            raise RuntimeError(f"Supabase a répondu HTTP {response.status}.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Transmet les mesures série de CONSERVA à Supabase.")
    parser.add_argument("--port", help="Port USB de la carte, par exemple COM5")
    parser.add_argument("--baud", type=int, help="Débit série (par défaut : SERIAL_BAUD de config.js)")
    parser.add_argument("--list-ports", action="store_true", help="Liste les ports série puis quitte")
    args = parser.parse_args()

    if args.list_ports:
        ports = list(list_ports.comports())
        if not ports:
            print("Aucun port série détecté.")
            return 1
        for port in ports:
            print(f"{port.device}\t{port.description}")
        return 0

    try:
        project_url, api_key, configured_baud = load_config()
        port_name = args.port or choose_port()
        baud_rate = args.baud or configured_baud
        sensor_key = getpass.getpass("Clé du capteur Supabase (elle ne sera pas affichée) : ").strip()
        if not sensor_key:
            raise RuntimeError("La clé du capteur est nécessaire. Consultez public.cles_capteurs dans Supabase.")

        print(f"Connexion à {port_name} à {baud_rate} bauds…")
        print("Fermez le Moniteur série Arduino avant de lancer ce pont. Ctrl+C pour arrêter.")
        with serial.Serial(port_name, baud_rate, timeout=1) as device:
            device.reset_input_buffer()
            print("Pont actif : en attente de mesures JSON…")
            while True:
                raw_line = device.readline()
                if not raw_line:
                    continue
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if not isinstance(data, dict):
                        raise ValueError("un objet JSON était attendu")
                    temperature = float(data.get("temperature", data.get("t")))
                    humidity = float(data.get("humidite", data.get("h")))
                    if not -40 <= temperature <= 85 or not 0 <= humidity <= 100:
                        raise ValueError("valeurs hors plage")
                except (json.JSONDecodeError, TypeError, ValueError) as exc:
                    print(f"Ligne ignorée (JSON attendu) : {line!r} ({exc})")
                    continue

                try:
                    send_measurement(project_url, api_key, sensor_key, temperature, humidity)
                    print(f"Envoyé à Supabase : {temperature:.1f} °C, {humidity:.1f} %")
                except HTTPError as exc:
                    details = exc.read().decode("utf-8", errors="replace")
                    print(f"Erreur Supabase HTTP {exc.code} : {details}", file=sys.stderr)
                except (URLError, TimeoutError, OSError) as exc:
                    print(f"Erreur réseau/Supabase : {exc}", file=sys.stderr)
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nPont série arrêté.")
        return 0
    except (RuntimeError, serial.SerialException) as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1
    except EOFError:
        print("\nSaisie interrompue.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
