import streamlit as st
from notion_client import Client
import pandas as pd
from datetime import datetime, timedelta
import requests
import plotly.express as px

st.set_page_config(page_title="🏃‍♂️ 런닝 대시보드", layout="wide")

# Secrets 로드
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
WEATHER_API_KEY = st.secrets["OPENWEATHER_API_KEY"]

@st.cache_data(ttl=600)
def load_data():
    notion = Client(auth=NOTION_TOKEN)
    results = notion.databases.query(database_id=DATABASE_ID)
    data = []
    for page in results['results']:
        props = page['properties']
        data.append({
            '날짜': props.get('날짜', {}).get('date', {}).get('start', ''),
            '거리(km)': float(props.get('거리', {}).get('number', 0) or 0),
            '시간': props.get('시간', {}).get('rich_text', [{}])[0].get('plain_text', ''),
            '평균페이스': props.get('평균페이스', {}).get('rich_text', [{}])[0].get('plain_text', ''),
            '심박수': props.get('심박수', {}).get('number', 0) or 0,
            '상태': props.get('상태', {}).get('select', {}).get('name', '')
        })
    return pd.DataFrame(data)

# 데이터 로드
df = load_data()
df['날짜'] = pd.to_datetime(df['날짜'])
recent = df.tail(30).copy()

def time_to_seconds(t):
    if not t: return 0
    h, m, s = map(int, t.split(':'))
    return h*3600 + m*60 + s

recent['페이스'] = recent['시간'].apply(time_to_seconds) / (recent['거리(km)'] * 60)

st.title("🏃‍♂️ 런닝 대시보드")

# 날씨
col1, col2 = st.columns(2)
try:
    r = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q=Seoul&appid={WEATHER_API_KEY}&units=metric").json()
    col1.metric("🌡️", f"{r['main']['temp']}°C")
    col2.metric("☁️", r['weather'][0]['description'])
except: pass

# 통계 카드
c1, c2, c3, c4 = st.columns(4)
c1.metric("📏 총거리", f"{recent['거리(km)'].sum():.1f}km")
c2.metric("🏃 횟수", len(recent))
c3.metric("⏱️ 페이스", f"{recent['페이스'].mean():.1f}'/km")
c4.metric("❤️ 심박", f"{recent['심박수'].mean():.0f}bpm")

# 그래프
c1, c2 = st.columns(2)
with c1: st.plotly_chart(px.line(recent, x='날짜', y='거리(km)', title="거리"), use_container_width=True)
with c2: st.plotly_chart(px.line(recent, x='날짜', y='페이스', title="페이스"), use_container_width=True)

st.subheader("📋 최근 기록")
st.dataframe(recent[['날짜', '거리(km)', '평균페이스', '심박수', '상태']].tail(10))
