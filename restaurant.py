"""
SI 507 Final Project - Ann Arbor Restaurant Recommendation Network
restaurant.py: Core data classes for the project.
"""

import networkx as nx


class Restaurant:
    """
    Represents a single restaurant from the Yelp dataset.

    Attributes
    ----------
    business_id : str
        Unique identifier from Yelp.
    name : str
        Name of the restaurant.
    categories : list[str]
        List of cuisine/category tags (e.g. ['Pizza', 'Italian']).
    price : str
        Price range string: '$', '$$', '$$$', or '$$$$'. Empty string if unknown.
    rating : float
        Yelp star rating (1.0 - 5.0).
    neighborhood : str
        Assigned neighborhood name based on coordinates.
    lat : float
        Latitude coordinate.
    lon : float
        Longitude coordinate.
    address : str
        Street address.
    review_count : int
        Number of Yelp reviews.
    """

    def __init__(self, business_id, name, categories, price, rating,
                 neighborhood, lat, lon, address="", review_count=0):
        self.business_id = business_id
        self.name = name
        self.categories = categories if categories else []
        self.price = price if price else ""
        self.rating = float(rating) if rating else 0.0
        self.neighborhood = neighborhood
        self.lat = float(lat) if lat else 0.0
        self.lon = float(lon) if lon else 0.0
        self.address = address
        self.review_count = int(review_count) if review_count else 0

    def shares_features_with(self, other):
        """
        Count how many features this restaurant shares with another.

        Features compared:
        - Same neighborhood
        - Overlapping cuisine category
        - Same price range
        - Similar rating (within 0.5 stars)

        Parameters
        ----------
        other : Restaurant
            The restaurant to compare against.

        Returns
        -------
        int
            Number of shared features (0 to 4).
        """
        count = 0
        if self.neighborhood and self.neighborhood == other.neighborhood:
            count += 1
        shared_cats = set(self.categories) & set(other.categories)
        if shared_cats:
            count += 1
        if self.price and self.price == other.price:
            count += 1
        if self.rating and other.rating and abs(self.rating - other.rating) <= 0.5:
            count += 1
        return count

    def __repr__(self):
        return f"Restaurant(name={self.name!r}, neighborhood={self.neighborhood!r}, rating={self.rating})"

    def __eq__(self, other):
        if not isinstance(other, Restaurant):
            return False
        return self.business_id == other.business_id

    def __hash__(self):
        return hash(self.business_id)


class RestaurantGraph:
    """
    A graph where nodes are Restaurant objects and edges connect
    restaurants that share at least 2 features (neighborhood, cuisine,
    price, and/or similar rating).

    Wraps a networkx Graph for traversal and analysis.
    """

    def __init__(self):
        self._graph = nx.Graph()
        self._restaurants = {}  # business_id -> Restaurant

    def add_restaurant(self, restaurant):
        """
        Add a Restaurant node to the graph.

        Parameters
        ----------
        restaurant : Restaurant
        """
        self._graph.add_node(restaurant.business_id, data=restaurant)
        self._restaurants[restaurant.business_id] = restaurant

    def build_edges(self, min_shared=2):
        """
        Connect all pairs of restaurants that share at least min_shared features.
        Edges store the shared feature count as a weight.

        Parameters
        ----------
        min_shared : int
            Minimum number of shared features to create an edge. Default is 2.
        """
        ids = list(self._restaurants.keys())
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                r1 = self._restaurants[ids[i]]
                r2 = self._restaurants[ids[j]]
                shared = r1.shares_features_with(r2)
                if shared >= min_shared:
                    self._graph.add_edge(ids[i], ids[j], weight=shared)

    def get_neighbors(self, business_id):
        """
        Return a list of Restaurant objects directly connected to the given restaurant.

        Parameters
        ----------
        business_id : str

        Returns
        -------
        list[Restaurant]
            Neighbor restaurants sorted by edge weight (descending), then by rating.
        """
        if business_id not in self._graph:
            return []
        neighbor_ids = list(self._graph.neighbors(business_id))
        neighbors = []
        for nid in neighbor_ids:
            weight = self._graph[business_id][nid].get("weight", 0)
            neighbors.append((weight, self._restaurants[nid]))
        neighbors.sort(key=lambda x: (x[0], x[1].rating), reverse=True)
        return [r for _, r in neighbors]

    def get_recommendations(self, business_id, n=5):
        """
        Return the top n recommended restaurants given a starting restaurant.
        Uses direct neighbors sorted by shared features and rating.

        Parameters
        ----------
        business_id : str
            Starting restaurant.
        n : int
            Number of recommendations to return.

        Returns
        -------
        list[Restaurant]
        """
        neighbors = self.get_neighbors(business_id)
        return neighbors[:n]

    def find_path(self, start_id, end_id):
        """
        Find the shortest path between two restaurants in the graph.

        Parameters
        ----------
        start_id : str
        end_id : str

        Returns
        -------
        list[Restaurant] or None
            Ordered list of restaurants on the path, or None if no path exists.
        """
        if start_id not in self._graph or end_id not in self._graph:
            return None
        try:
            path_ids = nx.shortest_path(self._graph, start_id, end_id)
            return [self._restaurants[rid] for rid in path_ids]
        except nx.NetworkXNoPath:
            return None

    def search_by_name(self, query):
        """
        Case-insensitive search for restaurants by name.

        Parameters
        ----------
        query : str

        Returns
        -------
        list[Restaurant]
        """
        query = query.lower().strip()
        results = []
        for r in self._restaurants.values():
            if query in r.name.lower():
                results.append(r)
        return sorted(results, key=lambda x: x.name)

    def search_by_cuisine(self, cuisine):
        """
        Search for restaurants by cuisine/category keyword (case-insensitive).

        Parameters
        ----------
        cuisine : str

        Returns
        -------
        list[Restaurant]
        """
        cuisine = cuisine.lower().strip()
        results = []
        for r in self._restaurants.values():
            for cat in r.categories:
                if cuisine in cat.lower():
                    results.append(r)
                    break
        return sorted(results, key=lambda x: x.rating, reverse=True)

    def get_restaurant(self, business_id):
        """
        Return a Restaurant by its ID, or None if not found.

        Parameters
        ----------
        business_id : str

        Returns
        -------
        Restaurant or None
        """
        return self._restaurants.get(business_id)

    def get_all_restaurants(self):
        """Return a list of all Restaurant objects in the graph."""
        return list(self._restaurants.values())

    def get_all_neighborhoods(self):
        """Return a sorted list of unique neighborhood names."""
        hoods = set(r.neighborhood for r in self._restaurants.values() if r.neighborhood)
        return sorted(hoods)

    def get_all_cuisines(self):
        """Return a sorted list of unique cuisine/category tags."""
        cats = set()
        for r in self._restaurants.values():
            for c in r.categories:
                cats.add(c)
        return sorted(cats)

    @property
    def node_count(self):
        """Number of restaurants in the graph."""
        return self._graph.number_of_nodes()

    @property
    def edge_count(self):
        """Number of edges in the graph."""
        return self._graph.number_of_edges()
