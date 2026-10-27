"""세계지도 역사 연대기 앱
실행: streamlit run main.py
"""

import re
import pycountry
import plotly.graph_objects as go
import requests
import streamlit as st
from bs4 import BeautifulSoup

st.set_page_config(
    page_title="세계 역사 연대기 지도",
    page_icon="🌍",
    layout="wide",
)

# 국가코드(ISO-3) -> (한글 이름, [(연도, 시대, 제목, 설명), ...])
# BC = 기원전
HISTORY = {}

HISTORY["KOR"] = ("대한민국(한반도)", [
    ("BC 2333", "고대", "고조선 건국", "단군이 세웠다고 전해짐."),
    ("BC 108", "고대", "고조선 멸망", "한나라 침공, 한사군 설치."),
    ("BC 57~18", "삼국", "삼국 성립", "신라·고구려·백제 건국."),
    ("372", "삼국", "고구려 불교 공인", "소수림왕, 태학 설립."),
    ("660~668", "삼국", "백제·고구려 멸망", "나당 연합군에 패배."),
    ("676", "남북국", "신라 삼국 통일", "북쪽엔 698년 발해 건국."),
    ("918", "고려", "고려 건국", "왕건 건국, 936년 통일."),
    ("1231", "고려", "몽골 침입", "강화도로 천도해 항쟁."),
    ("1392", "조선", "조선 건국", "이성계, 한양에 도읍."),
    ("1446", "조선", "훈민정음 반포", "세종이 1443년 창제."),
    ("1592~1598", "조선", "임진왜란", "이순신과 의병이 막아냄."),
    ("1636", "조선", "병자호란", "청에 항복(삼전도)."),
    ("1876", "근대", "강화도 조약", "불평등 조약으로 개항."),
    ("1910", "일제강점기", "국권 피탈", "일본의 강제 병합."),
    ("1919", "일제강점기", "3·1 운동", "임시정부가 수립됨."),
    ("1945", "현대", "광복과 분단", "38도선으로 남북 분할."),
    ("1948", "현대", "정부 수립", "대한민국 정부 수립."),
    ("1950~1953", "현대", "6·25 전쟁", "정전협정으로 중단."),
    ("1960", "현대", "4·19 혁명", "이승만 정권 퇴진."),
    ("1961~1979", "현대", "경제개발", "고도성장, 권위주의 통치."),
    ("1987", "현대", "6월 민주항쟁", "직선제 개헌을 이끎."),
    ("1988", "현대", "서울 올림픽", "국제적 위상이 높아짐."),
    ("1997", "현대", "외환위기", "IMF 구제금융을 받음."),
    ("2002", "현대", "한일 월드컵", "공동 개최, 4강 진출."),
])

HISTORY["JPN"] = ("일본", [
    ("BC 14000경", "선사", "조몬 시대", "토기를 쓴 수렵·채집 사회."),
    ("BC 300경", "고대", "야요이 시대", "벼농사와 금속기 전래."),
    ("3세기", "고대", "야마타이국", "히미코 여왕의 연합 세력."),
    ("538/552", "고대", "불교 전래", "백제에서 전해짐."),
    ("645", "고대", "다이카 개신", "중앙집권 개혁 시작."),
    ("710·794", "고대", "나라·헤이안 천도", "도읍을 두 차례 옮김."),
    ("1185~1192", "중세", "가마쿠라 막부", "최초의 무사 정권."),
    ("1274·1281", "중세", "몽골 침입", "태풍 등으로 실패."),
    ("1336", "중세", "무로마치 막부", "아시카가 가문이 개창."),
    ("1467", "중세", "오닌의 난", "전국시대의 계기."),
    ("1543", "근세", "조총 전래", "포르투갈인이 전함."),
    ("1603", "근세", "에도 막부", "약 260년 평화기."),
    ("1853", "근대", "페리 내항", "미국의 개항 요구."),
    ("1868", "근대", "메이지 유신", "천황 중심 근대화."),
    ("1894~1905", "근대", "청일·러일 전쟁", "제국주의 열강으로 부상."),
    ("1931~1945", "근현대", "침략과 패전", "태평양 전쟁, 1945년 패전."),
    ("1947", "현대", "평화헌법", "전쟁 포기를 명시."),
    ("1964", "현대", "도쿄 올림픽", "전후 부흥의 상징."),
    ("1991", "현대", "버블 붕괴", "장기 불황의 시작."),
])

