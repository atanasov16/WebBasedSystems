import re
import json
import pandas as pd
import os
from pathlib import Path


def parse_price(price_str):
    try:
        if pd.isna(price_str) or price_str == 'N/A':
            return None
        cleaned = str(price_str).replace('.', '')
        price_float = float(cleaned)
        return price_float
    except (ValueError, AttributeError, TypeError):
        return None


def parse_laptop_name(name):
    if pd.isna(name) or name == 'N/A':
        return {"brand": None, "model": None, "cpu": None, "ram": None,
                "storage": None, "screen_size": None}

    name_clean = name.replace('Лаптоп ', '').strip()

    brand_match = re.search(r'^([A-Za-z]+)', name_clean)
    if not brand_match:
        return {"brand": None, "model": None, "cpu": None, "ram": None,
                "storage": None, "screen_size": None}

    brand = brand_match.group(1).strip()

    spec_pattern = r'([A-Za-z0-9\-]+)\/([A-Za-z0-9]+)\/([A-Za-z0-9]+)'
    spec_match = re.search(spec_pattern, name_clean)

    if spec_match:
        cpu = spec_match.group(1).strip()
        ram = spec_match.group(2).strip()
        storage = spec_match.group(3).strip()

        model_part = name_clean[:spec_match.start()].replace(brand, '').strip()
    else:
        cpu_pattern = r'(i[3-9]-\d+[A-Z]*|R[3-9]-\d+[A-Z]*)'
        cpu_match = re.search(cpu_pattern, name_clean)
        cpu = cpu_match.group(1) if cpu_match else None
        ram = None
        storage = None
        model_part = name_clean.replace(brand, '').strip()

    screen_size_match = re.search(r'(\d+(?:\.\d+)?)"', name_clean)
    screen_size = screen_size_match.group(1) + '"' if screen_size_match else None

    return {
        "brand": brand,
        "model": model_part,
        "cpu": cpu,
        "ram": ram,
        "storage": storage,
        "screen_size": screen_size
    }

def parse_phone_name(name):
    if pd.isna(name) or name == 'N/A':
        return {"brand": None, "model": None, "ram": None, "storage": None, "color": None}

    brand_match = re.search(r'^([A-Za-z]+)', name)
    if not brand_match:
        return {"brand": None, "model": None, "ram": None, "storage": None, "color": None}

    brand = brand_match.group(1).strip()

    ram_storage_pattern = r'(\d+)\+(\d+)[A-Za-z]*B'
    ram_storage_match = re.search(ram_storage_pattern, name)

    if ram_storage_match:
        ram = ram_storage_match.group(1) + 'GB'
        storage = ram_storage_match.group(2) + 'GB'

        model_part = name[:ram_storage_match.start()].replace(brand, '').strip()
    else:
        ram = None
        storage = None
        model_part = name.replace(brand, '').strip()

    color_keywords = ['Black', 'Blue', 'Gold', 'Green', 'Silver', 'White', 'Cyan', 'Sandy Gold',
                      'Midnight Black', 'Starry Blue', 'Sage Green', 'Forest Green', 'Ocean Blue']
    color = None
    for keyword in color_keywords:
        if keyword in name:
            color = keyword
            break

    return {
        "brand": brand,
        "model": model_part,
        "ram": ram,
        "storage": storage,
        "color": color
    }


def parse_tv_name(name):
    if pd.isna(name) or name == 'N/A':
        return {"brand": None, "model": None, "size": None, "resolution": None, "features": None}


    size_match = re.search(r'(\d+)"', name)
    size = size_match.group(1) + '"' if size_match else None

    resolution_pattern = r'(HD|FHD|4K|UHD|UltraHD|4k UHD)'
    resolution_match = re.search(resolution_pattern, name, re.IGNORECASE)
    resolution = resolution_match.group(1) if resolution_match else None

    tv_brands = ['FUEGO', 'HISENSE', 'PHILIPS', 'LG', 'TCL', 'GRUNDIG', 'HOOBART', 'SAMSUNG', 'SONY', 'PANASONIC']
    brand = None
    for tv_brand in tv_brands:
        if tv_brand in name:
            brand = tv_brand
            break

    if not brand:
        if resolution_match:
            remaining = name[resolution_match.end():].strip()
            first_word = remaining.split()[0] if remaining else None
            brand = first_word if first_word and len(first_word) > 2 else None

    model_pattern = r'([A-Z0-9\-]+[A-Z][A-Z0-9\-]*)'
    model_match = re.search(model_pattern, name)
    model = model_match.group(1) if model_match else None

    features = []
    if 'Smart' in name:
        features.append('Smart TV')
    if 'Wi-Fi' in name or 'Wifi' in name:
        features.append('Wi-Fi')

    return {
        "brand": brand,
        "model": model,
        "size": size,
        "resolution": resolution,
        "features": ', '.join(features) if features else None
    }


def create_product_schema(product_id, category, original_name, price_data, parsed_data):
    product = {
        "@context": "https://schema.org",
        "@type": "Product",
        "@id": product_id,
        "category": category,
        "name": original_name,
        "offers": {
            "@type": "Offer",
            "price": price_data["price"],
            "priceCurrency": "MKD",
            "availability": "https://schema.org/InStock"
        }
    }

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
        description_parts.append(f"{parsed_data['size']} display")

    if (price_data["regular_price"] and
        price_data["regular_price"] != price_data["price"]):
        discount_info = f" (Discounted from {price_data['regular_price']:,.0f} MKD)"
        description_parts.append(discount_info)

    if description_parts:
        product["description"] = " ".join(description_parts).strip() + "."

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
            "screen_size": "Screen Size"
        }
    elif category == "Smartphones":
        properties_map = {
            "ram": "RAM",
            "storage": "Storage"
        }
    elif category == "Televisions":
        properties_map = {
            "size": "Screen Size",
            "resolution": "Resolution",
            "features": "Features"
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

    return product

def process_neptun_data():
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    output_dir = base_dir / "reforged_data"

    output_dir.mkdir(exist_ok=True)

    all_products = []
    product_id_counter = 1

    files_to_process = [
        {"path": data_dir / "neptun_laptops.csv", "category": "Laptops", "parser": parse_laptop_name},
        {"path": data_dir / "neptun_phones.csv", "category": "Smartphones", "parser": parse_phone_name},
        {"path": data_dir / "neptun_tvs.csv", "category": "Televisions", "parser": parse_tv_name},
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

            df = df[df['name'] != 'N/A']
            df = df.dropna(subset=['name'])

            for index, row in df.iterrows():
                price_data = {
                    "price": parse_price(row['price']),
                    "regular_price": parse_price(row['regular_price']),
                    "discount_price": parse_price(row['discount_price'])
                }

                if price_data["price"] is None:
                    continue

                parsed = parser_func(row['name'])
                product_id = f"neptun-{category.lower()}-{product_id_counter}"
                product_schema = create_product_schema(
                    product_id, category, row['name'], price_data, parsed
                )
                all_products.append(product_schema)
                product_id_counter += 1

            print(f"  Successfully processed {len(df)} {category.lower()}.")

        except Exception as e:
            print(f"  Error processing {file_path}: {e}")
            import traceback
            traceback.print_exc()

    output_file = output_dir / "neptun_products_structured.jsonld"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_products, f, indent=2, ensure_ascii=False)

    print(f"\nSuccessfully processed {len(all_products)} products total")
    print(f"Output saved to {output_file}")

    return all_products


if __name__ == "__main__":
    process_neptun_data()