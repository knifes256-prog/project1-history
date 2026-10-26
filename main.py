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