HISTORY["CHN"] = ("중국", [
    ("BC 2070경", "고대", "하(夏)", "전승상 최초의 왕조."),
    ("BC 1600경", "고대", "상(商)", "갑골문과 청동기 문명."),
    ("BC 1046", "고대", "주(周)", "봉건제, 이후 춘추전국."),
    ("BC 551", "고대", "공자 탄생", "제자백가의 시대."),
    ("BC 221", "고대", "진의 통일", "진시황, 군현제 시행."),
    ("BC 202", "고대", "한(漢)", "유교 발전, 실크로드."),
    ("220", "중세", "삼국·위진남북조", "분열기가 이어짐."),
    ("589·618", "중세", "수·당", "수가 통일, 당이 번영."),
    ("960", "중세", "송(宋)", "활자·나침반·화약 발달."),
    ("1271", "중세", "원(元)", "쿠빌라이가 세움."),
    ("1368", "근세", "명(明)", "주원장이 한족 왕조 회복."),
    ("1644", "근세", "청(淸)", "마지막 왕조."),
    ("1840", "근대", "아편전쟁", "난징조약, 개항."),
    ("1911", "근대", "신해혁명", "청 멸망, 중화민국."),
    ("1937~1945", "근현대", "중일전쟁", "일본의 전면 침략."),
    ("1949", "현대", "중화인민공화국", "공산당 정권 수립."),
    ("1966~1976", "현대", "문화대혁명", "큰 혼란과 희생."),
    ("1978", "현대", "개혁·개방", "덩샤오핑, 고도성장."),
    ("2001", "현대", "WTO 가입", "세계 무역에 편입."),
])

HISTORY["USA"] = ("미국", [
    ("1607", "식민지", "제임스타운", "영국의 첫 영구 식민지."),
    ("1620", "식민지", "메이플라워호", "청교도가 정착."),
    ("1776", "건국", "독립선언", "영국에서 독립 선언."),
    ("1787", "건국", "미국 헌법", "연방제·삼권분립."),
    ("1803", "팽창", "루이지애나 매입", "국토가 두 배로 늘어남."),
    ("1861~1865", "분열", "남북전쟁", "북부 승리, 노예해방."),
    ("1869", "산업화", "대륙횡단철도", "동서가 연결됨."),
    ("1917", "대국", "1차 대전 참전", "연합국 승리에 기여."),
    ("1929", "대국", "대공황", "뉴딜 정책 추진."),
    ("1941~1945", "대국", "2차 대전", "초강대국으로 부상."),
    ("1947~1991", "냉전", "냉전", "소련과 이념·군비 경쟁."),
    ("1964", "현대", "민권법", "인종차별 금지."),
    ("1969", "현대", "달 착륙", "아폴로 11호."),
    ("2001", "현대", "9·11 테러", "대테러 전쟁 전개."),
    ("2008", "현대", "금융위기", "세계경제로 확산."),
])

HISTORY["GBR"] = ("영국", [
    ("43", "고대", "로마의 정복", "410년경 로마가 철수."),
    ("5~6세기", "중세", "앵글로·색슨 정착", "여러 왕국이 세워짐."),
    ("1066", "중세", "노르만 정복", "윌리엄 1세 즉위."),
    ("1215", "중세", "마그나카르타", "왕권을 제한."),
    ("1337~1453", "중세", "백년전쟁", "프랑스와 장기 전쟁."),
    ("1534", "근세", "수장령", "영국 국교회 성립."),
    ("1588", "근세", "아르마다 격파", "해양 강국의 기반."),
    ("1642", "근세", "청교도 혁명", "찰스 1세 처형."),
    ("1688", "근세", "명예혁명", "입헌군주제의 기초."),
    ("1707", "근대", "그레이트브리튼", "잉글랜드·스코틀랜드 합병."),
    ("1760경~", "근대", "산업혁명", "최초의 산업국가."),
    ("1815", "근대", "워털루 전투", "나폴레옹을 꺾음."),
    ("1837~1901", "근대", "빅토리아 시대", "제국의 전성기."),
    ("1914~1945", "현대", "두 차례 세계대전", "국력이 크게 소모됨."),
    ("1947", "현대", "인도 독립", "식민제국 해체."),
    ("1973", "현대", "EEC 가입", "유럽 통합에 참여."),
    ("2016~2020", "현대", "브렉시트", "EU를 탈퇴."),
])

