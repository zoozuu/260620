import streamlit as st
import pandas as pd
import requests
import pydeck as pdk
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
                "시간": datetime.fromtimestamp(prop["time"] / 1000).strftime("%Y-%m-%d %H:%M:%S"),
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
    st.warning("표시할 지진 데이터가 없습니다.")
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

# 지도
st.subheader("🗺️ 지진 발생 위치")

largest = filtered.loc[filtered["규모"].idxmax()]

# 규모별 색상
def color_by_mag(mag):
    if mag >= 7:
        return [255, 0, 0, 180]
    elif mag >= 5:
        return [255, 140, 0, 180]
    else:
        return [255, 215, 0, 160]

filtered = filtered.copy()
filtered["color"] = filtered["규모"].apply(color_by_mag)

scatter_layer = pdk.Layer(
    "ScatterplotLayer",
    data=filtered,
    get_position='[경도, 위도]',
    get_radius='규모 * 12000',
    get_fill_color='color',
    pickable=True,
    opacity=0.8
)

# 가장 강한 지진 강조
highlight_layer = pdk.Layer(
    "ScatterplotLayer",
    data=pd.DataFrame([largest]),
    get_position='[경도, 위도]',
    get_radius=150000,
    get_fill_color='[255,0,0,220]',
    pickable=True,
    opacity=0.4
)

tooltip = {
    "html": """
    <div style="font-size:14px;">
        <b>📍 위치</b><br/>
        {위치}<br/><br/>
        <b>🌋 규모</b> : {규모}<br/>
        <b>📏 깊이</b> : {깊이(km)} km<br/>
        <b>🕒 시간</b><br/>
        {시간}
    </div>
    """,
    "style": {
        "backgroundColor": "#111111",
        "color": "white"
    }
}

view_state = pdk.ViewState(
    latitude=filtered["위도"].mean(),
    longitude=filtered["경도"].mean(),
    zoom=1.3,
    pitch=0
)

deck = pdk.Deck(
    layers=[
        scatter_layer,
        highlight_layer
    ],
    initial_view_state=view_state,
    tooltip=tooltip,
    map_style="mapbox://styles/mapbox/dark-v10"
)

st.pydeck_chart(deck)

st.info(
    f"🚨 현재 가장 강한 지진 : 규모 {largest['규모']:.1f} | {largest['위치']}"
)

st.divider()

# 규모 분포
st.subheader("📊 규모 분포")

chart_data = (
    filtered["규모"]
    .round()
    .value_counts()
    .sort_index()
)

st.bar_chart(chart_data)

st.divider()

# TOP10
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
        "규모",
        ascending=False
    ),
    use_container_width=True,
    hide_index=True
)
