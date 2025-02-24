import os
import json
import sqlite3
from langchain_community.utilities import SQLDatabase
from aps import ModelDerivativesClient

def _parse_length(value):
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

def _parse_area(value):
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

def _parse_volume(value):
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

def _parse_angle(value):
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
    ("width",       "REAL", "Dimensions",               "Width",                _parse_length),
    ("height",      "REAL", "Dimensions",               "Height",               _parse_length),
    ("length",      "REAL", "Dimensions",               "Length",               _parse_length),
    ("area",        "REAL", "Dimensions",               "Area",                 _parse_area),
    ("volume",      "REAL", "Dimensions",               "Volume",               _parse_volume),
    ("perimeter",   "REAL", "Dimensions",               "Perimeter",            _parse_length),
    ("slope",       "REAL", "Dimensions",               "Slope",                _parse_angle),
    ("thickness",   "REAL", "Dimensions",               "Thickness",            _parse_length),
    ("radius",      "REAL", "Dimensions",               "Radius",               _parse_length),
    ("level",       "TEXT", "Constraints",              "Level",                lambda x: x),
    ("material",    "TEXT", "Materials and Finishes",   "Structural Material",  lambda x: x),
]

async def setup(urn: str, access_token: str, cache_urn_dir: str) -> SQLDatabase:
    propdb_path = os.path.join(cache_urn_dir, "props.sqlite3")
    if os.path.exists(propdb_path):
        return SQLDatabase.from_uri(f"sqlite:///{propdb_path}")

    model_derivative_client = ModelDerivativesClient(access_token)

    views_path = os.path.join(cache_urn_dir, "views.json")
    if not os.path.exists(views_path):
        views = await model_derivative_client.list_model_views(urn)
        with open(views_path, "w") as f: json.dump(views, f)
    else:
        with open(views_path, "r") as f: views = json.load(f)
    view_guid = views[0]["guid"] # Use the first view

    tree_path = os.path.join(cache_urn_dir, "tree.json")
    if not os.path.exists(tree_path):
        tree = await model_derivative_client.fetch_object_tree(urn, view_guid)
        with open(tree_path, "w") as f: json.dump(tree, f)
    else:
        with open(tree_path, "r") as f: tree = json.load(f)

    props_path = os.path.join(cache_urn_dir, "props.json")
    if not os.path.exists(props_path):
        props = await model_derivative_client.fetch_all_properties(urn, view_guid)
        with open(props_path, "w") as f: json.dump(props, f)
    else:
        with open(props_path, "r") as f: props = json.load(f)

    conn = sqlite3.connect(propdb_path)
    c = conn.cursor()
    c.execute(f"CREATE TABLE properties (object_id INTEGER, name TEXT, external_id TEXT, {", ".join([f'{column_name} {column_type}' for (column_name, column_type, _, _, _) in PROPERTIES])})")
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
    return SQLDatabase.from_uri(f"sqlite:///{propdb_path}")