HISTORY["FRA"] = ("프랑스", [
    ("BC 52", "고대", "알레시아 전투", "카이사르의 갈리아 정복."),
    ("496경", "중세", "클로비스 개종", "프랑크가 가톨릭 수용."),
    ("843", "중세", "베르됭 조약", "프랑크 제국 3분할."),
    ("987", "중세", "카페 왕조", "위그 카페 즉위."),
    ("1337~1453", "중세", "백년전쟁", "잔 다르크가 활약."),
    ("1598", "근세", "낭트 칙령", "위그노의 신앙 허용."),
    ("1643~1715", "근세", "루이 14세", "절대왕정의 전성기."),
    ("1789", "근대", "프랑스 혁명", "구체제가 무너짐."),
    ("1799~1815", "근대", "나폴레옹 시대", "유럽 제패 후 몰락."),
    ("1870", "근대", "보불전쟁", "제3공화국 수립."),
    ("1914~1918", "현대", "1차 대전", "승전국이 됨."),
    ("1940~1944", "현대", "독일 점령", "1944년 파리 해방."),
    ("1958", "현대", "제5공화국", "드골의 새 헌법."),
    ("1968", "현대", "5월 혁명", "학생·노동자 시위."),
    ("1992", "현대", "마스트리흐트 조약", "EU의 토대."),
])

HISTORY["DEU"] = ("독일", [
    ("9", "고대", "토이토부르크 전투", "게르만이 로마군 격파."),
    ("962", "중세", "신성로마제국", "오토 1세 대관."),
    ("1517", "근세", "종교개혁", "루터의 95개조 반박문."),
    ("1618~1648", "근세", "30년 전쟁", "베스트팔렌 조약."),
    ("1806", "근대", "제국 해체", "나폴레옹 전쟁의 결과."),
    ("1871", "근대", "독일 통일", "비스마르크 주도."),
    ("1914~1918", "현대", "1차 대전", "패전, 베르사유 조약."),
    ("1919", "현대", "바이마르 공화국", "민주 헌법 제정."),
    ("1933~1945", "현대", "나치 독일", "2차 대전과 홀로코스트."),
    ("1949", "현대", "동서독 분단", "서독과 동독 수립."),
    ("1961", "현대", "베를린 장벽", "냉전의 상징."),
    ("1989~1990", "현대", "장벽 붕괴·통일", "1990년 10월 3일 통일."),
])

HISTORY["ITA"] = ("이탈리아", [
    ("BC 753", "고대", "로마 건국(전승)", "로물루스가 세움."),
    ("BC 509", "고대", "로마 공화정", "왕정을 폐지."),
    ("BC 27", "고대", "로마 제정", "아우구스투스 즉위."),
    ("476", "중세", "서로마 멸망", "게르만 용병대장이 폐위."),
    ("14~16세기", "근세", "르네상스", "피렌체 중심의 부흥."),
    ("1861", "근대", "이탈리아 통일", "카보우르·가리발디."),
    ("1922", "현대", "무솔리니 집권", "파시스트 정권."),
    ("1946", "현대", "공화국 선포", "국민투표로 왕정 폐지."),
    ("1957", "현대", "로마 조약", "EEC 원회원국."),
])

