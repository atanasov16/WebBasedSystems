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
        return {"brand": None, "model": None, "color": None, "cpu": None}

    name_clean = name.replace('Лаптоп ', '').strip()

    brand_match = re.search(r'^([A-Za-z]+)', name_clean)
    if not brand_match:
        return {"brand": None, "model": None, "color": None, "cpu": None}

    brand = brand_match.group(1).strip()

    color_match = re.search(r'\((.*?)\)', name_clean)
    color = color_match.group(1) if color_match else None

    model_part = re.sub(r'\(.*?\)', '', name_clean).replace(brand, '').strip()

    cpu_pattern = r'(Intel® Core™ i[3-9]-[A-Z0-9]+|AMD Ryzen [0-9])'
    cpu_match = re.search(cpu_pattern, model_part, re.IGNORECASE)
    cpu = cpu_match.group(1) if cpu_match else None

    return {
        "brand": brand,
        "model": model_part,
        "color": color,
        "cpu": cpu
    }


def parse_phone_name(name):
    if pd.isna(name):
        return {"brand": None, "model": None, "color": None, "type": None}

    brand_match = re.search(r'^([A-Za-z]+)', name)
    if not brand_match:
        return {"brand": None, "model": None, "color": None, "type": None}

    brand = brand_match.group(1).strip()

    color_keywords = ['Black', 'Blue', 'Gray', 'Grey', 'Silver', 'White', 'Red', 'Gold', 'Green']
    color = None
    for keyword in color_keywords:
        if keyword in name:
            color = keyword
            break

    phone_type = "Smartphone"
    if 'Feature phone' in name:
        phone_type = "Feature phone"

    model_part = name.replace(brand, '').strip()
    if color:
        model_part = model_part.replace(color, '').strip()
    if phone_type == "Feature phone":
        model_part = model_part.replace('Feature phone', '').strip()

    return {
        "brand": brand,
        "model": model_part,
        "color": color,
        "type": phone_type
    }


def parse_tv_name(name):
    if pd.isna(name):
        return {"brand": None, "model": None, "size": None, "technology": None}

    brand_match = re.search(r'^([A-Za-z]+)', name)
    if not brand_match:
        return {"brand": None, "model": None, "size": None, "technology": None}

    brand = brand_match.group(1).strip()

    model_match = re.search(r'([A-Z0-9]+[A-Z][A-Z0-9]*)', name)
    model = model_match.group(1) if model_match else None

    size = None
    if model and re.search(r'^\d{2}', model):
        size_match = re.search(r'^(\d{2})', model)
        if size_match:
            size = size_match.group(1) + '"'

    technology = "OLED" if "OLED" in name else "LED"

    return {
        "brand": brand,
        "model": model,
        "size": size,
        "technology": technology
    }


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
            "color": "Color"
        }
    elif category == "Smartphones":
        properties_map = {
            "type": "Type",
            "color": "Color"
        }
    elif category == "Televisions":
        properties_map = {
            "size": "Screen Size",
            "technology": "Display Technology"
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
    if parsed_data.get("color"):
        description_parts.append(f"in {parsed_data['color']}")
    if category == "Laptops" and parsed_data.get("cpu"):
        description_parts.append(f"with {parsed_data['cpu']}")
    if category == "Televisions" and parsed_data.get("technology"):
        description_parts.append(f"with {parsed_data['technology']} display")

    if description_parts:
        product["description"] = " ".join(description_parts) + "."

    return product


def process_setec_data():
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    output_dir = base_dir / "reforged_data"

    output_dir.mkdir(exist_ok=True)

    all_products = []
    product_id_counter = 1

    files_to_process = [
        {"path": data_dir / "setec_laptops.csv", "category": "Laptops", "parser": parse_laptop_name},
        {"path": data_dir / "setec_smartphones.csv", "category": "Smartphones", "parser": parse_phone_name},
        {"path": data_dir / "setec_oled_tvs.csv", "category": "Televisions", "parser": parse_tv_name},
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
                product_id = f"setec-{category.lower()}-{product_id_counter}"
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

    output_file = output_dir / "setec_products_structured.jsonld"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_products, f, indent=2, ensure_ascii=False)

    print(f"\nSuccessfully processed {len(all_products)} products total")
    print(f"Output saved to {output_file}")

    return all_products


if __name__ == "__main__":
    process_setec_data()