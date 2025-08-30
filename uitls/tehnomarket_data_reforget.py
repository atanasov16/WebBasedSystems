import re
import json
import pandas as pd
import os
from pathlib import Path


def parse_price(price_str):
    try:
        if pd.isna(price_str):
            return None
        cleaned = str(price_str).replace(' ден.', '').replace(',', '')
        price_float = float(cleaned)
        return price_float
    except (ValueError, AttributeError, TypeError):
        return None


def parse_laptop_name(name):
    if pd.isna(name):
        return {"brand": None, "model": None, "cpu": None, "ram": None,
                "storage": None, "gpu": None, "screen_size": None, "color": None}

    result = {
        "brand": None,
        "model": None,
        "cpu": None,
        "ram": None,
        "storage": None,
        "gpu": None,
        "screen_size": None,
        "color": None
    }

    brand_match = re.search(r'^(APPLE|LENOVO|HP|DELL|ACER|ASUS|SAMSUNG|Microsoft)', name, re.IGNORECASE)
    if brand_match:
        result["brand"] = brand_match.group(1).title()

    cpu_patterns = [
        r'(i[3-9]-\d+[A-Z]*)',  # Intel Core i3-1215U, i5-1334U, etc.
        r'(Ryzen[3-9] \d+[A-Z]*)',  # Ryzen3 7320U, Ryzen5 5500U, etc.
        r'(M[1-4] \d+C CPU)',  # Apple M1, M2, M3, M4
        r'(AMD Ryzen \d)',  # AMD Ryzen 5
        r'(Intel® Core™ i[3-9]-[A-Z0-9]+)'  # Intel® Core™ i3-N305
    ]

    for pattern in cpu_patterns:
        cpu_match = re.search(pattern, name, re.IGNORECASE)
        if cpu_match:
            result["cpu"] = cpu_match.group(1)
            break

    ram_match = re.search(r'(\d+GB)(?:\s*\/|\s*DDR|$)', name, re.IGNORECASE)
    if ram_match:
        result["ram"] = ram_match.group(1)

    storage_match = re.search(r'(\d+GB\s*(?:SSD|HDD)|SSD\s*\d+GB|\d+TB\s*(?:SSD|HDD))', name, re.IGNORECASE)
    if storage_match:
        result["storage"] = storage_match.group(1)
    else:
        storage_fallback = re.search(r'(\d+[GT]B)', name, re.IGNORECASE)
        if storage_fallback:
            result["storage"] = storage_fallback.group(1)

    gpu_patterns = [
        r'(RTX\d+\s*\d+GB)',  # RTX3060 6GB, RTX3050Ti 4GB
        r'(MX\d+\s*\d+GB)',  # MX350 2GB
        r'(Radeon\s*\w+)',  # Radeon 610M, Vega8
        r'(Intel\s*(?:Iris|UHD|HD))',  # Intel Iris XE, Intel UHD
    ]

    for pattern in gpu_patterns:
        gpu_match = re.search(pattern, name, re.IGNORECASE)
        if gpu_match:
            result["gpu"] = gpu_match.group(1)
            break

    screen_match = re.search(r'(\d+(?:\.\d+)?"?)', name)
    if screen_match:
        result["screen_size"] = screen_match.group(1)

    color_keywords = [
        'Grey', 'Gray', 'Black', 'Blue', 'Silver', 'White', 'Red', 'Gold', 'Green',
        'Cloud Grey', 'Slate Grey', 'Terra Cotta', 'Arctic Gray', 'Dark Ash Silver',
        'Midnight', 'Starlight', 'Space Grey', 'Sky Blue', 'Pink', 'Purple', 'Lavender'
    ]

    for color in color_keywords:
        if color.lower() in name.lower():
            result["color"] = color
            break

    if result["brand"]:
        remaining = name[len(result["brand"]):].strip()
        model_candidates = re.split(r'\/|\d+GB|"|\,', remaining)
        if model_candidates:
            result["model"] = model_candidates[0].strip()

    return result


