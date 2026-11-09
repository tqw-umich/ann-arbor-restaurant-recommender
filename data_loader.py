"""
SI 507 Final Project - Ann Arbor Restaurant Recommendation Network
data_loader.py: Load and filter Yelp data, assign neighborhoods by coordinates.
"""

import json
import os
from restaurant import Restaurant, RestaurantGraph

# Ann Arbor bounding box (approximate lat/lon bounds)
ANN_ARBOR_BOUNDS = {
    "lat_min": 42.22,
    "lat_max": 42.33,
    "lon_min": -83.80,
    "lon_max": -83.67,
}

# Neighborhood definitions based on approximate coordinate zones within Ann Arbor.
# Each entry is (name, lat_min, lat_max, lon_min, lon_max).
NEIGHBORHOODS = [
    ("Kerrytown",        42.283, 42.295, -83.755, -83.737),
    ("Downtown",         42.277, 42.286, -83.752, -83.738),
    ("University Area",  42.270, 42.283, -83.745, -83.726),
    ("South University", 42.267, 42.275, -83.737, -83.720),
    ("Burns Park",       42.260, 42.272, -83.730, -83.710),
    ("Westside",         42.270, 42.310, -83.800, -83.755),
    ("Northeast",        42.290, 42.330, -83.720, -83.670),
    ("Southeast",        42.220, 42.260, -83.740, -83.670),
]


def assign_neighborhood(lat, lon):
    """
    Assign an Ann Arbor neighborhood name to a (lat, lon) coordinate.
    Returns the first matching neighborhood zone, or 'Other Ann Arbor'.

    Parameters
    ----------
    lat : float
    lon : float

    Returns
    -------
    str
    """
    for name, lat_min, lat_max, lon_min, lon_max in NEIGHBORHOODS:
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return name
    return "Other Ann Arbor"


def parse_price(attributes):
    """
    Extract price range string from Yelp business attributes dict.

    Parameters
    ----------
    attributes : dict or None

    Returns
    -------
    str
        '$', '$$', '$$$', '$$$$', or ''.
    """
    if not attributes:
        return ""
    level = attributes.get("RestaurantsPriceRange2")
    if level is None:
        return ""
    try:
        level = int(level)
    except (ValueError, TypeError):
        return ""
    mapping = {1: "$", 2: "$$", 3: "$$$", 4: "$$$$"}
    return mapping.get(level, "")


