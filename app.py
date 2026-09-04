import pandas as pd
import FinanceDataReader as fdr
import streamlit as st
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import datetime  # 🚨 달력을 만들기 위해 꼭 필요한 모듈입니다!

# 1. 페이지 설정
st.set_page_config(page_title="기업 및 소재 분석 대시보드", page_icon="📈", layout="wide")
st.title("📈 기업 주가 & 핵심 소재/환율 종합 분석 대시보드")
st.write("선택한 두 기업의 주가 변동률과 핵심 소재 및 거시경제 지표를 한눈에 비교합니다.")

# 2. 사이드바 설정 (기업, 지표, 달력)
st.sidebar.header("🔍 분석 조건 설정")

companies = {
    "삼성전자": "005930",
    "SK하이닉스": "000660",
    "포스코홀딩스": "005490"
}
company_a = st.sidebar.selectbox("첫 번째 기업", list(companies.keys()))
company_b = st.sidebar.selectbox("두 번째 기업", list(companies.keys()), index=1)

materials = {
    "원/달러 환율 (KODEX 미국달러선물)": "261220",
    "KODEX 구리선물(H)": "138230",
    "TIGER 철강": "148070"
}
selected_material = st.sidebar.selectbox("비교할 소재 / 거시지표", list(materials.keys()))

st.sidebar.divider() # 사이드바 구분선

# 📅 조회 기간 설정 달력 위젯
st.sidebar.header("📅 조회 기간 설정")
start_date = st.sidebar.date_input("시작일", datetime.date(2026, 1, 1))
end_date = st.sidebar.date_input("종료일", datetime.date(2026, 8, 26))

# 3. 데이터 수집 함수 (달력에서 선택한 날짜 반영)
@st.cache_data
def get_stock_data(company_name, start, end):
    code = companies[company_name]
    return fdr.DataReader(code, start, end)

@st.cache_data
def get_material_data(material_name, start, end):
    code = materials[material_name]
    try:
        df = fdr.DataReader(code, start, end)
        return pd.DataFrame({'Close': df['Close']}).dropna()
    except:
        return pd.DataFrame()

# 🚨 함수 호출 (달력 날짜 반영하여 데이터 가져오기)
data_a = get_stock_data(company_a, start_date, end_date)
data_b = get_stock_data(company_b, start_date, end_date)
mat_data = get_material_data(selected_material, start_date, end_date)

# 4. 상단 요약 지표 (전일 대비 등락 화살표 추가!)
col1, col2, col3 = st.columns(3)

with col1:
    if len(data_a) >= 2:
        current_a = data_a['Close'].iloc[-1] # 최근 종가
        prev_a = data_a['Close'].iloc[-2]    # 하루 전 종가
        diff_a = current_a - prev_a          # 차이 계산
        st.metric(f"📌 {company_a}", f"{current_a:,.0f} 원", f"{diff_a:,.0f} 원")
    elif not data_a.empty:
        st.metric(f"📌 {company_a}", f"{data_a['Close'].iloc[-1]:,.0f} 원")

with col2:
    if len(data_b) >= 2:
        current_b = data_b['Close'].iloc[-1]
        prev_b = data_b['Close'].iloc[-2]
        diff_b = current_b - prev_b
        st.metric(f"📌 {company_b}", f"{current_b:,.0f} 원", f"{diff_b:,.0f} 원")
    elif not data_b.empty:
        st.metric(f"📌 {company_b}", f"{data_b['Close'].iloc[-1]:,.0f} 원")

with col3:
    if len(mat_data) >= 2:
        current_m = mat_data['Close'].iloc[-1]
        prev_m = mat_data['Close'].iloc[-2]
        diff_m = current_m - prev_m
        st.metric(f"🧪 {selected_material.split(' ')[0]}", f"{current_m:,.0f}", f"{diff_m:,.0f}")
    elif not mat_data.empty:
        st.metric(f"🧪 {selected_material.split(' ')[0]}", f"{mat_data['Close'].iloc[-1]:,.0f}")

st.divider()
# 5. 탭 구성
tab1, tab2, tab3 = st.tabs(["📈 주가 & 소재 통합 비교", "🧪 소재 상세 데이터", "📰 관련 경제 뉴스"])

with tab1:
    st.subheader(f"📊 {company_a} vs {company_b} vs {selected_material.split(' ')[0]} 수익률(%) 비교")
    
    if data_a.empty or data_b.empty or mat_data.empty:
        st.error("데이터가 없습니다. 공휴일이거나 아직 장이 열리지 않은 날짜일 수 있습니다. 날짜를 변경해 보세요.")
    else:
        # 시간대(Timezone) 제거
        mat_data.index = mat_data.index.tz_localize(None)
        
        # 첫날 기준 수익률(%) 환산
        pct_a = (data_a["Close"] / data_a["Close"].iloc[0] - 1) * 100
        pct_b = (data_b["Close"] / data_b["Close"].iloc[0] - 1) * 100
        pct_mat = (mat_data["Close"] / mat_data["Close"].iloc[0] - 1) * 100
        
        combined_df = pd.DataFrame({
            f"{company_a} (%)": pct_a,
            f"{company_b} (%)": pct_b,
            f"{selected_material.split(' ')[0]} (%)": pct_mat
        }).ffill().dropna()
        
        st.line_chart(combined_df)
        st.caption("💡 단위를 일치시키기 위해 시작일 대비 등락률(%)로 환산하여 비교한 차트입니다.")

with tab2:
    st.subheader(f"🧪 {selected_material.split(' ')[0]} 원본 데이터 및 추이")
    if not mat_data.empty:
        st.line_chart(mat_data['Close'])
        st.dataframe(mat_data.tail(10), use_container_width=True)

with tab3:
    st.subheader("📰 실시간 연관 경제 뉴스")
    keyword = st.radio("검색 키워드", [company_a, company_b, selected_material.split()[0]], horizontal=True)
    
    @st.cache_data(ttl=3600)
    def get_news(kw):
        url = f"https://news.google.com/rss/search?q={urllib.parse.quote(kw)}&hl=ko&gl=KR&ceid=KR:ko"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            root = ET.fromstring(urllib.request.urlopen(req).read())
            return [{"title": i.find('title').text, "link": i.find('link').text} for i in root.findall('./channel/item')[:5]]
        except:
            return []
            
    news_list = get_news(keyword)
    if news_list:
        for n in news_list:
            st.markdown(f"🔹 [{n['title']}]({n['link']})")