def parse_phone_name(name):
    """
    Parses a Tehnomarket phone name string into its components.
    Tehnomarket phone names are extremely detailed.
    """
    if pd.isna(name):
        return {"brand": None, "model": None, "ram": None, "storage": None, "color": None, "network": None}

    result = {
        "brand": None,
        "model": None,
        "ram": None,
        "storage": None,
        "color": None,
        "network": None
    }

    brand_match = re.search(
        r'^(XIAOMI|SAMSUNG|APPLE|MOTOROLA|HUAWEI|MEANIT|TREVI|BLACKVIEW|DOOGEE|NOKIA|HONOR|GOOGLE|SONY)', name,
        re.IGNORECASE)
    if brand_match:
        result["brand"] = brand_match.group(1).title()

    ram_storage_match = re.search(r'(\d+)\/?\s*(\d+)[GT]B', name, re.IGNORECASE)
    if ram_storage_match:
        result["ram"] = ram_storage_match.group(1) + 'GB'
        result["storage"] = ram_storage_match.group(2) + 'GB'

    color_keywords = [
        'Black', 'White', 'Red', 'Blue', 'Green', 'Gold', 'Silver', 'Gray', 'Grey',
        'Midnight Black', 'Ocean Blue', 'Sandy Gold', 'Forest Green', 'Awesome Lavander',
        'Awesome White', 'Awesome Black', 'Awesome Lime', 'Awesome Pink', 'Awesome Olive',
        'Awesome Graphite', 'Awesome Lightgray', 'Awesome Iceblue', 'Awesome Navy',
        'Starry Blue', 'Sage Green', 'Clover Green', 'Lavender Blue', 'Nebula Green',
        'Mystic Silver', 'Onyx Black', 'Marble Grey', 'Cobalt Violet', 'Amber Yellow',
        'Natural Titanium', 'White Titanium', 'Desert Titanium', 'Black Titanium',
        'Space Grey', 'Starlight', 'Pink', 'Purple', 'Light Blue', 'Light Green',
        'Titanium Black', 'Titanium Gray', 'Titanium White', 'Titanium Silver'
    ]

    for color in color_keywords:
        if color.lower() in name.lower():
            result["color"] = color
            break

    if '5G' in name:
        result["network"] = '5G'
    elif '4G' in name or 'LTE' in name:
        result["network"] = '4G/LTE'

    if result["brand"]:
        remaining = name[len(result["brand"]):].strip()
        if result["color"]:
            remaining = remaining.replace(result["color"], '')
        if result["ram"] and result["storage"]:
            ram_storage_str = f"{result['ram'].replace('GB', '')}/{result['storage']}"
            remaining = remaining.replace(ram_storage_str, '')

        model_match = re.search(r'([A-Za-z0-9\s]+?)(?:\d+[GT]B|$|5G|4G|LTE)', remaining)
        if model_match:
            result["model"] = model_match.group(1).strip()

    return result


def parse_tv_name(name):
    if pd.isna(name):
        return {"brand": None, "model": None, "size": None, "resolution": None, "technology": None,
                "smart_platform": None}

    result = {
        "brand": None,
        "model": None,
        "size": None,
        "resolution": None,
        "technology": None,
        "smart_platform": None
    }

    brand_match = re.search(r'^(SONY|SAMSUNG|PHILIPS|LG|TCL|HISENSE|PANASONIC|SHARP)', name, re.IGNORECASE)
    if brand_match:
        result["brand"] = brand_match.group(1).title()

    size_match = re.search(r'(\d+)"', name)
    if size_match:
        result["size"] = size_match.group(1) + '"'

    resolution_match = re.search(r'(4K|UHD|ULTRA HD|FULL HD|HD|8K)', name, re.IGNORECASE)
    if resolution_match:
        result["resolution"] = resolution_match.group(1).upper()

    if 'OLED' in name.upper():
        result["technology"] = 'OLED'
    elif 'QLED' in name.upper():
        result["technology"] = 'QLED'
    elif 'LED' in name.upper():
        result["technology"] = 'LED'

    if 'ANDROID' in name.upper():
        result["smart_platform"] = 'Android TV'
    elif 'GOOGLE' in name.upper():
        result["smart_platform"] = 'Google TV'
    elif 'WEBOS' in name.upper():
        result["smart_platform"] = 'webOS'
    elif 'TIZEN' in name.upper():
        result["smart_platform"] = 'Tizen'

    model_match = re.search(r'([A-Z]+-[A-Z0-9]+)', name)
    if model_match:
        result["model"] = model_match.group(1)

    return result


