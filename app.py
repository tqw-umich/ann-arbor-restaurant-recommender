"""
SI 507 Final Project - Ann Arbor Restaurant Recommendation Network
app.py: Streamlit interface with four interaction modes.

Run with:
    streamlit run app.py

To use the full Yelp dataset instead of sample data, set:
    export YELP_BUSINESS_JSON=/path/to/yelp_academic_dataset_business.json

To enable the dining narrative feature (Mode 4), set:
    export ANTHROPIC_API_KEY=your_api_key_here
"""

import os
import streamlit as st
from data_loader import build_graph, build_sample_graph

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Ann Arbor Eats",
    page_icon="🍽️",
    layout="wide",
)

# ─── Load graph (cached so it only builds once per session) ──────────────────
@st.cache_resource
def load_graph():
    data_path = os.environ.get("YELP_BUSINESS_JSON", "")
    if data_path and os.path.exists(data_path):
        return build_graph(data_path)
    return build_sample_graph()


graph = load_graph()

# ─── Sidebar navigation ───────────────────────────────────────────────────────
st.sidebar.title("🍽️ Ann Arbor Eats")
st.sidebar.markdown(f"**{graph.node_count} restaurants** · **{graph.edge_count} connections**")
st.sidebar.markdown("---")

mode = st.sidebar.radio(
    "Choose a mode",
    [
        "🔍 Search",
        "📋 Restaurant Detail",
        "⭐ Recommendations",
        "🌙 Dining Path",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "Built with [Yelp Open Dataset](https://www.yelp.com/dataset) · SI 507 Final Project"
)


# ─── Mode 1: Search ──────────────────────────────────────────────────────────
if mode == "🔍 Search":
    st.title("🔍 Search Restaurants")
    st.markdown("Search by restaurant name or cuisine type.")

    col1, col2 = st.columns(2)
    with col1:
        name_query = st.text_input("Search by name", placeholder="e.g. Zingerman")
    with col2:
        cuisine_query = st.text_input("Search by cuisine", placeholder="e.g. Korean, Pizza, BBQ")

    all_hoods = ["All"] + graph.get_all_neighborhoods()
    selected_hood = st.selectbox("Filter by neighborhood", all_hoods)

    price_options = ["All", "$", "$$", "$$$", "$$$$"]
    selected_price = st.selectbox("Filter by price range", price_options)

    min_rating = st.slider("Minimum rating", 1.0, 5.0, 3.5, step=0.5)

    if name_query:
        results = graph.search_by_name(name_query)
    elif cuisine_query:
        results = graph.search_by_cuisine(cuisine_query)
    else:
        results = graph.get_all_restaurants()

    if selected_hood != "All":
        results = [r for r in results if r.neighborhood == selected_hood]
    if selected_price != "All":
        results = [r for r in results if r.price == selected_price]
    results = [r for r in results if r.rating >= min_rating]

    st.markdown(f"**{len(results)} results found**")

    if not results:
        st.info("No restaurants match your filters. Try adjusting the criteria.")
    else:
        for r in results[:30]:
            with st.expander(
                f"{r.name}  ·  {'⭐' * round(r.rating)} {r.rating}  ·  {r.price or '?'}  ·  {r.neighborhood}"
            ):
                st.write(f"**Cuisine:** {', '.join(r.categories[:4]) if r.categories else 'N/A'}")
                st.write(f"**Address:** {r.address or 'N/A'}")
                st.write(f"**Reviews:** {r.review_count:,}")
                neighbor_count = len(graph.get_neighbors(r.business_id))
                st.write(f"**Graph connections:** {neighbor_count} similar restaurants")


# ─── Mode 2: Restaurant Detail ───────────────────────────────────────────────
elif mode == "📋 Restaurant Detail":
    st.title("📋 Restaurant Detail")
    st.markdown("Pick a restaurant to see its full profile and graph neighbors.")

    all_restaurants = sorted(graph.get_all_restaurants(), key=lambda x: x.name)
    options = {r.name: r.business_id for r in all_restaurants}

    selected_name = st.selectbox("Choose a restaurant", list(options.keys()))
    selected_id = options[selected_name]
    r = graph.get_restaurant(selected_id)

    if r:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader(r.name)
            st.markdown(f"**Neighborhood:** {r.neighborhood}")
            st.markdown(f"**Cuisine:** {', '.join(r.categories) if r.categories else 'N/A'}")
            st.markdown(f"**Price:** {r.price or 'Unknown'}")
            st.markdown(f"**Rating:** {'⭐' * round(r.rating)} {r.rating} ({r.review_count:,} reviews)")
            st.markdown(f"**Address:** {r.address or 'N/A'}")
            st.markdown(f"**Coordinates:** {r.lat:.4f}, {r.lon:.4f}")
        with col2:
            st.metric("Rating", f"{r.rating} ⭐")
            st.metric("Reviews", f"{r.review_count:,}")
            neighbors = graph.get_neighbors(r.business_id)
            st.metric("Graph neighbors", len(neighbors))

        st.markdown("---")
        st.subheader("🔗 Graph Neighbors")
        st.markdown("These restaurants share at least 2 features with this one.")

        if not neighbors:
            st.info("This restaurant has no direct connections in the graph.")
        else:
            for n in neighbors[:10]:
                shared = n.shares_features_with(r)
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.write(f"**{n.name}** · {n.neighborhood} · {', '.join(n.categories[:2])}")
                with col_b:
                    st.write(f"{n.rating}⭐ · {shared} shared features")


# ─── Mode 3: Recommendations ─────────────────────────────────────────────────
elif mode == "⭐ Recommendations":
    st.title("⭐ Restaurant Recommendations")
    st.markdown("Pick a restaurant you like and we'll suggest similar ones.")

    all_restaurants = sorted(graph.get_all_restaurants(), key=lambda x: x.name)
    options = {r.name: r.business_id for r in all_restaurants}

    selected_name = st.selectbox("I like this restaurant...", list(options.keys()))
    selected_id = options[selected_name]
    n_recs = st.slider("Number of recommendations", 3, 10, 5)

    recs = graph.get_recommendations(selected_id, n=n_recs)
    base = graph.get_restaurant(selected_id)

    if not recs:
        st.warning(
            f"No recommendations found for **{base.name}**. "
            "This restaurant may not have enough connections in the graph."
        )
    else:
        st.markdown(f"**Because you like {base.name}...**")
        for i, r in enumerate(recs, 1):
            shared = r.shares_features_with(base)
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{i}. {r.name}**")
                    st.caption(
                        f"{r.neighborhood} · {', '.join(r.categories[:3]) if r.categories else 'N/A'}"
                    )
                with col2:
                    st.metric("Rating", f"{r.rating}⭐")
                with col3:
                    st.metric("Price", r.price or "?")
                st.progress(shared / 4.0, text=f"{shared}/4 features match")
                st.divider()


# ─── Mode 4: Dining Path + LLM Narrative ─────────────────────────────────────
elif mode == "🌙 Dining Path":
    st.title("🌙 Plan Your Evening")
    st.markdown(
        "Pick two restaurants and we'll find a path through the graph "
        "connecting them stop by stop. Then generate a narrative of your evening."
    )

    all_restaurants = sorted(graph.get_all_restaurants(), key=lambda x: x.name)
    names = [r.name for r in all_restaurants]
    id_map = {r.name: r.business_id for r in all_restaurants}

    col1, col2 = st.columns(2)
    with col1:
        start_name = st.selectbox("Start at...", names, index=0)
    with col2:
        end_name = st.selectbox("End at...", names, index=min(4, len(names) - 1))

    if start_name == end_name:
        st.warning("Please choose two different restaurants.")
    else:
        if st.button("🗺️ Find Path", type="primary"):
            start_id = id_map[start_name]
            end_id = id_map[end_name]
            path = graph.find_path(start_id, end_id)

            if path is None:
                st.error(
                    "No path found between these two restaurants. "
                    "They may be in disconnected parts of the graph. Try a different pair."
                )
            else:
                # Store path in session state so the narrative button can use it
                st.session_state["current_path"] = path

        # ── Display path if one exists in session state ──
        path = st.session_state.get("current_path")

        if path and path[0].name == start_name and path[-1].name == end_name:
            st.subheader(f"Your Evening Route  ·  {len(path)} stops")

            for i, r in enumerate(path):
                with st.container():
                    col_num, col_info, col_meta = st.columns([1, 4, 2])
                    with col_num:
                        st.markdown(f"### {i + 1}")
                    with col_info:
                        st.markdown(f"**{r.name}**")
                        st.caption(
                            f"{r.neighborhood}  ·  "
                            f"{', '.join(r.categories[:3]) if r.categories else 'N/A'}"
                        )
                        st.caption(r.address or "")
                    with col_meta:
                        st.metric("Rating", f"{r.rating}⭐")
                        st.write(f"Price: {r.price or '?'}")
                    if i < len(path) - 1:
                        next_r = path[i + 1]
                        shared = r.shares_features_with(next_r)
                        st.caption(f"↓ connected by {shared} shared features")
                    st.divider()

            st.subheader("Why these stops are connected")
            for i in range(len(path) - 1):
                r1, r2 = path[i], path[i + 1]
                shared_cats = set(r1.categories) & set(r2.categories)
                same_hood = r1.neighborhood == r2.neighborhood
                same_price = r1.price == r2.price
                close_rating = abs(r1.rating - r2.rating) <= 0.5
                reasons = []
                if shared_cats:
                    reasons.append(f"both serve {', '.join(list(shared_cats)[:2])}")
                if same_hood:
                    reasons.append(f"both in {r1.neighborhood}")
                if same_price:
                    reasons.append(f"same price range ({r1.price})")
                if close_rating:
                    reasons.append("similar ratings")
                st.write(f"**{r1.name}** → **{r2.name}**: {', '.join(reasons)}")

            # ── LLM Narrative Section ──────────────────────────────────────────
            st.markdown("---")
            st.subheader("✨ Dining Narrative")

            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if not api_key:
                st.info(
                    "💡 **Want a narrated version of your evening?** "
                    "Set the `ANTHROPIC_API_KEY` environment variable and rerun the app.\n\n"
                    "```bash\nexport ANTHROPIC_API_KEY=your_key_here\nstreamlit run app.py\n```"
                )
            else:
                if st.button("✨ Generate Dining Story", type="secondary"):
                    with st.spinner("Writing your evening story..."):
                        try:
                            import anthropic

                            # Build a structured summary of the path for the prompt
                            stops_text = "\n".join(
                                f"{i+1}. {r.name} — {r.neighborhood}, "
                                f"{', '.join(r.categories[:3]) if r.categories else 'N/A'}, "
                                f"{r.price or '?'}, {r.rating}⭐"
                                for i, r in enumerate(path)
                            )

                            connections_text = "\n".join(
                                f"  {path[i].name} → {path[i+1].name}: "
                                + ", ".join(
                                    filter(None, [
                                        f"both {list(set(path[i].categories) & set(path[i+1].categories))[0]}" if set(path[i].categories) & set(path[i+1].categories) else "",
                                        f"same neighborhood ({path[i].neighborhood})" if path[i].neighborhood == path[i+1].neighborhood else "",
                                        f"same price range ({path[i].price})" if path[i].price == path[i+1].price else "",
                                        "similar vibe" if abs(path[i].rating - path[i+1].rating) <= 0.5 else "",
                                    ])
                                )
                                for i in range(len(path) - 1)
                            )

                            prompt = (
                                f"Write a short, vivid dining narrative (150–200 words) for an evening "
                                f"in Ann Arbor that starts at {path[0].name} and ends at {path[-1].name}. "
                                f"The stops in order are:\n\n{stops_text}\n\n"
                                f"Each stop connects to the next because:\n{connections_text}\n\n"
                                f"Make it feel like an actual evening out — warm, specific, and fun. "
                                f"Mention each restaurant by name and weave in why each transition makes sense."
                            )

                            client = anthropic.Anthropic(api_key=api_key)
                            message = client.messages.create(
                                model="claude-haiku-4-5-20251001",
                                max_tokens=400,
                                messages=[{"role": "user", "content": prompt}],
                            )

                            narrative = message.content[0].text
                            st.session_state["narrative"] = narrative

                        except Exception as e:
                            st.error(f"Could not generate narrative: {e}")

                # Display narrative if it exists
                if "narrative" in st.session_state:
                    st.markdown(
                        f"""
                        <div style="
                            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                            border-left: 4px solid #e2b96f;
                            border-radius: 8px;
                            padding: 1.5rem 2rem;
                            color: #f0e6d3;
                            font-size: 1.05rem;
                            line-height: 1.7;
                            font-style: italic;
                            margin-top: 1rem;
                        ">
                        {st.session_state["narrative"]}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.caption("✨ Your evening, narrated.")
