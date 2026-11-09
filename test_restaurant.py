"""
SI 507 Final Project - Ann Arbor Restaurant Recommendation Network
test_restaurant.py: Unit tests for Restaurant and RestaurantGraph.

Run with:
    python -m pytest test_restaurant.py -v
"""

import pytest
from restaurant import Restaurant, RestaurantGraph


@pytest.fixture
def r_zingermans():
    return Restaurant(
        "biz001", "Zingerman's Deli",
        ["Delis", "Sandwiches", "Jewish"], "$$", 4.5,
        "Kerrytown", 42.2894, -83.7458, "422 Detroit St", 2500
    )

@pytest.fixture
def r_miss_kim():
    return Restaurant(
        "biz004", "Miss Kim",
        ["Korean", "Asian Fusion"], "$$", 4.6,
        "Kerrytown", 42.2891, -83.7460, "415 N Fifth Ave", 1100
    )

@pytest.fixture
def r_slurping_turtle():
    return Restaurant(
        "biz003", "Slurping Turtle",
        ["Japanese", "Ramen", "Noodles"], "$$$", 4.3,
        "Downtown", 42.2820, -83.7479, "66 E Michigan Ave", 900
    )

@pytest.fixture
def r_mani():
    return Restaurant(
        "biz006", "Mani Osteria",
        ["Italian", "Pizza", "Wine Bars"], "$$$", 4.5,
        "Downtown", 42.2816, -83.7490, "341 E Liberty St", 1200
    )

@pytest.fixture
def r_vinology():
    return Restaurant(
        "biz008", "Vinology",
        ["American", "Wine Bars", "Tapas"], "$$$", 4.0,
        "Downtown", 42.2818, -83.7477, "110 S Main St", 900
    )

@pytest.fixture
def small_graph(r_zingermans, r_miss_kim, r_slurping_turtle, r_mani, r_vinology):
    """A graph with 5 restaurants and edges built at min_shared=2."""
    g = RestaurantGraph()
    for r in [r_zingermans, r_miss_kim, r_slurping_turtle, r_mani, r_vinology]:
        g.add_restaurant(r)
    g.build_edges(min_shared=2)
    return g

@pytest.fixture
def sample_graph():
    """Full sample graph from data_loader (20 restaurants)."""
    from data_loader import build_sample_graph
    return build_sample_graph()


# Restaurant class tests

class TestRestaurantInit:
    def test_basic_attributes(self, r_zingermans):
        r = r_zingermans
        assert r.business_id == "biz001"
        assert r.name == "Zingerman's Deli"
        assert r.rating == 4.5
        assert r.price == "$$"
        assert r.neighborhood == "Kerrytown"

    def test_categories_list(self, r_zingermans):
        assert isinstance(r_zingermans.categories, list)
        assert "Delis" in r_zingermans.categories

    def test_coordinates_are_floats(self, r_zingermans):
        assert isinstance(r_zingermans.lat, float)
        assert isinstance(r_zingermans.lon, float)

    def test_none_categories_defaults_to_empty_list(self):
        r = Restaurant("x", "Test", None, "$", 3.0, "Hood", 42.0, -83.0)
        assert r.categories == []

    def test_empty_price_is_allowed(self):
        r = Restaurant("x", "Test", [], "", 3.0, "Hood", 42.0, -83.0)
        assert r.price == ""

    def test_equality_by_business_id(self, r_zingermans):
        duplicate = Restaurant("biz001", "Different Name", [], "$", 1.0, "X", 0.0, 0.0)
        assert r_zingermans == duplicate

    def test_inequality_for_different_ids(self, r_zingermans, r_miss_kim):
        assert r_zingermans != r_miss_kim

    def test_restaurants_are_hashable(self, r_zingermans, r_miss_kim):
        s = {r_zingermans, r_miss_kim}
        assert len(s) == 2


