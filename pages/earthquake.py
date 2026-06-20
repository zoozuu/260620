import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(
    page_title="실시간 세계 지진 모니터링",
    page_icon="🌍",
    layout="wide"
)

# USGS API
URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"


@st.cache_data(ttl=300)
def load_earthquake_data():
    response = requests.get(URL)
    data = response.json()

    earthquakes = []

    for feature in data["features"]:
        properties = feature["properties"]
        geometry = feature["geometry"]

        earthquakes.append({
            "시간": datetime.fromtimestamp(
                properties["time"] / 1000
            ),
            "규모": properties["mag"],
            "위치": properties["place"],
            "위도": geometry["coordinates"][1],
            "경도": geometry["coordinates"][0],
            "깊이(km)": geometry["coordinates"][2]
        })

    return pd.DataFrame(earthquakes)


# 제목
st.title("🌍 실시간 세계 지진 모니터링")
st.caption("USGS Earthquake API 기반")

# 새로고침
if st.button("🔄 데이터 새로고침"):
    st.cache_data.clear()

# 데이터 로드
df = load_earthquake_data()

# 사이드바
st.sidebar.header("필터")

min_mag = st.sidebar.slider(
    "최소 규모",
    0.0,
    10.0,
    3.0,
    0.1
)

filtered_df = df[df["규모"] >= min_mag]

# 통계
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "총 지진 수",
        len(filtered_df)
    )

with col2:
    st.metric(
        "최대 규모",
        f"{filtered_df['규모'].max():.1f}"
    )

with col3:
    st.metric(
        "평균 규모",
        f"{filtered_df['규모'].mean():.2f}"
    )

with col4:
    st.metric(
        "규모 5 이상",
        len(filtered_df[filtered_df["규모"] >= 5])
    )

st.divider()

# 지도
st.subheader("🗺️ 지진 발생 위치")

map_df = filtered_df[["위도", "경도"]]
map_df.columns = ["lat", "lon"]

st.map(map_df)

st.divider()

# 규모별 분포
st.subheader("📊 규모 분포")

mag_count = (
    filtered_df["규모"]
    .round()
    .value_counts()
    .sort_index()
)

st.bar_chart(mag_count)

st.divider()

# 최근 강한 지진
st.subheader("🚨 규모가 큰 지진 TOP 10")

top10 = (
    filtered_df
    .sort_values("규모", ascending=False)
    .head(10)
)

st.dataframe(
    top10[["시간", "규모", "위치", "깊이(km)"]],
    use_container_width=True
)

st.divider()

# 전체 목록
st.subheader("📋 최근 지진 목록")

display_df = filtered_df.sort_values(
    "시간",
    ascending=False
)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)
