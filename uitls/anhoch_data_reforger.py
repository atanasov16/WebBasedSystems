import re
import json
import pandas as pd
import os
from pathlib import Path


def parse_price(price_str):
    try:
        cleaned = price_str.replace(' ден.', '').replace('.', '').replace(',', '.')
        price_float = float(cleaned)
        return price_float, "MKD"
    except (ValueError, AttributeError):
        return None, None


def parse_laptop_name(name):
    pattern = r"Notebook\s+([A-Za-z0-9]+)\s+([A-Za-z0-9\s]+?)\s+([A-Za-z0-9\-]+)\/([A-Za-z0-9]+)\/([A-Za-z0-9\s]+)\/([A-Za-z0-9\.\"\s]+)\/(.+)"
    match = re.search(pattern, name)

    if not match:
        pattern_fallback = r"Notebook\s+([A-Za-z0-9]+)\s+([A-Za-z0-9\s]+?)\s+([^\/]+)\/([^\/]+)\/([^\/]+)\/([^\/]+)\/(.+)"
        match = re.search(pattern_fallback, name)
        if not match:
            return {"brand": None, "model_line": None, "cpu": None, "ram": None,
                    "storage": None, "screen_info": None, "features": None}

    brand = match.group(1).strip()
    model_line = match.group(2).strip()
    cpu = match.group(3).strip()
    ram = match.group(4).strip()
    storage = match.group(5).strip()
    screen_info = match.group(6).strip()
    features = match.group(7).strip()

    screen_size_match = re.search(r'(\d+\.?\d*")', screen_info)
    screen_size = screen_size_match.group(1) if screen_size_match else None

    color = None
    color_keywords = ['Grey', 'Black', 'Blue', 'Silver', 'White', 'Red', 'Gold', 'Fog Blue', 'Awesome Lavander',
                      'Awesome White', 'Awesome Black']
    for keyword in color_keywords:
        if keyword in features:
            color = keyword
            break

    return {
        "brand": brand,
        "model_line": model_line,
        "cpu": cpu,
        "ram": ram,
        "storage": storage,
        "screen_size": screen_size,
        "screen_info": screen_info,
        "features": features,
        "color": color
    }


def parse_phone_name(name):
    pattern = r"([A-Za-z]+)\s+([A-Za-z0-9\s]+?)\s+([A-Za-z0-9]+)\/([A-Za-z0-9]+)\s+([A-Za-z\s]+)"
    match = re.search(pattern, name)

    if not match:
        return {"brand": None, "model": None, "ram": None, "storage": None, "color": None}

    brand = match.group(1).strip()
    model = match.group(2).strip()
    ram = match.group(3).strip()
    storage = match.group(4).strip()
    color = match.group(5).strip()

    return {
        "brand": brand,
        "model": model,
        "ram": ram,
        "storage": storage,
        "color": color
    }


def parse_tv_name(name):
    pattern1 = r"TV\s+([A-Za-z]+)\s+(\d+\")\s+([A-Za-z0-9\-]+)\s+([A-Za-z0-9\s]+?)\s+([A-Za-z]+)\s+([A-Za-z\s]+)"
    match = re.search(pattern1, name)

    if match:
        brand = match.group(1).strip()
        size = match.group(2).strip()
        model = match.group(3).strip()
        resolution = match.group(4).strip()
        tv_type = match.group(5).strip()
        features = match.group(6).strip()
    else:
        pattern2 = r"([A-Za-z]+)\s+([A-Za-z0-9\-]+)\s+(\d+\")\s+([A-Za-z0-9\s]+)"
        match = re.search(pattern2, name)
        if match:
            brand = match.group(1).strip()
            model = match.group(2).strip()
            size = match.group(3).strip()
            features = match.group(4).strip()
            resolution = None
            tv_type = None
        else:
            return {"brand": None, "model": None, "size": None, "resolution": None,
                    "type": None, "features": None}

    return {
        "brand": brand,
        "model": model,
        "size": size,
        "resolution": resolution,
        "type": tv_type,
        "features": features
    }


def create_product_schema(product_id, category, original_name, price, price_currency, parsed_data):
    product = {
        "@context": "https://schema.org",
        "@type": "Product",
        "@id": product_id,
        "category": category,
        "name": original_name,
        "offers": {
            "@type": "Offer",
            "price": price,
            "priceCurrency": price_currency,
            "availability": "https://schema.org/InStock"
        }
    }

    if parsed_data.get("brand"):
        product["brand"] = {
            "@type": "Brand",
            "name": parsed_data["brand"]
        }

    if parsed_data.get("model") or parsed_data.get("model_line"):
        product["model"] = parsed_data.get("model") or parsed_data.get("model_line")

    if parsed_data.get("color"):
        product["color"] = parsed_data["color"]

    additional_props = []

    if category == "Laptops":
        properties_map = {
            "cpu": "Processor",
            "ram": "RAM",
            "storage": "Storage",
            "screen_size": "Screen Size",
            "screen_info": "Screen Info",
            "features": "Features"
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
            "type": "Type",
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

    description_parts = []
    if parsed_data.get("brand"):
        description_parts.append(parsed_data["brand"])
    if parsed_data.get("model") or parsed_data.get("model_line"):
        description_parts.append(parsed_data.get("model") or parsed_data.get("model_line"))
    if category == "Laptops" and parsed_data.get("cpu"):
        description_parts.append(f"with {parsed_data['cpu']} processor")
    if category == "Smartphones" and parsed_data.get("ram") and parsed_data.get("storage"):
        description_parts.append(f"with {parsed_data['ram']} RAM and {parsed_data['storage']} storage")

    if description_parts:
        product["description"] = " ".join(description_parts) + "."

    return product


def process_anhoch_data():
    base_dir = Path(__file__).parent.parent  # Goes up from 'utils' to the project root
    data_dir = base_dir / "data"
    output_dir = base_dir / "reforged_data"

    output_dir.mkdir(exist_ok=True)

    all_products = []
    product_id_counter = 1

    files_to_process = [
        {"path": data_dir / "anhoch_laptops.csv", "category": "Laptops", "parser": parse_laptop_name},
        {"path": data_dir / "anhoch_phones.csv", "category": "Smartphones", "parser": parse_phone_name},
        {"path": data_dir / "anhoch_tvs.csv", "category": "Televisions", "parser": parse_tv_name},
    ]

    for file_info in files_to_process:
        file_path = file_info["path"]
        category = file_info["category"]
        parser_func = file_info["parser"]

        if not file_path.exists():
            continue

        try:
            df = pd.read_csv(file_path)

            for index, row in df.iterrows():
                price, currency = parse_price(row['price'])
                parsed = parser_func(row['name'])
                product_id = f"anhoch-{category.lower()}-{product_id_counter}"
                product_schema = create_product_schema(
                    product_id, category, row['name'], price, currency, parsed
                )
                all_products.append(product_schema)
                product_id_counter += 1

            print(f"  Successfully processed {len(df)} {category.lower()}.")

        except Exception as e:
            print(f"  Error processing {file_path}: {e}")

    # Save all products to a JSON-LD file
    output_file = output_dir / "anhoch_products_structured.jsonld"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_products, f, indent=2, ensure_ascii=False)

    print(f"\nSuccessfully processed {len(all_products)} products total")
    print(f"Output saved to {output_file}")

    return all_products


if __name__ == "__main__":
    process_anhoch_data()