HISTORY["EGY"] = ("이집트", [
    ("BC 3100경", "고대", "이집트 통일", "상·하 이집트가 통일됨."),
    ("BC 2560경", "고대", "대피라미드", "쿠푸왕의 피라미드."),
    ("BC 1550경", "고대", "신왕국", "람세스 2세 등 전성기."),
    ("BC 332", "고대", "알렉산드로스 정복", "프톨레마이오스 왕조로."),
    ("BC 30", "고대", "로마에 병합", "클레오파트라 7세."),
    ("641", "중세", "이슬람 정복", "아랍군이 정복."),
    ("969", "중세", "카이로 건설", "파티마 왕조."),
    ("1517", "근세", "오스만 편입", "오스만의 지배."),
    ("1798", "근대", "나폴레옹 원정", "근대화의 계기."),
    ("1869", "근대", "수에즈 운하", "무역의 요충지."),
    ("1952", "현대", "이집트 혁명", "왕정 붕괴, 나세르."),
    ("1979", "현대", "이스라엘과 평화", "아랍권 최초."),
    ("2011", "현대", "1·25 혁명", "무바라크 퇴진."),
])

HISTORY["IND"] = ("인도", [
    ("BC 2600경", "고대", "인더스 문명", "계획도시가 발달."),
    ("BC 1500경", "고대", "베다 시대", "카스트제도의 기원."),
    ("BC 5세기경", "고대", "불교 창시", "고타마 싯다르타."),
    ("BC 321", "고대", "마우리아 왕조", "아소카왕 때 최대 영토."),
    ("320", "고대", "굽타 왕조", "고전 문화의 황금기."),
    ("1206", "중세", "델리 술탄조", "이슬람 왕조 성립."),
    ("1526", "근세", "무굴 제국", "타지마할이 건립됨."),
    ("1757", "근대", "플라시 전투", "영국 지배가 본격화."),
        ("BC 776", "고대", "첫 올림피아 경기", "고대 올림픽 시작."),
    ("BC 508", "고대", "아테네 민주정", "클레이스테네스 개혁."),
    ("BC 490·480", "고대", "페르시아 전쟁", "마라톤·살라미스 승리."),
    ("BC 431~404", "고대", "펠로폰네소스 전쟁", "폴리스가 쇠퇴."),
    ("BC 336~323", "고대", "알렉산드로스 대왕", "헬레니즘 세계를 엶."),
    ("BC 146", "고대", "로마에 병합", "로마의 지배."),
    ("1453", "중세", "오스만 지배", "비잔티움 멸망 이후."),
    ("1821~1832", "근대", "독립 전쟁", "독립 왕국 수립."),
    ("1981", "현대", "EC 가입", "유럽공동체에 가입."),
])

HISTORY["TUR"] = ("튀르키예", [
    ("BC 1600경", "고대", "히타이트 제국", "철기 문화로 번성."),
    ("330", "고대", "콘스탄티노폴리스", "콘스탄티누스 1세 천도."),
    ("1071", "중세", "만지케르트 전투", "셀주크가 비잔티움 격파."),
    ("1299", "중세", "오스만 제국 건국", "오스만 1세."),
    ("1453", "근세", "콘스탄티노폴리스 함락", "비잔티움 멸망."),
    ("1520~1566", "근세", "쉴레이만 대제", "오스만의 전성기."),
    ("1683", "근세", "빈 포위 실패", "영토가 줄기 시작."),
    ("1914~1918", "현대", "1차 대전 패전", "제국 분할."),
    ("1923", "현대", "튀르키예 공화국", "아타튀르크의 개혁."),
])

HISTORY["BRA"] = ("브라질", [
    ("1500", "식민지", "카브랄 도착", "포르투갈이 영유 선언."),
    ("16세기", "식민지", "사탕수수와 노예제", "노예 노동 기반 경제."),
    ("1808", "식민지", "왕실 이주", "리우데자네이루로 이전."),
    ("1822", "제국", "독립 선언", "페드루 1세."),
    ("1888", "제국", "노예제 폐지", "황금법 제정."),
    ("1889", "공화국", "공화정 선포", "군부 쿠데타로 왕정 종식."),
    ("1930", "공화국", "바르가스 집권", "산업화 정책."),
    ("1964~1985", "공화국", "군사독재", "이후 민정 이양."),
    ("1988", "공화국", "신헌법", "민주 헌법 제정."),
])




