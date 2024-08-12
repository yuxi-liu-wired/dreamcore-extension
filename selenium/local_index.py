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
from bs4 import BeautifulSoup
import urllib.parse


def do_filter(image):
    width, height = image.size
    return width > 100 and height > 100 and width < 3000 and height < 3000


def get_image_url(img_src):
    if img_src.startswith("data:image"):
        return img_src
    parsed_url = urllib.parse.urlparse(img_src)
    return parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path


def process_image(img_src, counter):
    try:
        print(f"Processing image: {img_src}")

        # Skip SVG files
        if img_src.lower().endswith(".svg"):
            print("Skipping SVG file")
            return None

        # Download image with a user-agent header
        if img_src.startswith("data:image"):
            # Extract the base64 image data
            img_str = img_src.split(",")[-1]
            # Decode the base64 image data
            img_data = base64.b64decode(img_str)
            # Open the image
            image = Image.open(io.BytesIO(img_data))
        else:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(img_src, headers=headers)

            # Check if the response is successful
            if response.status_code != 200:
                print(f"Failed to download image. Status code: {response.status_code}")
                return None

            # Try to open the image
            try:
                image = Image.open(io.BytesIO(response.content))
            except Exception as e:
                print(f"Failed to open image: {str(e)}")
                return None

        if do_filter(image):
            filtered_image = apply_filter(image)
        else:
            print(f"Image {image.size} is too small or too large, skipping filter")
            return None
        # Save images
        original_image_path = os.path.join("output", f"original_{counter}.png")
        image.save(original_image_path)
        print(f"Saved original image to: {original_image_path}")
        modified_image_path = os.path.join("output", f"modified_{counter}.png")
        filtered_image.save(modified_image_path)
        print(f"Saved modified image to: {modified_image_path}")

        # Convert filtered image to base64
        buffered = io.BytesIO()
        filtered_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"

    except Exception as e:
        print(f"Error processing image: {str(e)}")
        traceback.print_exc()
        return None


# Set up the WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

# Load a website
# source_url = "https://en.wikipedia.org/wiki/Albert_Einstein"
source_url = "https://www.thetimes.com/"
driver.get(source_url)

# Wait for the page to load
wait = WebDriverWait(driver, 10)
wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

# Get the page source and parse it with BeautifulSoup
page_source = driver.page_source
soup = BeautifulSoup(page_source, "html.parser")

# Create an output directory if it doesn't exist
os.makedirs("output", exist_ok=True)

# for counter, img in enumerate(soup.find_all("img")):
#     unparsed_src = img.get("src")
#     if unparsed_src:
#         original_src = urllib.parse.urljoin(source_url, unparsed_src)
#     elif unparsed_src[:4] == "data":
#         original_src = unparsed_src
#     if original_src:
#         new_src = process_image(original_src, counter)
#         if new_src:
#             # Create a new img tag with only essential attributes
#             new_img = soup.new_tag("img")
#             new_img["src"] = new_src
#             if img.get("width", "") != "":
#                 new_img["width"] = img.get("width", "")
#             if img.get("height", "") != "":
#                 new_img["height"] = img.get("height", "")
#             img.replace_with(new_img)

# Update the page with the modified HTML
# driver.execute_script(
#     f"document.body.innerHTML = '{soup.body.encode_contents().decode()}'"
# )


for counter, img in enumerate(soup.find_all("img")):
    unparsed_src = img.get("src")
    print(f"Processing image: {unparsed_src}")
    unparsed_data_src = img.get("data-src")

    if unparsed_src and not unparsed_src.startswith("data:"):
        original_src = urllib.parse.urljoin(source_url, unparsed_src)
        new_src = process_image(original_src, counter)
        if new_src:
            # Update the image source using JavaScript
            print(f"var img = document.querySelector('img[src^=''{unparsed_src}'']');")
            script = f"""
            var img = document.querySelector('img[src^="{unparsed_src}"]');
            if (img) {{
                img.src = '{new_src}';
                if (img.hasAttribute('width')) {{img.width = img.getAttribute('width');}}
                if (img.hasAttribute('height')) {{img.height = img.getAttribute('height');}}
                // Remove all attributes except src, width, and height
                for (var i = img.attributes.length - 1; i >= 0; i--) {{
                    var attrib = img.attributes[i];
                    if (attrib.name !== 'src' && attrib.name !== 'width' && attrib.name !== 'height') {{
                        img.removeAttribute(attrib.name);
                    }}
                }}
            }}
            """
            driver.execute_script(script)

# Keep the browser open
input("Press Enter to close the browser...")
driver.quit()