class TestSharesFeatures:
    def test_same_neighborhood_counts(self, r_zingermans, r_miss_kim):
        # Both in Kerrytown
        count = r_zingermans.shares_features_with(r_miss_kim)
        assert count >= 1

    def test_same_price_counts(self, r_zingermans, r_miss_kim):
        # Both $$
        count = r_zingermans.shares_features_with(r_miss_kim)
        assert count >= 1

    def test_shared_category_counts(self):
        r1 = Restaurant("a", "A", ["Italian", "Pizza"], "$$", 4.0, "Downtown", 42.28, -83.74)
        r2 = Restaurant("b", "B", ["Pizza", "American"], "$$", 3.8, "Westside", 42.29, -83.76)
        count = r1.shares_features_with(r2)
        assert count >= 1

    def test_similar_rating_within_half_star_counts(self):
        r1 = Restaurant("a", "A", [], "$", 4.0, "X", 42.0, -83.0)
        r2 = Restaurant("b", "B", [], "$", 4.4, "Y", 42.1, -83.1)
        count = r1.shares_features_with(r2)
        assert count >= 2  # same price + similar rating

    def test_no_shared_features_returns_zero(self):
        r1 = Restaurant("a", "A", ["Italian"], "$",  4.0, "Kerrytown", 42.0, -83.0)
        r2 = Restaurant("b", "B", ["Korean"],  "$$", 2.0, "Northeast", 42.3, -83.7)
        count = r1.shares_features_with(r2)
        assert count == 0

    def test_max_shared_features_is_four(self):
        r1 = Restaurant("a", "A", ["Italian"], "$$", 4.2, "Downtown", 42.28, -83.74)
        r2 = Restaurant("b", "B", ["Italian"], "$$", 4.0, "Downtown", 42.28, -83.75)
        count = r1.shares_features_with(r2)
        assert count <= 4


# RestaurantGraph tests 

class TestGraphConstruction:
    def test_node_count_matches_added_restaurants(self, small_graph):
        assert small_graph.node_count == 5

    def test_edges_created_for_similar_restaurants(self, small_graph):
        # Mani and Vinology share Downtown + $$$ → should be connected
        mani = small_graph.get_restaurant("biz006")
        vinology = small_graph.get_restaurant("biz008")
        if mani.shares_features_with(vinology) >= 2:
            neighbors = small_graph.get_neighbors("biz006")
            neighbor_ids = [n.business_id for n in neighbors]
            assert "biz008" in neighbor_ids

    def test_no_self_loops(self, small_graph):
        for rid in ["biz001", "biz003", "biz004", "biz006", "biz008"]:
            neighbor_ids = [n.business_id for n in small_graph.get_neighbors(rid)]
            assert rid not in neighbor_ids

    def test_edges_are_symmetric(self, small_graph):
        """If A is a neighbor of B, B must be a neighbor of A."""
        for rid in ["biz001", "biz003", "biz004", "biz006", "biz008"]:
            for n in small_graph.get_neighbors(rid):
                reverse_ids = [x.business_id for x in small_graph.get_neighbors(n.business_id)]
                assert rid in reverse_ids

    def test_sample_graph_has_edges(self, sample_graph):
        assert sample_graph.edge_count > 0

    def test_sample_graph_node_count(self, sample_graph):
        assert sample_graph.node_count == 20


class TestSearch:
    def test_search_by_name_finds_match(self, sample_graph):
        results = sample_graph.search_by_name("Pizza")
        assert len(results) > 0

    def test_search_by_name_is_case_insensitive(self, sample_graph):
        lower = sample_graph.search_by_name("pizza")
        upper = sample_graph.search_by_name("PIZZA")
        assert len(lower) == len(upper)

    def test_search_by_name_no_match_returns_empty(self, sample_graph):
        results = sample_graph.search_by_name("xkjsdflkjsd")
        assert results == []

    def test_search_by_cuisine_finds_match(self, sample_graph):
        results = sample_graph.search_by_cuisine("Korean")
        assert len(results) > 0

    def test_search_by_cuisine_sorted_by_rating_descending(self, sample_graph):
        results = sample_graph.search_by_cuisine("American")
        ratings = [r.rating for r in results]
        assert ratings == sorted(ratings, reverse=True)

    def test_search_by_cuisine_no_match_returns_empty(self, sample_graph):
        results = sample_graph.search_by_cuisine("Klingon Food")
        assert results == []


