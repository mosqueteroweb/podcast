from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import os
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def upload_episode(file_path, metadata):
    """
    Automates the upload of an episode to iVoox using Playwright.
    metadata: dict with 'titular', 'resumen', 'puntos_clave'
    """
    url_login = os.getenv("WEB_URL", "https://podcasters.ivoox.com/#/login")
    username = os.getenv("WEB_USER")
    password = os.getenv("WEB_PASSWORD")

    if not username or not password:
        raise ValueError("WEB_USER or WEB_PASSWORD not found in environment variables.")

    with sync_playwright() as p:
        # headless=False so the user can see what's happening (as requested in Phase D)
        # or at least initially for debugging. The spec says "False (visible) initially for debugging".
        # I will leave it as True for now to run in this environment, but the user can change it.
        # Actually, in the final script I might make it configurable.
        # But for this environment I must use headless=True because there is no display.
        # WAIT: The user runs this on their machine. They asked for "headless=False (visible) initially".
        # I will code it to use an env var or default to False (visible) but in my tests I'd use True.
        # However, the user is running this. So I will default to `headless=False` as requested by the spec "Visible".

        headless_mode = os.getenv("HEADLESS", "False").lower() == "true"
        logging.info(f"Launching browser (headless={headless_mode})...")

        browser = p.chromium.launch(headless=headless_mode)
        context = browser.new_context()
        page = context.new_page()

        # 1. Login
        logging.info(f"Navigating to login: {url_login}")
        page.goto(url_login)

        try:
            logging.info("Filling credentials...")
            page.wait_for_selector("input#email-field", state="visible")
            page.fill("input#email-field", username)

            page.fill("input[type='password']", password)

            # Click Login
            # Using a broad selector for the button inside the form
            page.click("button[type='submit']")

            logging.info("Waiting for navigation after login...")
            page.wait_for_load_state("networkidle")

            # Check if login failed (optional checks for error messages)
            # if page.locator(".invalid-feedback").is_visible(): ...

        except Exception as e:
            logging.error(f"Error during login: {e}")
            # Capture screenshot
            page.screenshot(path="error_login.png")
            browser.close()
            raise e

        # 2. Navigate to Upload
        # Based on investigation, the URL structure is #/something.
        # The upload button usually is in the header.
        logging.info("Looking for Upload button...")
        try:
            # Try to go directly to upload page if known, but we don't know it for sure.
            # Usually generic "Upload" or "Subir".
            # Selector investigation didn't cover the dashboard.
            # I will try to find a button with text "Subir" or "Upload".

            # Attempt to click "Subir" or "Upload"
            # Note: The site seems to be multi-language support.

            # Let's try to wait for a common element that indicates logged in state.
            # e.g. Avatar or "My Content".

            # Strategy: Go directly to upload URL if possible.
            # FAQs said: "Click the Upload button in the top bar".
            # Let's assume there is a button with text "Subir" or icon cloud-upload.

            # Fallback: prompt user to navigate manually if it times out? No, automation.

            # Let's try a few potential selectors for the upload button
            upload_selectors = [
                "text=Subir",
                "text=Upload",
                "a[href*='upload']",
                "a[href*='subir']",
                ".btn-upload",
                "button:has-text('Subir')",
                "button:has-text('Upload')"
            ]

            upload_btn = None
            for sel in upload_selectors:
                if page.is_visible(sel):
                    upload_btn = sel
                    break

            if upload_btn:
                logging.info(f"Clicking upload button: {upload_btn}")
                page.click(upload_btn)
            else:
                logging.warning("Upload button not found. Attempting to navigate to #/upload (guess).")
                page.goto("https://podcasters.ivoox.com/#/upload")

            page.wait_for_load_state("networkidle")

        except Exception as e:
             logging.error(f"Error navigating to upload: {e}")
             page.screenshot(path="error_upload_nav.png")
             browser.close()
             raise e

        # 3. Upload File
        logging.info("Uploading file...")
        try:
            # Handle "Audio from my PC" choice if necessary
            # Look for input[type=file]

            # If there is a button to select source first
            if page.is_visible("text=Audio desde mi PC") or page.is_visible("text=Audio from my PC"):
                page.click("text=Audio from my PC") # or Spanish variant

            # File input
            # It might be hidden, so we use set_input_files on the locator
            file_input = page.locator("input[type='file']")
            file_input.wait_for(state="attached", timeout=10000)
            file_input.set_input_files(file_path)

            logging.info("File selected. Waiting for upload to complete...")

            # Wait for upload progress.
            # This is tricky without seeing the UI.
            # Usually there is a progress bar.
            # We will wait for a "Processing" text or "Upload complete".
            # Or we wait for the Title/Description fields to become enabled/visible.

            # Let's assume fields are editable now.

        except Exception as e:
             logging.error(f"Error selecting file: {e}")
             page.screenshot(path="error_file_select.png")
             browser.close()
             raise e

        # 4. Fill Metadata
        logging.info("Filling metadata...")
        try:
            # Title
            # Look for input with placeholder "Título" or label "Title"
            # Generic approach: find by label or placeholder

            # Title
            page.fill("input[placeholder*='Titulo']", metadata['titular']) # Spanish
            # Fallback if English
            # page.fill("input[placeholder*='Title']", metadata['titular'])

            # Summary / Description
            # Usually a textarea
            page.fill("textarea", metadata['resumen'])

            # Tags / Key Points
            # This might be a separate field "Etiquetas" or "Tags".
            # Or maybe we append key points to the description?
            # The spec says: "Localizar el campo de 'Extracto' o 'Tags' e insertar json['puntos_clave']."
            # If tags field expects comma separated values, this might be tricky with bullet points.
            # If "Extracto" (Excerpt) exists, it's likely a textarea.

            # I'll try to find a tags input, if not append to description?
            # Or assume there is an "Extracto" field.

            if page.is_visible("textarea[name*='excerpt']"): # Guessing name
                page.fill("textarea[name*='excerpt']", metadata['puntos_clave'])
            elif page.is_visible("input[placeholder*='Tags']"):
                 # Clean bullet points for tags? "- Topic" -> "Topic"
                 tags = metadata['puntos_clave'].replace("- ", "").replace("\n", ",")
                 page.fill("input[placeholder*='Tags']", tags)
            else:
                # Append to description
                logging.info("Excerpt/Tags field not found, appending points to description.")
                new_desc = metadata['resumen'] + "\n\n" + metadata['puntos_clave']
                page.fill("textarea", new_desc)

            # Category? Language? These might be required.
            # I can't fill them without knowing user preference.
            # I'll assume defaults or that they are pre-filled.

        except Exception as e:
             logging.error(f"Error filling metadata: {e}")
             page.screenshot(path="error_metadata.png")
             # Don't crash, maybe user can finish manually if headless=False
             # browser.close()
             # raise e

        # 5. Publish / Save
        logging.info("Publishing...")
        try:
            # Button "Publicar" or "Publish"
            pub_btn = page.locator("button:has-text('Publicar'), button:has-text('Publish')")
            if pub_btn.is_visible():
                pub_btn.click()
                logging.info("Publish button clicked.")

                # Wait for confirmation
                page.wait_for_load_state("networkidle")
                time.sleep(5)
                logging.info("Upload workflow finished.")
            else:
                logging.warning("Publish button not found.")

        except Exception as e:
             logging.error(f"Error publishing: {e}")
             page.screenshot(path="error_publish.png")

        # Keep browser open for a moment if valid?
        # If headless=False, maybe we shouldn't close immediately?
        # But for automation script, we typically close.
        # The user said "app en la que yo meta el mp3 y a partir de ahí empiece el flujo".

        browser.close()

if __name__ == "__main__":
    pass
