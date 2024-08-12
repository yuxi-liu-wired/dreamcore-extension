from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import requests
import io
import base64
from custom_filter import apply_filter
import traceback
import os


def process_image(img, counter):
    try:
        # Get image source
        src = img.get_attribute("src")
        print(f"Processing image: {src}")

        # Skip SVG files
        if src.lower().endswith(".svg"):
            print("Skipping SVG file")
            return

        # Download image with a user-agent header
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(src, headers=headers)

        # Check if the response is successful
        if response.status_code != 200:
            print(f"Failed to download image. Status code: {response.status_code}")
            return

        # Try to open the image
        try:
            image = Image.open(io.BytesIO(response.content))
        except Exception as e:
            print(f"Failed to open image: {str(e)}")
            return

        # Save the original image
        original_image_path = os.path.join("output", f"original_{counter}.png")
        image.save(original_image_path)
        print(f"Saved original image to: {original_image_path}")

        filtered_image = apply_filter(image)

        # Save the modified image
        modified_image_path = os.path.join("output", f"modified_{counter}.png")
        filtered_image.save(modified_image_path)
        print(f"Saved modified image to: {modified_image_path}")

        # Convert filtered image to base64
        buffered = io.BytesIO()
        filtered_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        # Replace image source with filtered version
        driver.execute_script(
            "arguments[0].src = 'data:image/png;base64," + img_str + "'", img
        )
        print("Successfully processed and replaced image")

    except Exception as e:
        print(f"Error processing image: {str(e)}")
        traceback.print_exc()


# Set up the WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

# Load a website
driver.get("https://en.wikipedia.org/wiki/Albert_Einstein")

# Wait for all images to be present in the DOM
wait = WebDriverWait(driver, 10)  # Adjust timeout as needed
images = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "img")))

# Create an output directory if it doesn't exist
os.makedirs("output", exist_ok=True)

# Process each image
for counter, img in enumerate(images):
    process_image(img, counter)

# Keep the browser open
input("Press Enter to close the browser...")
driver.quit()
