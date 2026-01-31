# Automatización de Podcast con iVoox y Gemini

Este proyecto automatiza la generación de metadatos (título, resumen, puntos clave) utilizando Google Gemini y la subida de episodios a iVoox mediante Playwright.

## Requisitos

1.  Python 3.8+
2.  Una cuenta de Google Cloud con API Key habilitada para Gemini.
3.  Una cuenta en iVoox Podcasters.

## Instalación

1.  Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    playwright install chromium
    ```

2.  Configura las variables de entorno:
    *   Copia el archivo `.env.template` a `.env`.
    *   Edita `.env` y rellena tus credenciales:
        ```ini
        GOOGLE_API_KEY=tu_api_key_de_google
        WEB_USER=tu_email_ivoox
        WEB_PASSWORD=tu_password_ivoox
        HEADLESS=False  # Cambia a True para ocultar el navegador
        ```

## Uso

Ejecuta el script principal proporcionando la ruta a tu archivo MP3:

```bash
python main.py ruta/a/tu/episodio.mp3
```

O simplemente ejecuta el script y sigue las instrucciones en pantalla:

```bash
python main.py
```

## Funcionamiento

1.  **Análisis con IA**: El script sube el audio a Gemini, que analiza el contenido y genera un título atractivo, un resumen y puntos clave.
2.  **Revisión**: Se mostrarán los metadatos en la consola.
3.  **Subida a iVoox**: Si confirmas, se abrirá un navegador automatizado que iniciará sesión en iVoox, subirá el archivo y rellenará los campos con la información generada.

## Solución de Problemas

*   **Selectores no encontrados**: Si iVoox cambia su diseño, es posible que los selectores CSS en `src/ivoox_uploader.py` necesiten actualización.
*   **Errores de Login**: Si tienes activada la autenticación en dos pasos o aparece un CAPTCHA, el script puede fallar. Revisa las capturas de pantalla de error generadas en la carpeta raíz (`error_login.png`, etc.).