WIKI_API = "https://en.wikipedia.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"

# 주요 인물 설명: 기존 내장 연대기에서 자주 등장하는 인물들을 우선 제공.
# 새 국가/사건은 Wikipedia 링크에서 인물 문서를 찾아 상세 설명을 불러옵니다.
PEOPLE = {
    "단군": "고조선을 세웠다고 전해지는 인물이다. 단군 신화는 한국 고대 국가의 기원과 건국 이념을 이해하는 중요한 자료이다.",
    "세종": "조선 제4대 국왕이다. 훈민정음 창제를 주도했으며 과학·문화·제도 발전을 추진했다.",
    "이순신": "조선의 무신으로 임진왜란 때 수군을 이끌었다. 한산도 대첩 등에서 활약했다.",
    "왕건": "고려를 건국하고 후삼국을 통일한 고려 태조이다.",
    "이성계": "조선의 건국자이자 태조이다. 고려 말 권력을 장악한 뒤 1392년 조선을 세웠다.",
    "히미코": "3세기 일본 열도의 야마타이국을 다스린 것으로 중국 사서에 기록된 여왕이다.",
    "진시황": "중국을 최초로 통일한 진나라의 황제이다. 문자·도량형을 통일하고 중앙집권 체제를 강화했다.",
    "공자": "중국 춘추 시대의 사상가로 인(仁)과 예(禮)를 강조했다. 유교 사상의 형성에 큰 영향을 주었다.",
    "쿠빌라이": "몽골 제국의 칸이자 원나라를 세운 황제이다.",
    "덩샤오핑": "중국의 지도자로 1978년 이후 개혁·개방 정책을 추진했다.",
    "조지 워싱턴": "미국 독립전쟁의 총사령관이자 초대 대통령이다.",
    "에이브러햄 링컨": "미국의 제16대 대통령이다. 남북전쟁을 이끌었으며 노예제 폐지를 추진했다.",
    "마틴 루터 킹": "미국의 흑인 민권운동 지도자로 비폭력 저항과 인종 평등을 주장했다.",
    "윌리엄 1세": "1066년 노르만 정복을 이끌고 잉글랜드 왕이 되었다.",
    "마틴 루터": "독일의 종교개혁가로 1517년 면벌부 비판을 계기로 종교개혁 운동에 영향을 주었다.",
    "비스마르크": "프로이센의 정치가로 외교와 전쟁을 통해 1871년 독일 통일을 이끌었다.",
    "율리우스 카이사르": "로마의 장군이자 정치가로 갈리아를 정복하고 로마 공화정 말기의 권력 투쟁에서 핵심 역할을 했다.",
    "아우구스투스": "로마의 초대 황제로 원수정을 세우고 제국의 기반을 다졌다.",
    "가리발디": "이탈리아 통일 운동의 군사 지도자이다.",
    "클레오파트라": "프톨레마이오스 왕조의 마지막 통치자 중 한 명으로 로마의 권력자들과 외교 관계를 맺었다.",
    "아소카": "마우리아 왕조의 왕으로 불교를 후원하고 인도 아대륙의 넓은 지역을 통치했다.",
    "간디": "인도 독립운동 지도자로 비폭력·불복종 운동을 이끌었다.",
    "표트르 대제": "러시아의 황제로 군사·행정 개혁과 서유럽식 근대화를 추진했다.",
    "블라디미르 레닌": "러시아 혁명에서 볼셰비키를 이끌고 소련 성립의 기반을 마련했다.",
    "알렉산드로스": "마케도니아의 왕으로 페르시아 제국을 정복하고 헬레니즘 문화 확산의 계기를 만들었다.",
    "오스만 1세": "오스만 왕조의 창시자로 여겨지는 인물이다.",
    "무스타파 케말 아타튀르크": "튀르키예 공화국의 초대 대통령으로 세속화와 근대화 개혁을 추진했다.",
    "페드루 1세": "브라질 독립을 선언하고 브라질 제국의 초대 황제가 되었다.",
    "나폴레옹": "프랑스의 군인·정치가로 프랑스 혁명 이후 권력을 잡고 유럽 여러 지역을 지배했다.",
    "잔 다르크": "백년전쟁 중 프랑스군의 사기를 높인 인물로, 프랑스의 국가적 상징이 되었다.",
    "루이 14세": "프랑스의 국왕으로 절대왕정의 전성기를 상징한다.",
}

            api, params=params,
            headers={"User-Agent": "WorldHistoryTimeline/2.0 (educational app)"},
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        return {}