def create_product_schema(product_id, category, original_name, price, parsed_data):
    product = {
        "@context": "https://schema.org",
        "@type": "Product",
        "@id": product_id,
        "category": category,
        "name": original_name,
        "offers": {
            "@type": "Offer",
            "price": price,
            "priceCurrency": "MKD",
            "availability": "https://schema.org/InStock"
        }
    }

    if parsed_data.get("brand"):
        product["brand"] = {
            "@type": "Brand",
            "name": parsed_data["brand"]
        }

    if parsed_data.get("model"):
        product["model"] = parsed_data["model"]

    if parsed_data.get("color"):
        product["color"] = parsed_data["color"]

    additional_props = []

    if category == "Laptops":
        properties_map = {
            "cpu": "Processor",
            "ram": "RAM",
            "storage": "Storage",
            "gpu": "Graphics Card",
            "screen_size": "Screen Size"
        }
    elif category == "Smartphones":
        properties_map = {
            "ram": "RAM",
            "storage": "Storage",
            "network": "Network Technology"
        }
    elif category == "Televisions":
        properties_map = {
            "size": "Screen Size",
            "resolution": "Resolution",
            "technology": "Display Technology",
            "smart_platform": "Smart Platform"
        }
    else:
        properties_map = {}

    for key, schema_name in properties_map.items():
        if parsed_data.get(key):
            additional_props.append({
                "@type": "PropertyValue",
                "name": schema_name,
                "value": parsed_data[key]
            })

    if additional_props:
        product["additionalProperty"] = additional_props

    description_parts = []
    if parsed_data.get("brand"):
        description_parts.append(parsed_data["brand"])
    if parsed_data.get("model"):
        description_parts.append(parsed_data["model"])
    if category == "Laptops" and parsed_data.get("cpu"):
        description_parts.append(f"with {parsed_data['cpu']} processor")
    if category == "Smartphones" and parsed_data.get("ram") and parsed_data.get("storage"):
        description_parts.append(f"with {parsed_data['ram']} RAM and {parsed_data['storage']} storage")
    if category == "Televisions" and parsed_data.get("size"):
        description_parts.append(f"{parsed_data['size']} {parsed_data.get('technology', 'display')}")

    if description_parts:
        product["description"] = " ".join(description_parts) + "."

    return product


def process_tehnomarket_data():
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    output_dir = base_dir / "reforged_data"

    output_dir.mkdir(exist_ok=True)

    all_products = []
    product_id_counter = 1

    files_to_process = [
        {"path": data_dir / "tehnomarket_laptops.csv", "category": "Laptops", "parser": parse_laptop_name},
        {"path": data_dir / "tehnomarket_phones.csv", "category": "Smartphones", "parser": parse_phone_name},
        {"path": data_dir / "tehnomarket_tvs.csv", "category": "Televisions", "parser": parse_tv_name},
    ]

    for file_info in files_to_process:
        file_path = file_info["path"]
        category = file_info["category"]
        parser_func = file_info["parser"]

        if not file_path.exists():
            print(f"Warning: {file_path} not found. Skipping.")
            continue

        try:
            print(f"Processing {file_path}...")
            df = pd.read_csv(file_path)

            df = df.dropna(subset=['name'])

            processed_count = 0
            for index, row in df.iterrows():
                price = parse_price(row['price'])

                if price is None:
                    continue

                parsed = parser_func(row['name'])
                product_id = f"tehnomarket-{category.lower()}-{product_id_counter}"
                product_schema = create_product_schema(
                    product_id, category, row['name'], price, parsed
                )
                all_products.append(product_schema)
                product_id_counter += 1
                processed_count += 1

            print(f"  Successfully processed {processed_count} {category.lower()}.")

        except Exception as e:
            print(f"  Error processing {file_path}: {e}")
            import traceback
            traceback.print_exc()

    output_file = output_dir / "tehnomarket_products_structured.jsonld"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_products, f, indent=2, ensure_ascii=False)

    print(f"\nSuccessfully processed {len(all_products)} products total")
    print(f"Output saved to {output_file}")

    return all_products


if __name__ == "__main__":
    process_tehnomarket_data()