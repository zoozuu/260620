import streamlit as st
import pandas as pd
import requests
import plotly.express as px
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

        earthquakes = []

        for feature in data["features"]:
            prop = feature["properties"]
            geo = feature["geometry"]

            mag = prop.get("mag")

            if mag is None:
                continue

            earthquakes.append({
                "시간": datetime.fromtimestamp(
                    prop["time"] / 1000
                ).strftime("%Y-%m-%d %H:%M:%S"),
                "규모": float(mag),
                "위치": prop.get("place", "정보 없음"),
                "위도": geo["coordinates"][1],
                "경도": geo["coordinates"][0],
                "깊이(km)": geo["coordinates"][2]
            })

        return pd.DataFrame(earthquakes)

    except Exception as e:
        st.error(f"데이터를 불러오지 못했습니다.\n{e}")
        return pd.DataFrame()


# 제목
st.title("🌍 실시간 세계 지진 모니터링")
st.caption("USGS Earthquake API 기반")

# 새로고침
if st.button("🔄 데이터 새로고침"):
    st.cache_data.clear()
    st.rerun()

# 데이터 로드
df = load_data()

if df.empty:
    st.warning("지진 데이터를 불러오지 못했습니다.")
    st.stop()

# 사이드바
st.sidebar.header("필터")

min_mag = st.sidebar.slider(
    "최소 규모",
    0.0,
    10.0,
    3.0,
    0.1
)

filtered = df[df["규모"] >= min_mag]

if filtered.empty:
    st.warning("조건에 맞는 지진이 없습니다.")
    st.stop()

# 통계 카드
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("총 지진 수", len(filtered))

with col2:
    st.metric("최대 규모", f"{filtered['규모'].max():.1f}")

with col3:
    st.metric("평균 규모", f"{filtered['규모'].mean():.2f}")

with col4:
    st.metric(
        "규모 5 이상",
        len(filtered[filtered["규모"] >= 5])
    )

st.divider()

# 가장 큰 지진
largest = filtered.loc[
    filtered["규모"].idxmax()
]

st.info(
    f"🚨 현재 가장 강한 지진 : 규모 {largest['규모']:.1f} | {largest['위치']}"
)

# 지도
st.subheader("🗺️ 세계 지진 지도")

filtered = filtered.copy()

filtered["강조"] = "일반"

filtered.loc[
    filtered["규모"] == filtered["규모"].max(),
    "강조"
] = "최대 규모"

fig = px.scatter_geo(
    filtered,
    lat="위도",
    lon="경도",
    size="규모",
    color="강조",
    hover_name="위치",
    hover_data={
        "규모": True,
        "깊이(km)": True,
        "시간": True,
        "위도": False,
        "경도": False,
        "강조": False
    },
    projection="natural earth",
    size_max=35
)

fig.update_layout(
    height=700,
    margin=dict(l=0, r=0, t=0, b=0),
    legend_title="지진 유형"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.divider()

# 규모 분포
st.subheader("📊 규모 분포")

mag_dist = (
    filtered["규모"]
    .round()
    .value_counts()
    .sort_index()
)

st.bar_chart(mag_dist)

st.divider()

# 규모 TOP10
st.subheader("🚨 규모 상위 10개 지진")

top10 = (
    filtered
    .sort_values("규모", ascending=False)
    .head(10)
)

st.dataframe(
    top10,
    use_container_width=True,
    hide_index=True
)

st.divider()

# 전체 목록
st.subheader("📋 전체 지진 목록")

st.dataframe(
    filtered.sort_values(
        "시간",
        ascending=False
    ),
    use_container_width=True,
    hide_index=True
)