@st.cache_data(ttl=86400, show_spinner=False)
def wiki_summary(title):
    data = wiki_request({
        "action": "query", "format": "json", "redirects": 1,
        "prop": "extracts|pageimages|info", "exintro": 1,
        "explaintext": 1, "piprop": "thumbnail", "pithumbsize": 900,
        "inprop": "url", "titles": title,
    })
    pages = data.get("query", {}).get("pages", {})
    if not isinstance(pages, dict) or not pages:
        return None
    page = next(iter(pages.values()), {})
    if not isinstance(page, dict) or "missing" in page:
        return None
    return {
        "title": page.get("title", title),
        "extract": page.get("extract", ""),
        "image": page.get("thumbnail", {}).get("source"),
        "url": page.get("fullurl", "https://en.wikipedia.org/wiki/" + title.replace(" ", "_")),
    }

@st.cache_data(ttl=86400, show_spinner=False)
def commons_image(query):
    """사건명에 맞는 Wikimedia Commons 이미지를 찾습니다."""
    data = wiki_request({
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": f"filetype:bitmap {query}", "gsrnamespace": 6,
        "gsrlimit": 1, "prop": "imageinfo", "iiprop": "url", "iiurlwidth": 900,
    }, api=COMMONS_API)
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        info = page.get("imageinfo", [])
        if info:
            return info[0].get("thumburl") or info[0].get("url")
    return None

@st.cache_data(ttl=86400, show_spinner=False)
def wiki_timeline(country_name):
    """역사 문서의 제목/문단을 이용해 미리 내장되지 않은 국가의 연대기를 구성합니다."""
    candidates = [f"History of {country_name}", f"History of {country_name} by period", country_name]
    for title in candidates:
        data = wiki_request({
            "action": "parse", "format": "json", "page": title,
            "prop": "text|sections",
        })
        parsed = data.get("parse")
        if not parsed:
            continue
        parsed_html = parsed.get("text", {}).get("*", "")
        if not parsed_html:
            continue
        soup = BeautifulSoup(parsed_html, "html.parser")
        events = []
        current_heading = None
        for node in soup.find_all(["h2", "h3", "h4", "p"]):
            if node.name in ("h2", "h3", "h4"):
                current_heading = node.get_text(" ", strip=True).replace("[edit]", "").strip()
                continue
            paragraph = node.get_text(" ", strip=True)
            if len(paragraph) < 100:
                continue
            # 지나치게 자잘한 세부 사항 대신 역사적으로 의미 있는 문단만 선별
            years = re.findall(r"(?<!\d)(?:c\.?\s*)?(?:\d{1,2}(?:st|nd|rd|th) century|\d{3,4})(?!\d)", paragraph)
            if not years and not current_heading:
                continue
            year = years[0] if years else current_heading
            title_text = current_heading or f"{country_name}의 역사적 변화"
            # HTML 문서에서 인물/기관 링크를 추출해 클릭 가능한 후보로 보관
            links = []
            for a in node.find_all("a", href=True):
                href = a.get("href", "")
                text = a.get_text(" ", strip=True)
                if href.startswith("./") and text and len(text) < 50:
                    wiki_title = href[2:].split("#")[0].replace("_", " ")
                    if wiki_title and wiki_title not in links:
                        links.append(wiki_title)
            events.append({
                "year": year, "era": current_heading or "역사적 사건",
                "title": title_text[:100], "desc": paragraph[:850],
                "people": links[:5], "image_query": f"{country_name} {title_text}",
                "url": "https://en.wikipedia.org/wiki/" + title.replace(" ", "_"),
            })
            if len(events) >= 18:
                break
        if events:
            # 같은 제목으로 반복되는 문단을 줄입니다.
            unique, seen = [], set()
            for event in events:
                key = (event["title"], event["year"])
                if key not in seen:
                    seen.add(key)
                    unique.append(event)
            return unique, "https://en.wikipedia.org/wiki/" + title.replace(" ", "_")
    return [], None

