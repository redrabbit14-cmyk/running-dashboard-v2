import streamlit as st
from notion_client import Client

st.set_page_config(layout="wide")
st.title("🔍 노션 데이터 구조 진단")

# Secrets
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]

st.success("✅ Secrets 연결됨")

# Notion 연결 테스트
notion = Client(auth=NOTION_TOKEN)
results = notion.databases.query(database_id=DATABASE_ID)

st.subheader("📊 데이터베이스 구조")
if results['results']:
    first_page = results['results'][0]
    props = first_page['properties']
    
    st.json(props)  # 실제 속성 이름 표시
    
    st.subheader("첫 번째 기록 미리보기")
    for key, value in props.items():
        st.write(f"**{key}**: {value}")
else:
    st.warning("데이터베이스가 비어있습니다.")