def load_ann_arbor_restaurants(business_json_path, max_count=None):
    """
    Load Ann Arbor restaurants from a Yelp business.json file.

    Filters to businesses that:
    - Are in Ann Arbor, MI (by city field or coordinate bounds)
    - Have 'Restaurants' or 'Food' in their categories
    - Are currently open (is_open == 1)

    Parameters
    ----------
    business_json_path : str
        Path to yelp_academic_dataset_business.json
    max_count : int or None
        Optional cap on how many restaurants to load (for testing).

    Returns
    -------
    list[Restaurant]
    """
    restaurants = []
    with open(business_json_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                biz = json.loads(line)
            except json.JSONDecodeError:
                continue

            lat = biz.get("latitude")
            lon = biz.get("longitude")
            if not lat or not lon:
                continue
            lat, lon = float(lat), float(lon)

            city = biz.get("city", "")
            state = biz.get("state", "")
            in_bounds = (
                ANN_ARBOR_BOUNDS["lat_min"] <= lat <= ANN_ARBOR_BOUNDS["lat_max"]
                and ANN_ARBOR_BOUNDS["lon_min"] <= lon <= ANN_ARBOR_BOUNDS["lon_max"]
            )
            is_aa = (city.lower() == "ann arbor" and state == "MI") or in_bounds
            if not is_aa:
                continue

            if biz.get("is_open", 0) != 1:
                continue

            raw_cats = biz.get("categories") or ""
            categories = [c.strip() for c in raw_cats.split(",") if c.strip()]
            if not any(c in ("Restaurants", "Food") for c in categories):
                continue

            cuisine_cats = [c for c in categories if c not in ("Restaurants", "Food")]
            neighborhood = assign_neighborhood(lat, lon)
            price = parse_price(biz.get("attributes"))

            r = Restaurant(
                business_id=biz["business_id"],
                name=biz.get("name", "Unknown"),
                categories=cuisine_cats,
                price=price,
                rating=biz.get("stars", 0.0),
                neighborhood=neighborhood,
                lat=lat,
                lon=lon,
                address=biz.get("address", ""),
                review_count=biz.get("review_count", 0),
            )
            restaurants.append(r)

            if max_count and len(restaurants) >= max_count:
                break

    return restaurants


def build_graph(business_json_path, max_count=None):
    """
    Load Ann Arbor restaurants from the Yelp dataset and build the graph.

    Parameters
    ----------
    business_json_path : str
    max_count : int or None

    Returns
    -------
    RestaurantGraph
    """
    restaurants = load_ann_arbor_restaurants(business_json_path, max_count)
    graph = RestaurantGraph()
    for r in restaurants:
        graph.add_restaurant(r)
    graph.build_edges(min_shared=2)
    return graph


def build_sample_graph():
    """
    Build a small sample graph with hardcoded restaurants for demo/testing
    when the full Yelp dataset is not available.

    Returns
    -------
    RestaurantGraph
    """
    sample_data = [
        ("biz001", "Zingerman's Deli",          ["Delis", "Sandwiches", "Jewish"],   "$$",  4.5, "Kerrytown",        42.2894, -83.7458, "422 Detroit St",    2500),
        ("biz002", "Frita Batidos",              ["Cuban", "Burgers", "Latin"],       "$$",  4.4, "Downtown",         42.2817, -83.7481, "117 W Washington",  1800),
        ("biz003", "Slurping Turtle",            ["Japanese", "Ramen", "Noodles"],    "$$$", 4.3, "Downtown",         42.2820, -83.7479, "66 E Michigan Ave",  900),
        ("biz004", "Miss Kim",                   ["Korean", "Asian Fusion"],          "$$",  4.6, "Kerrytown",        42.2891, -83.7460, "415 N Fifth Ave",   1100),
        ("biz005", "Totoro",                     ["Japanese", "Sushi", "Asian"],      "$$",  4.2, "University Area",  42.2778, -83.7395, "622 Church St",      800),
        ("biz006", "Mani Osteria",               ["Italian", "Pizza", "Wine Bars"],   "$$$", 4.5, "Downtown",         42.2816, -83.7490, "341 E Liberty St",  1200),
        ("biz007", "Tomukun Noodle Bar",         ["Korean", "Noodles", "Asian"],      "$$",  4.1, "University Area",  42.2780, -83.7401, "505 E Liberty St",   700),
        ("biz008", "Vinology",                   ["American", "Wine Bars", "Tapas"],  "$$$", 4.0, "Downtown",         42.2818, -83.7477, "110 S Main St",      900),
        ("biz009", "Isalita",                    ["Mexican", "Margaritas"],           "$$",  4.3, "South University", 42.2710, -83.7310, "341 E Liberty St",  1000),
        ("biz010", "Seva",                       ["Vegetarian", "Vegan", "American"], "$$",  4.2, "South University", 42.2708, -83.7315, "314 E Liberty St",   600),
        ("biz011", "Pizza House",                ["Pizza", "Italian", "American"],    "$$",  3.8, "University Area",  42.2782, -83.7403, "618 Church St",     2000),
        ("biz012", "Gratzi",                     ["Italian", "Wine Bars"],            "$$$", 4.1, "Downtown",         42.2815, -83.7482, "326 S Main St",      800),
        ("biz013", "Afternoon Delight",          ["American", "Breakfast & Brunch"],  "$",   4.3, "Kerrytown",        42.2892, -83.7461, "251 E Liberty St",  1500),
        ("biz014", "Jerusalem Garden",           ["Middle Eastern", "Mediterranean"], "$",   4.4, "Downtown",         42.2819, -83.7476, "307 S Fifth Ave",    900),
        ("biz015", "Blue Tractor BBQ",           ["BBQ", "American", "Burgers"],      "$$",  3.9, "Downtown",         42.2813, -83.7488, "207 E Washington",  1100),
        ("biz016", "Sava's",                     ["American", "Brunch"],              "$$",  4.2, "Downtown",         42.2822, -83.7480, "216 S State St",    1200),
        ("biz017", "Krazy Jim's Blimpy Burger",  ["Burgers", "American"],             "$",   4.5, "South University", 42.2713, -83.7319, "304 S Ashley St",   1800),
        ("biz018", "Amadeus",                    ["Polish", "European"],              "$$",  4.3, "Downtown",         42.2820, -83.7472, "122 E Washington",   400),
        ("biz019", "Thai Palace",                ["Thai", "Asian"],                   "$$",  4.0, "University Area",  42.2776, -83.7390, "708 Packard St",     600),
        ("biz020", "Red Hawk Bar & Grill",       ["American", "Burgers", "Bar"],      "$$",  3.7, "University Area",  42.2779, -83.7398, "316 S State St",     900),
    ]
    graph = RestaurantGraph()
    for row in sample_data:
        bid, name, cats, price, rating, hood, lat, lon, addr, reviews = row
        r = Restaurant(bid, name, cats, price, rating, hood, lat, lon, addr, reviews)
        graph.add_restaurant(r)
    graph.build_edges(min_shared=2)
    return graph
