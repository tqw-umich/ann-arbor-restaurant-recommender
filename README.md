# Ann Arbor Restaurant Recommendation Network
**SI 507 Final Project**

## Overview

A graph-based restaurant recommendation system for Ann Arbor.

- **Nodes** = restaurants
- **Edges** = two restaurants share at least 2 of: same neighborhood, overlapping cuisine, same price range, similar rating (within 0.5 stars)

The graph structure reveals connections that a simple list cannot: starting from one restaurant, you can walk its neighbors to discover places you would actually like.

## Setup

### 1. Install dependencies
```bash
pip install streamlit networkx pytest anthropic
```

### 2. (Optional) Use the full Yelp dataset
Download from https://www.yelp.com/dataset, then set the path:
```bash
export YELP_BUSINESS_JSON=/path/to/yelp_academic_dataset_business.json
```
If this is not set, the app automatically uses a built-in 20-restaurant sample dataset.

### 3. (Optional) Enable the dining narrative feature
The Dining Path mode can generate a short narrative of your evening.
To enable it, set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY=your_api_key_here
```
Get a key at https://console.anthropic.com. If no key is set, all other features still work normally.

### 4. Run the app
```bash
streamlit run app.py
```

### 5. Run the tests
```bash
python -m pytest test_restaurant.py -v
```

## Files

| File | Description |
|------|-------------|
| `restaurant.py` | `Restaurant` and `RestaurantGraph` classes |
| `data_loader.py` | Yelp JSON loading, neighborhood assignment, sample graph |
| `app.py` | Streamlit app with 4 interaction modes |
| `test_restaurant.py` | 40 unit tests |

## Four Interaction Modes

1. **Search** — filter by name, cuisine, neighborhood, price, and minimum rating
2. **Restaurant Detail** — view a restaurant's full profile and its graph neighbors
3. **Recommendations** — get similar restaurant suggestions based on graph connections
4. **Dining Path** — find a path between two restaurants, see why each stop connects to the next, and optionally generate a short narrative of your evening

## Notes on neighborhood assignment

The proposal described using `geopandas` for a spatial join with City of Ann Arbor GeoJSON boundary data. The final implementation uses a coordinate bounding-box approach instead — each restaurant's lat/lon is checked against hand-defined coordinate ranges for eight Ann Arbor neighborhoods. This produces equivalent results for the graph's edge logic without adding a heavyweight geospatial dependency, keeping the project installable with a single `pip install` command.

## Data sources

- [Yelp Open Dataset](https://www.yelp.com/dataset) — restaurant names, categories, price ranges, ratings, coordinates
- Neighborhood zones derived from Ann Arbor coordinate bounds

## No external API key required for core features

The graph, search, recommendations, and path-finding all run locally with no external calls. The narrative feature in Mode 4 is optional.

## Use of Language Models

I used the Anthropic API to add a dining narrative feature in Mode 4. Once the app finds a path between two restaurants, it sends the list of stops and why each one connects to the next to the API, which writes a short story of the evening. This was the part of the project I was most excited about and also the part I spent the most time debugging. All the graph logic, classes, and tests are my own work — the API is only used for the narrative generation at the end.
