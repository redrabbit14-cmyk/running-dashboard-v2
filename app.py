import streamlit as st
from notion_client import Client
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime
import numpy as np

# 페이지 설정 - 모바일 최적화
st.set_page_config(
    page_title="🏃‍♂️ 런닝 대시보드", 
    page_icon="🏃‍♂️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Secrets 로드
@st.cache_data(ttl=60)
def load_secrets():
    return {
        "NOTION_TOKEN": st.secrets["NOTION_TOKEN"],
        "DATABASE_ID": st.secrets["DATABASE_ID"],
        "WEATHER_API_KEY": st.secrets["OPENWEATHER_API_KEY"]
    }

secrets = load_secrets()

@st.cache_data(ttl=1800)  # 30분 캐시
def load_notion_data():
    notion = Client(auth=secrets["NOTION_TOKEN"])
    results = notion.databases.query(database_id=secrets["DATABASE_ID"])
    
    data = []
    for page in results['results']:
        props = page['properties']
        row = {
            '날짜': props.get('날짜', {}).get('date', {}).get('start', ''),
            '거리(km)': float(props.get('거리', {}).get('number', 0) or 0),
            '시간': props.get('시간', {}).get('rich_text', [{}])[0].get('plain_text', '0:00:00'),
            '평균페이스': props.get('평균페이스', {}).get('rich_text', [{}])[0].get('plain_text', ''),
            '심박수': float(props.get('심박수', {}).get('number', 0) or 0),
            '상태': props.get('상태', {}).get('select', {}).get('name', '기타'),
            '날씨': props.get('날씨', {}).get('select', {}).get('name', '')
        }
        data.append(row)
    df = pd.DataFrame(data)
    df['날짜'] = pd.to_datetime(df['날짜'])
    return df.sort_values('날짜', ascending=False)

def get_weather():
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q=Seoul&appid={secrets['WEATHER_API_KEY']}&units=metric&lang=ko"
        resp = requests.get(url, timeout=5).json()
        return {
            'temp': resp['main']['temp'],
            'humidity': resp['main']['humidity'],
            'desc': resp['weather'][0]['description']
        }
    except:
        return None

def parse_time(time_str):
    if pd.isna(time_str) or time_str == '0:00:00': return 0
    try:
        parts = time_str.split(':')
        if len(parts) == 3:
            return int(parts[0])*3600 + int(parts[1])*60 + int(parts[2])
    except:
        pass
    return 0

# 메인 앱
st.title("🏃‍♂️ 런닝 대시보드")

# 현재 날씨
weather_data = get_weather()
col1, col2, col3 = st.columns(3)
if weather_data:
    col1.metric("🌡️ 서울", f"{weather_data['temp']}°C")
    col2.metric("💧", f"{weather_data['humidity']}%")
    col3.metric("☁️", weather_data['desc'])

st.markdown("---")

# 데이터 로드
try:
    df = load_notion_data()
    if df.empty:
        st.warning("⚠️ 노션 데이터베이스에 런닝 기록이 없습니다.")
        st.stop()
    st.success(f"✅ {len(df)}개 런닝 기록 로드 완료!")
except Exception as e:
    st.error(f"❌ 데이터 로드 실패: {str(e)[:100]}")
    st.stop()

# 최근 30일 데이터
recent_df = df.tail(30).copy()
recent_df['시간_초'] = recent_df['시간'].apply(parse_time)
recent_df['페이스_분km'] = recent_df['시간_초'] / (recent_df['거리(km)'] * 60)

# 2x2 통계 카드
col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

with col1:
    total_dist = recent_df['거리(km)'].sum()
    st.metric("📏 총거리", f"{total_dist:.1f}km")

with col2:
    st.metric("🏃 런닝횟수", f"{len(recent_df)}회")

with col3:
    avg_pace = recent_df['페이스_분km'].mean()
    st.metric("⏱️ 평균페이스", f"{avg_pace:.1f}'/km")

with col4:
    avg_hr = recent_df['심박수'].mean()
    st.metric("❤️ 평균심박", f"{avg_hr:.0f}bpm")

# 그래프
st.markdown("### 📊 런닝 추이")
col1, col2 = st.columns(2)

with col1:
    fig_dist = px.line(recent_df, x='날짜', y='거리(km)', 
                      title="거리추이", markers=True)
    fig_dist.update_layout(height=300, showlegend=False, margin=dict(t=40))
    st.plotly_chart(fig_dist, use_container_width=True)

with col2:
    fig_pace = px.line(recent_df, x='날짜', y='페이스_분km', 
                      title="페이스추이", markers=True)
    fig_pace.update_layout(height=300, showlegend=False, margin=dict(t=40))
    st.plotly_chart(fig_pace, use_container_width=True)

# 최근 기록 테이블
st.markdown("### 📋 최근 10회 기록")
st.dataframe(
    recent_df[['날짜', '거리(km)', '평균페이스', '심박수', '상태', '날씨']].head(10),
    use_container_width=True, hide_index=True
)

# 상태별 파이차트
if '상태' in recent_df.columns and len(recent_df['상태'].value_counts()) > 1:
    st.markdown("### 🎯 상태분포")
    status_counts = recent_df['상태'].value_counts()
    fig_pie = px.pie(values=status_counts.values, names=status_counts.index)
    fig_pie.update_layout(height=350)
    st.plotly_chart(fig_pie, use_container_width=True)

# 모바일 CSS
st.markdown("""
<style>
    [data-testid="stSidebar"] { display: none !important; }
    .main .block-container { padding: 1rem; }
    @media (max-width: 768px) {
        .main .block-container { padding: 0.5rem; }
    }
</style>
""", unsafe_allow_html=True)