def person_detail(name):
    """인물의 간단한 설명과 대표 이미지를 위키백과에서 불러옵니다."""
    known = PEOPLE.get(name)
    summary = wiki_summary(name)
    if summary and summary.get("extract"):
        return summary
    if known:
        return {"title": name, "extract": known, "image": None,
                "url": "https://en.wikipedia.org/wiki/" + name.replace(" ", "_")}
    return {"title": name, "extract": "상세 설명을 불러오지 못했습니다. 아래 문서에서 확인할 수 있습니다.",
            "image": None, "url": "https://en.wikipedia.org/wiki/" + name.replace(" ", "_")}

def build_map(names, selected):
    isos, z = list(names.keys()), []
    for iso in isos:
        z.append(2 if iso == selected else (1 if iso in HISTORY else 0))
    hover = [f"{flag_emoji(i)} {label(i, names)}" for i in isos]
    colors = [[0, "#d9dee5"], [0.5, "#4c78a8"], [1, "#f58518"]]
    fig = go.Figure(go.Choropleth(
        locations=isos, z=z, zmin=0, zmax=2, text=hover,
        hovertemplate="%{text}<extra></extra>", colorscale=colors,
        showscale=False, marker_line_color="white", marker_line_width=0.4,
    ))
    fig.update_layout(
        height=520, margin=dict(l=0, r=0, t=0, b=0),
        geo=dict(showframe=False, showcoastlines=False,
                 projection_type="natural earth", bgcolor="rgba(0,0,0,0)"),
        paper_bgcolor="rgba(0,0,0,0)", clickmode="event+select",
    )
    return fig

def render_person(name, key):
    """굵게+밑줄이 적용된 클릭 버튼으로 인물 설명을 펼칩니다."""
    st.markdown(
        "<style>div[data-testid='stButton'] button p {font-weight:700;text-decoration:underline;}</style>",
        unsafe_allow_html=True,
    )
    safe_key = re.sub(r"[^a-zA-Z0-9가-힣]+", "_", f"{key}_{name}")[:180]
    if st.button(f"**{name}**", key=f"person_{safe_key}", help="클릭하면 인물 상세 설명이 표시됩니다"):
        st.session_state["active_person"] = name
    if st.session_state.get("active_person") == name:
        with st.container(border=True):
            with st.spinner(f"{name}의 정보를 불러오는 중..."):
                info = person_detail(name)
            st.subheader(info["title"])
            if info.get("image"):
                st.image(info["image"], width=220)
            st.write(info.get("extract") or "설명을 찾지 못했습니다.")
            st.markdown(f"[관련 문서 열기]({info['url']})")
            if st.button("상세 설명 닫기", key=f"close_{safe_key}"):
                st.session_state["active_person"] = None
                st.rerun()

def show_curated_timeline(events, country_name):
    eras = list(dict.fromkeys(ev[1] for ev in events))
    chosen = st.multiselect("시대 필터", eras, default=eras)
    for idx, (year, era, title, desc) in enumerate(events):
        if era not in chosen:
            continue
        st.markdown(f"### {year} · {era}")
        left, right = st.columns([1, 2.7])
        with left:
            image_url = commons_image(f"{country_name} {title}")
            if image_url:
                st.image(image_url, use_container_width=True)
            else:
                st.caption("이 사건의 사진을 찾지 못했습니다.")
        with right:
            st.subheader(title)
            st.write(desc)
            people = []
            for person in PEOPLE:
                if person in title or person in desc:
                    people.append(person)
            # 일부 사건은 제목만으로 인물이 드러나지 않으므로 연대기 설명에 언급된 인물 위주로 표시
            if people:
                st.markdown("**주요 인물 (이름을 클릭하면 상세 설명 표시):**")
                for person in people:
                    render_person(person, f"{country_name}_{idx}")
        st.divider()

