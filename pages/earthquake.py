import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(
    page_title="실시간 세계 지진 모니터링",
    page_icon="🌍",
    layout="wide"
)

URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"

@st.cache_data(ttl=300)
def load_data():
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()

        data = response.json()

        rows = []

        for feature in data["features"]:
            prop = feature["properties"]
            geo = feature["geometry"]

            mag = prop.get("mag")

            if mag is None:
                continue

            rows.append({
                "시간": datetime.fromtimestamp(prop["time"] / 1000),
                "규모": float(mag),
                "위치": prop.get("place", "정보 없음"),
                "위도": geo["coordinates"][1],
                "경도": geo["coordinates"][0],
                "깊이(km)": geo["coordinates"][2]
            })

        return pd.DataFrame(rows)

    except Exception as e:
        st.error(f"데이터를 불러오지 못했습니다.\n{e}")
        return pd.DataFrame()

st.title("🌍 실시간 세계 지진 모니터링")

if st.button("새로고침"):
    st.cache_data.clear()
    st.rerun()

df = load_data()

if df.empty:
    st.warning("표시할 지진 데이터가 없습니다.")
    st.stop()

min_mag = st.sidebar.slider(
    "최소 규모",
    min_value=0.0,
    max_value=10.0,
    value=3.0,
    step=0.1
)

filtered = df[df["규모"] >= min_mag]

if filtered.empty:
    st.warning("조건에 맞는 지진이 없습니다.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)

col1.metric("총 지진 수", len(filtered))
col2.metric("최대 규모", f"{filtered['규모'].max():.1f}")
col3.metric("평균 규모", f"{filtered['규모'].mean():.2f}")
col4.metric("규모 5 이상", len(filtered[filtered["규모"] >= 5]))

st.subheader("🗺️ 지진 발생 위치")

map_df = filtered.rename(
    columns={
        "위도": "lat",
        "경도": "lon"
    }
)

st.map(map_df[["lat", "lon"]])

st.subheader("📊 규모 분포")

chart_data = (
    filtered["규모"]
    .round()
    .value_counts()
    .sort_index()
)

st.bar_chart(chart_data)

st.subheader("🚨 규모 상위 10개 지진")

top10 = filtered.sort_values(
    "규모",
    ascending=False
).head(10)

st.dataframe(
    top10,
    use_container_width=True
)

st.subheader("📋 전체 지진 목록")

st.dataframe(
    filtered.sort_values(
        "시간",
        ascending=False
    ),
    use_container_width=True
)
