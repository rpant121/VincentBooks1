import streamlit as st
import requests
import pandas as pd
import random

# --- Streamlit page config ---
st.set_page_config(page_title="Fable Book Explorer", layout="wide")
st.title("📚 Fable Book Explorer")
st.caption("Browse and analyze books from a Fable reading list (API-powered).")

# --- Constants ---
BASE_URL = "https://api.fable.co/api/v2/users/0c031026-9f1f-4a02-889c-79d2bdb11781/book_lists/33f803be-3e8d-4ed6-bd19-79a330d2bb32/books"
HEADERS = {"User-Agent": "Mozilla/5.0"}

@st.cache_data(show_spinner=False)
def fetch_all_books():
    """Fetch all paginated books from the Fable API."""
    all_books = []
    url = BASE_URL

    while url:
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if not results:
            break

        for item in results:
            book = item.get("book", {})
            all_books.append(book)

        url = data.get("next")

    # --- Format into DataFrame ---
    rows = []
    for b in all_books:
        authors = b.get("authors", [])
        genres = b.get("genres", [])
        rows.append({
            "title": b.get("title"),
            "subtitle": b.get("subtitle"),
            "author": authors[0]["name"] if authors else None,
            "genre": genres[0]["name"] if genres else "Unknown",
            "pages": b.get("page_count"),
            "isbn": b.get("isbn"),
            "published_date": b.get("published_date"),
            "imprint": b.get("imprint"),
            "cover_image": b.get("cover_image"),
            "book_url": f"https://fable.co/book/{b.get('id')}" if b.get("id") else None,
            "started_reading": b.get("started_reading_at"),
            "finished_reading": b.get("finished_reading_at")
        })
    return pd.DataFrame(rows)

# --- UI: Fetch button ---
if st.button("🔄 Fetch Books from Fable"):
    with st.spinner("Fetching books..."):
        df = fetch_all_books()
        st.success(f"✅ Fetched {len(df)} books successfully!")

        # --- Sidebar filters ---
        st.sidebar.header("🔍 Filters & Sorting")

        search = st.sidebar.text_input("Search title or author")
        selected_genres = st.sidebar.multiselect("Filter by genre", sorted(df["genre"].unique()))
        sort_by = st.sidebar.selectbox("Sort by", ["title", "author", "published_date"])
        ascending = st.sidebar.checkbox("Ascending", value=True)

        # --- Filtering logic ---
        filtered_df = df.copy()
        if search:
            filtered_df = filtered_df[
                filtered_df["title"].str.contains(search, case=False, na=False) |
                filtered_df["author"].str.contains(search, case=False, na=False)
            ]
        if selected_genres:
            filtered_df = filtered_df[filtered_df["genre"].isin(selected_genres)]

        filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)

        # --- Genre color map ---
        unique_genres = sorted(filtered_df["genre"].unique())
        genre_colors = {
            g: f"#{random.randint(0, 0xFFFFFF):06x}" for g in unique_genres
        }

        # --- Data Table ---
        st.subheader("📊 Book Data")
        st.dataframe(filtered_df[["title", "author", "genre", "pages", "published_date", "started_reading", "finished_reading"]])

        # --- Download Button ---
        csv = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "💾 Download CSV",
            data=csv,
            file_name="fable_books.csv",
            mime="text/csv"
        )

        # --- Gallery View ---
        st.subheader("📖 Book Gallery")
        for _, row in filtered_df.iterrows():
            with st.container():
                cols = st.columns([1, 3])
                with cols[0]:
                    if row["cover_image"]:
                        st.image(row["cover_image"], width=110)
                with cols[1]:
                    title = row.get("title", "Untitled")
                    url = row.get("book_url", "")
                    st.markdown(f"**[{title}]({url})**")

                    if row.get("author"):
                        st.write(f"*by {row['author']}*")

                    genre_color = genre_colors.get(row["genre"], "#888888")
                    st.markdown(
                        (
                            f'<span style="background-color:{genre_color}; color:white; '
                            f'padding:3px 8px; border-radius:6px; font-size:0.85em;">'
                            f'{row["genre"]}</span>'
                        ),
                        unsafe_allow_html=True,
                    )

                    if row.get("published_date"):
                        st.caption(f"Published: {row['published_date']}")
else:
    st.info("Click the button above to fetch books from Fable.")
