import argparse
import sys
import os
import logging
from dotenv import load_dotenv

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gemini_client import process_audio
from ivoox_uploader import upload_episode

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Automatización de Publicación de Podcast con IA")
    parser.add_argument("file_path", nargs="?", help="Ruta al archivo de audio (.mp3)")

    args = parser.parse_args()

    file_path = args.file_path

    # Interactive mode if no argument provided
    if not file_path:
        print("--- Automatización de Podcast ---")
        file_path = input("Por favor, introduce la ruta del archivo de audio (.mp3): ").strip()

    if not file_path:
        logging.error("No se proporcionó archivo. Saliendo.")
        sys.exit(1)

    # Remove quotes if user dragged and dropped file
    file_path = file_path.strip('"').strip("'")

    if not os.path.exists(file_path):
        logging.error(f"El archivo no existe: {file_path}")
        sys.exit(1)

    if not file_path.lower().endswith(".mp3"):
        logging.warning("El archivo no tiene extensión .mp3. Continuando de todos modos...")

    try:
        logging.info("--- Inicio del Proceso ---")

        # Phase C: Gemini Processing
        logging.info("1. Enviando archivo a Gemini para generar metadatos...")
        metadata = process_audio(file_path)

        print("\n--- Metadatos Generados ---")
        print(f"Titular: {metadata.get('titular')}")
        print(f"Resumen: {metadata.get('resumen')}")
        print(f"Puntos Clave:\n{metadata.get('puntos_clave')}")
        print("---------------------------\n")

        # Confirmation (Optional, but good for CLI)
        confirm = input("¿Deseas proceder con la subida a iVoox? (s/n): ").lower()
        if confirm != 's':
            logging.info("Operación cancelada por el usuario.")
            sys.exit(0)

        # Phase D: iVoox Uploading
        logging.info("2. Iniciando automatización de navegador para subida a iVoox...")
        upload_episode(file_path, metadata)

        logging.info("[SUCCESS] ¡Publicación completada con éxito!")

    except Exception as e:
        logging.error(f"Ocurrió un error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
