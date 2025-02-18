import os
import json
import sqlite3
from aps import ModelDerivativesClient

def parse_length(value):
    units = {
        "m": 1,
        "cm": 0.01,
        "mm": 0.001,
        "km": 1000,
        "in": 0.0254,
        "ft": 0.3048,
        "ft-and-fractional-in": 0.3048,
        "yd": 0.9144,
        "mi": 1609.34
    }
    number, unit = value.split()
    return float(number) * units[unit]

def parse_area(value):
    units = {
        "m^2": 1,
        "cm^2": 0.0001,
        "mm^2": 0.000001,
        "km^2": 1000000,
        "in^2": 0.00064516,
        "ft^2": 0.092903,
        "yd^2": 0.836127,
        "mi^2": 2589988.11
    }
    number, unit = value.split()
    return float(number) * units[unit]

def parse_volume(value):
    units = {
        "m^3": 1,
        "cm^3": 0.000001,
        "mm^3": 0.000000001,
        "km^3": 1000000000,
        "in^3": 0.0000163871,
        "ft^3": 0.0283168,
        "CF": 0.0283168,
        "yd^3": 0.764555
    }
    number, unit = value.split()
    return float(number) * units[unit]

def parse_angle(value):
    units = {
        "degrees": 1,
        "degree": 1,
        "deg": 1,
        "°": 1,
        "radians": 57.2958,
        "radian": 57.2958,
        "rad": 57.2958,
    }
    number, unit = value.split()
    return float(number) * units[unit]

# Define the properties to extract from the model
# (column name, column type, category name, property name, parsing function)
PROPERTIES = [
    ("width",       "REAL", "Dimensions",               "Width",                parse_length),
    ("height",      "REAL", "Dimensions",               "Height",               parse_length),
    ("length",      "REAL", "Dimensions",               "Length",               parse_length),
    ("area",        "REAL", "Dimensions",               "Area",                 parse_area),
    ("volume",      "REAL", "Dimensions",               "Volume",               parse_volume),
    ("perimeter",   "REAL", "Dimensions",               "Perimeter",            parse_length),
    ("slope",       "REAL", "Dimensions",               "Slope",                parse_angle),
    ("thickness",   "REAL", "Dimensions",               "Thickness",            parse_length),
    ("radius",      "REAL", "Dimensions",               "Radius",               parse_length),
    ("level",       "TEXT", "Constraints",              "Level",                lambda x: x),
    ("material",    "TEXT", "Materials and Finishes",   "Structural Material",  lambda x: x),
]

async def create_property_database(urn: str, propdb_path: str, access_token: str):
    model_derivative_client = ModelDerivativesClient(access_token)

    views = await model_derivative_client.list_model_views(urn)
    with open(os.path.dirname(propdb_path) + "/views.json", "w") as f: json.dump(views, f)
    tree = await model_derivative_client.fetch_object_tree(urn, views[0]["guid"]) # Use the first view
    with open(os.path.dirname(propdb_path) + "/tree.json", "w") as f: json.dump(tree, f)
    props = await model_derivative_client.fetch_all_properties(urn, views[0]["guid"]) # Use the first view
    with open(os.path.dirname(propdb_path) + "/props.json", "w") as f: json.dump(props, f)

    conn = sqlite3.connect(propdb_path)
    c = conn.cursor()
    c.execute(f"CREATE TABLE properties (object_id NUMBER, name TEXT, external_id TEXT, {", ".join([f'{column_name} {column_type}' for (column_name, column_type, _, _, _) in PROPERTIES])})")
    for row in props:
        object_id = row["objectid"]
        name = row["name"]
        external_id = row["externalId"]
        object_props = row["properties"]
        insert_values = [object_id, name, external_id]
        for (_, _, category_name, property_name, parse_func) in PROPERTIES:
            if category_name in object_props and property_name in object_props[category_name]:
                insert_values.append(parse_func(object_props[category_name][property_name]))
            else:
                insert_values.append(None)
        c.execute(f"INSERT INTO properties VALUES ({', '.join(['?' for _ in insert_values])})", insert_values)
    conn.commit()
    conn.close()