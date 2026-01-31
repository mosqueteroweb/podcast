import google.generativeai as genai
import os
import time
import json
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def process_audio(file_path):
    """
    Uploads audio to Gemini, extracts metadata (title, summary, key points),
    and returns a dictionary with the results.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")

    genai.configure(api_key=api_key)

    logging.info(f"Uploading file: {file_path}")
    try:
        myfile = genai.upload_file(file_path)
        logging.info(f"File uploaded: {myfile.name}")

        # Wait for the file to be active
        while myfile.state.name == "PROCESSING":
            logging.info("Processing audio file...")
            time.sleep(2)
            myfile = genai.get_file(myfile.name)

        if myfile.state.name != "ACTIVE":
            raise RuntimeError(f"File upload failed with state: {myfile.state.name}")

        logging.info("File is ACTIVE. Generating content...")

        # Instantiate the model
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Prompt engineering
        prompt = """
        Actúa como un editor de contenidos experto para un podcast.
        Analiza el archivo de audio proporcionado y genera metadatos para su publicación.

        La salida debe ser ESTRICTAMENTE un objeto JSON válido con la siguiente estructura:
        {
          "titular": "Un título atractivo y conciso",
          "resumen": "Un párrafo descriptivo del contenido",
          "puntos_clave": "- Tema 1\n- Tema 2\n- Tema 3\n- Tema 4\n- Tema 5"
        }

        Asegúrate de que 'puntos_clave' sea una cadena de texto con formato de lista de viñetas (bullet points) separados por saltos de línea.
        No incluyas bloques de código markdown (```json ... ```) en la respuesta, solo el JSON crudo.
        """

        result = model.generate_content([myfile, prompt])

        # Clean up: Delete the file from Google's servers
        logging.info("Deleting file from Gemini servers...")
        myfile.delete()

        response_text = result.text.strip()

        # Remove markdown code blocks if present (just in case)
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        response_text = response_text.strip()

        try:
            data = json.loads(response_text)
            logging.info("JSON parsed successfully.")
            return data
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON response: {response_text}")
            raise e

    except Exception as e:
        logging.error(f"An error occurred in Gemini processing: {e}")
        raise e

if __name__ == "__main__":
    # Test block (requires a dummy file)
    pass
