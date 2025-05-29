import csv
import re
import os
import sys
import requests
from requests.adapters import HTTPAdapter, Retry

def smart_capitalize(word):
    return word if word and word[0].isupper() else word.capitalize()

def capitalize_title(first, last, model):
    first_clean = first.strip().capitalize()
    last_clean = ' '.join([part.capitalize() for part in last.strip().split()])
    model_clean = ' '.join([smart_capitalize(part) for part in model.strip().split()])
    return f"{first_clean} {last_clean} {model_clean}"

def capitalize_after_dash(match):
    prefix = match.group(1)
    suffix = match.group(2).upper()
    return prefix + suffix

def normalize_code(text):
    text = re.sub(r'\b"\b', '', text)
    text = re.sub(r'\b  \b', ' ', text)
    text = re.sub(r'\b[cC][jJ]-?', 'CJ-', text)
    text = re.sub(r'\b[dD][jJ]-?', 'DJ-', text)
    text = re.sub(r'\b[fF][cC]-?', 'FC-', text)
    text = re.sub(r'\b(CJ-|DJ-|FC-)([^\s]*)', capitalize_after_dash, text)
    return text

def safe_filename(name):
    return re.sub(r'[^a-zA-Z0-9 _\-]', '', name).strip()

def format_address(street1, street2, city, state, country):
    address_parts = [p.strip() for p in street1.split(',') if p.strip()]
    city_included = any(city.lower() in part.lower() for part in address_parts)
    state_included = any(state.lower() in part.lower() for part in address_parts)

    address_lines = []

    if address_parts:
        address_lines.append(address_parts[0])
    elif street1.strip():
        address_lines.append(street1.strip())

    if not city_included or not state_included:
        line2_parts = []
        if not city_included and city:
            line2_parts.append(city)
        if not state_included and state:
            line2_parts.append(state)
        if line2_parts:
            address_lines.append(', '.join(line2_parts))

    if country:
        address_lines.append(country)

    return '\n'.join(address_lines)

file_exts = (
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.svg', '.webp', '.heic', '.ico',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp', '.rtf', '.txt', '.md', '.csv', '.epub', '.pages',
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.tgz', '.lz', '.iso',
    '.mp4', '.mov', '.avi', '.wmv', '.flv', '.mkv', '.webm', '.mpeg', '.mpg', '.3gp', '.vob',
)

session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504, 522, 524])
adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)
session.mount("http://", adapter)

def download_file(url, save_path):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        with session.get(url, headers=headers, stream=True, timeout=(10, 20)) as response:
            response.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        print(f"Downloaded: {url}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed for {url}: {e}")
    except Exception as e:
        print(f"Unexpected error downloading {url}: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <csv_file>")
        sys.exit(1)

    csv_filename = sys.argv[1]

    if not os.path.isfile(csv_filename):
        print(f"File not found: {csv_filename}")
        sys.exit(1)

    # Get the base directory of the input CSV
    base_dir = os.path.dirname(os.path.abspath(csv_filename))

    with open(csv_filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)

        for index, row in enumerate(reader, start=1):
            if len(row) < 11:
                continue

            cleaned = [normalize_code(field.replace('"', '').replace('  ', ' ')) for field in row]

            first, last, model = cleaned[0], cleaned[1], cleaned[10]
            street1, street2 = cleaned[2], cleaned[3]
            city, state, country = cleaned[4], cleaned[5], cleaned[7]
            email, phone = cleaned[8], cleaned[9]
            comments = cleaned[11] if len(cleaned) > 11 else ''

            folder_name = os.path.join(base_dir, safe_filename(capitalize_title(first, last, model)))
            os.makedirs(folder_name, exist_ok=True)

            address_block = format_address(street1, street2, city, state, country)

            content = f"""
---------------------------------------------------------------------------------------
Address: 
{address_block}

Email: {email}

Telephone: {phone}

Story:
{comments}

---------------------------------------------------------------------------------------
"""
            txt_filename = os.path.join(folder_name, f"{safe_filename(capitalize_title(first, last, model))}.txt")
            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Created file: {txt_filename}")

            file_fields = [f for f in cleaned if any(f.lower().endswith(ext) for ext in file_exts)]
            for i, url in enumerate(file_fields, start=1):
                ext = os.path.splitext(url)[-1]
                save_name = f"{safe_filename(capitalize_title(first, last, model))} {i}{ext}"
                save_path = os.path.join(folder_name, save_name)

                download_file(url, save_path)

if __name__ == "__main__":
    main()