class TestRecommendations:
    def test_recommendations_returns_a_list(self, sample_graph):
        all_r = sample_graph.get_all_restaurants()
        recs = sample_graph.get_recommendations(all_r[0].business_id)
        assert isinstance(recs, list)

    def test_recommendations_do_not_include_starting_restaurant(self, sample_graph):
        all_r = sample_graph.get_all_restaurants()
        target_id = all_r[0].business_id
        recs = sample_graph.get_recommendations(target_id)
        ids = [r.business_id for r in recs]
        assert target_id not in ids

    def test_recommendations_respect_n_limit(self, sample_graph):
        all_r = sample_graph.get_all_restaurants()
        recs = sample_graph.get_recommendations(all_r[0].business_id, n=3)
        assert len(recs) <= 3

    def test_single_node_graph_returns_no_recommendations(self):
        g = RestaurantGraph()
        r = Restaurant("solo", "Lone Restaurant", ["Burgers"], "$", 4.0, "X", 42.0, -83.0)
        g.add_restaurant(r)
        g.build_edges()
        assert g.get_recommendations("solo") == []


class TestPathFinding:
    def test_path_exists_between_connected_restaurants(self, sample_graph):
        all_r = sample_graph.get_all_restaurants()
        for i in range(len(all_r)):
            for j in range(i + 1, len(all_r)):
                path = sample_graph.find_path(all_r[i].business_id, all_r[j].business_id)
                if path is not None:
                    assert len(path) >= 2
                    return
        pytest.skip("No connected pairs found in sample graph")

    def test_path_starts_and_ends_at_correct_restaurants(self, sample_graph):
        all_r = sample_graph.get_all_restaurants()
        for i in range(len(all_r)):
            for j in range(i + 1, len(all_r)):
                path = sample_graph.find_path(all_r[i].business_id, all_r[j].business_id)
                if path is not None:
                    assert path[0].business_id == all_r[i].business_id
                    assert path[-1].business_id == all_r[j].business_id
                    return

    def test_path_with_invalid_end_id_returns_none(self, small_graph):
        result = small_graph.find_path("biz001", "nonexistent")
        assert result is None

    def test_path_with_both_invalid_ids_returns_none(self, small_graph):
        result = small_graph.find_path("fake1", "fake2")
        assert result is None


class TestEdgeCases:
    def test_empty_graph_has_zero_nodes_and_edges(self):
        g = RestaurantGraph()
        assert g.node_count == 0
        assert g.edge_count == 0

    def test_empty_graph_search_returns_empty(self):
        g = RestaurantGraph()
        assert g.search_by_name("anything") == []
        assert g.get_all_restaurants() == []
        assert g.get_restaurant("none") is None

    def test_get_restaurant_not_in_graph_returns_none(self, small_graph):
        assert small_graph.get_restaurant("does_not_exist") is None

    def test_get_neighbors_for_unknown_id_returns_empty(self, small_graph):
        assert small_graph.get_neighbors("unknown") == []

    def test_building_edges_twice_does_not_duplicate(self, small_graph):
        edges_before = small_graph.edge_count
        small_graph.build_edges(min_shared=2)
        assert small_graph.edge_count == edges_before

    def test_get_all_neighborhoods_returns_list(self, sample_graph):
        hoods = sample_graph.get_all_neighborhoods()
        assert isinstance(hoods, list)
        assert len(hoods) > 0

    def test_get_all_cuisines_contains_expected_values(self, sample_graph):
        cuisines = sample_graph.get_all_cuisines()
        assert isinstance(cuisines, list)
        assert "Korean" in cuisines or "Italian" in cuisines
