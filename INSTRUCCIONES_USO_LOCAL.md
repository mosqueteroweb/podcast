# Instrucciones de Uso y Configuración

Este proyecto te permite generar feeds de podcast personales a partir de canales de YouTube, alojando los archivos de audio en los "Releases" de tu repositorio de GitHub y el feed RSS en el propio código fuente.

## 1. Configuración Inicial en GitHub

1.  **Hacer Fork / Crear Repositorio:**
    *   Sube estos archivos a un nuevo repositorio en tu cuenta de GitHub.
    *   **Importante:** Asegúrate de que el repositorio sea **PÚBLICO**. Si es privado, AntennaPod no podrá descargar los archivos de audio.

2.  **Activar Permisos de Actions:**
    *   Ve a la pestaña `Settings` del repositorio.
    *   En el menú lateral: `Actions` -> `General`.
    *   En "Workflow permissions", selecciona **"Read and write permissions"**.
    *   Dale a "Save".

## 2. Añadir Canales

1.  Edita el archivo `channels.txt` en el repositorio.
2.  Añade la URL del canal de YouTube que quieras seguir. Una URL por línea.
    *   Ejemplo: `https://www.youtube.com/@NombreDelCanal`
3.  Guarda los cambios (Commit).

## 3. Generación del Podcast

El sistema está configurado para ejecutarse automáticamente **cada 6 horas**.
Sin embargo, puedes forzar la primera ejecución manualmente:

1.  Ve a la pestaña `Actions`.
2.  Selecciona el flujo `Update Podcast Feed` en la lista de la izquierda.
3.  Pulsa el botón `Run workflow`.

Espera unos minutos a que termine. Si todo va bien:
*   Verás un "check" verde.
*   En la pestaña "Code", aparecerá un nuevo archivo XML con el nombre del canal (ej. `NombreDelCanal.xml`).
*   En la sección "Releases" (barra lateral derecha), verás un release llamado "Audio Downloads" con los archivos mp3.

## 4. Suscribirse en AntennaPod

1.  Necesitas la dirección "Raw" del archivo XML generado.
2.  En GitHub, haz clic en el archivo `.xml` que se ha creado.
3.  Haz clic en el botón **"Raw"** (arriba a la derecha del visor de código).
4.  Copia esa URL de la barra de direcciones del navegador.
    *   Será algo como: `https://raw.githubusercontent.com/TuUsuario/TuRepo/main/NombreDelCanal.xml`
5.  Abre AntennaPod en tu móvil.
6.  Ve a "Añadir Podcast" -> "Añadir podcast por URL".
7.  Pega la URL y suscríbete.

## Notas Importantes

*   **Límite de Episodios:** El script mantiene los **5 últimos videos** de cada canal. Los más antiguos se borrarán automáticamente del Release para mantener la limpieza.
*   **Espacio:** GitHub Releases es muy generoso con el espacio, pero el script limpia lo viejo por higiene.
*   **Privacidad:** Recuerda que al ser un repo público, cualquiera que encuentre el enlace podría descargar los audios. Esto está pensado para uso personal.

---

## Plan Técnico Ejecutado

El sistema funciona con los siguientes componentes:

1.  **`src/audio_processor.py`**: Usa `yt-dlp` para descargar el audio de YouTube y convertirlo a MP3.
2.  **`src/feed_generator.py`**: Crea el archivo XML RSS compatible con podcast.
3.  **`src/github_client.py`**: Gestiona la subida y borrado de archivos en GitHub Releases usando la API de GitHub.
4.  **`main.py`**: Coordina todo el proceso (leer canales -> descargar -> subir -> actualizar feed).
5.  **`.github/workflows/update_feed.yml`**: Automatiza la ejecución en la nube de GitHub.
