from bs4 import BeautifulSoup
import base64
from io import BytesIO
from PIL import Image
from custom_filter import apply_filter
import re
from tqdm import tqdm
import random

with open("wordlists/dark_adjs_list.txt", "r", encoding="utf-8") as f:
    dark_adjs = f.read().splitlines()
with open("wordlists/dark_nouns_list.txt", "r", encoding="utf-8") as f:
    dark_nouns = f.read().splitlines()
with open("wordlists/dark_verbs_list.txt", "r", encoding="utf-8") as f:
    dark_verbs = f.read().splitlines()
with open("wordlists/top_english_adjs_lower_10000.txt", "r", encoding="utf-8") as f:
    top_adjs = f.read().splitlines()
with open("wordlists/top_english_nouns_lower_10000.txt", "r", encoding="utf-8") as f:
    top_nouns = f.read().splitlines()
with open("wordlists/top_english_verbs_lower_10000.txt", "r", encoding="utf-8") as f:
    top_verbs = f.read().splitlines()


def do_filter(image):
    width, height = image.size
    return width > 100 and height > 100 and width < 3000 and height < 3000


def process_html_image(html_path, output_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")

    for img_tag in tqdm(soup.find_all("img")):
        data_image = img_tag.get("src")
        if data_image and data_image.startswith("data:image"):
            header, encoded = data_image.split(",", 1)
            image_type = header.split(";")[0].split("/")[1]
            if image_type in ["png", "jpg", "jpeg"]:
                try:
                    decoded = base64.b64decode(encoded)
                    image = Image.open(BytesIO(decoded))
                    if not do_filter(image):
                        continue
                    filtered_image = apply_filter(image)

                    buffered = BytesIO()
                    filtered_image.save(buffered, format=image_type)
                    encoded_filtered = base64.b64encode(buffered.getvalue()).decode()
                    img_tag["src"] = (
                        f"data:image/{image_type};base64,{encoded_filtered}"
                    )
                except Exception as e:
                    print(f"Error processing image: {e}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(str(soup))


def process_html_text(html_path, output_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    soup = BeautifulSoup(html_content, "html.parser")

    for element in tqdm(soup.find_all(text=True)):
        if element.parent.name not in ["script", "style"]:
            if bool(re.search(r"[A-z]", element.string)):
                element.replace_with(_modify_text(element.string))

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(str(soup))


# Change this value to increase or decrease the frequency of word replacement
replacement_frequency = 0.4


def _modify_text(text):
    # split at punctuations and spaces so "word." becomes ["word", "."]
    words = re.findall(r"\w+|\s+|[^\w\s]", text)
    for i, word in enumerate(words):
        # skip unless it matches [A-z]
        if not bool(re.fullmatch(r"[A-z]+", word)):
            continue
        if random.random() > replacement_frequency:
            continue
        if word.lower() in top_adjs:
            words[i] = _match_case(word, random.choice(dark_adjs))
        elif word.lower() in top_nouns:
            words[i] = _match_case(word, random.choice(dark_nouns))
        elif word.lower() in top_verbs:
            words[i] = _match_case(word, random.choice(dark_verbs))
    return "".join(words)


def _match_case(source, target):
    if source.isupper():
        return target.upper()
    elif source[0].isupper():
        return target.capitalize()
    return target


# Change the file names as needed
process_html_text("The Times.html", "text_modified_The Times.html")
process_html_image("text_modified_The Times.html", "modified_The Times.html")

# Albert Einstein - Wikipedia.html
# process_html_text(
#     "Albert Einstein - Wikipedia.html", "text_modified_Albert Einstein - Wikipedia.html"
# )
# process_html_image(
#     "text_modified_Albert Einstein - Wikipedia.html",
#     "modified_Albert Einstein - Wikipedia.html",
# )