def show_dynamic_timeline(events):
    eras = list(dict.fromkeys(ev["era"] for ev in events))
    chosen = st.multiselect("시대 필터", eras, default=eras, key="dynamic_eras")
    for idx, event in enumerate(events):
        if event["era"] not in chosen:
            continue
        st.markdown(f"### {event['year']} · {event['era']}")
        left, right = st.columns([1, 2.7])
        with left:
            image_url = commons_image(event["image_query"])
            if image_url:
                st.image(image_url, use_container_width=True)
            else:
                st.caption("관련 이미지를 찾지 못했습니다.")
        with right:
            st.subheader(event["title"])
            st.write(event["desc"])
            candidates = event.get("people", [])
            if candidates:
                st.markdown("**관련 인물·문서 (이름을 클릭하면 상세 설명 표시):**")
                for person in candidates:
                    render_person(person, f"dynamic_{idx}")
        st.divider()

# ---------------- 앱 본문 ----------------
st.title("🌍 세계 역사 연대기 지도")
st.caption("지도에서 나라를 클릭하거나 목록에서 선택하세요. 국기·사건 이미지·인물 상세 설명을 제공합니다.")
st.info("파란색: 연대기가 내장된 국가 · 회색: 위키백과 자료에서 연대기를 구성하는 국가 · 주황색: 현재 선택한 국가")

names = country_table()
st.session_state.setdefault("iso", "KOR")
st.session_state.setdefault("last_click", None)
st.session_state.setdefault("active_person", None)

fig = build_map(names, st.session_state["iso"])
event = st.plotly_chart(fig, key="world_map", on_select="rerun",
                        selection_mode="points", use_container_width=True)
points = []
try:
    points = event.selection.points
except Exception:
    pass
if points:
    clicked = points[0].get("location")
    if clicked and clicked != st.session_state["last_click"]:
        st.session_state["last_click"] = clicked
        st.session_state["iso"] = clicked
        st.session_state["picker"] = clicked
        st.rerun()

def sort_key(i):
    return (i not in HISTORY, label(i, names))

sorted_isos = sorted(names, key=sort_key)
def on_pick():
    st.session_state["iso"] = st.session_state["picker"]

st.session_state.setdefault("picker", st.session_state["iso"])
st.selectbox("또는 목록에서 나라 선택", sorted_isos,
             format_func=lambda i: f"{flag_emoji(i)} {label(i, names)}",
             key="picker", on_change=on_pick)

iso = st.session_state["iso"]
country_name = label(iso, names)
st.divider()
st.header(f"{flag_emoji(iso)} 📜 {country_name}의 역사 연대기")

if iso in HISTORY:
    show_curated_timeline(HISTORY[iso][1], country_name)
    st.caption("※ 기존 내장 사건에 사건별 이미지를 연결합니다. 사진 검색 결과는 Wikimedia Commons에서 제공됩니다.")
else:
    st.caption("이 국가에는 별도 내장 연대기가 없어 위키백과의 역사 문서에서 시대별 문단을 추출합니다. 자동 추출 결과는 참고용이므로 문서 링크로 교차 확인하세요.")
    with st.spinner(f"{country_name}의 역사 자료를 찾는 중..."):
        events, source_url = wiki_timeline(names.get(iso, iso))
    if events:
        show_dynamic_timeline(events)
        if source_url:
            st.markdown(f"[역사 자료 원문 열기]({source_url})")
    else:
        st.warning("자동으로 연대기를 만들지 못했습니다. 인터넷 연결을 확인하거나 아래에서 문서를 직접 열어 보세요.")
        st.markdown(f"[{country_name} 역사 문서 검색](https://en.wikipedia.org/wiki/Special:Search?search=History+of+{country_name.replace(' ', '+')})")
