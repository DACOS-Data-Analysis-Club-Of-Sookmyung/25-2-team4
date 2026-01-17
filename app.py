import os
import json
from math import ceil
from datetime import datetime, date

import streamlit as st

# =========================
# 설정
# =========================
BASE_DIR = "."
PROJECT_FILE = os.path.join(BASE_DIR, "project_textified.jsonl")

# ✅ 첫 항목은 "로그인할 계정 선택" (placeholder)
USERS = ["로그인할 계정 선택", "u00001", "u00002", "u00003"]
RESULT_PATTERN = "hybrid_results_{uid}.json"

PAGE_SIZE = 10
USERS_FILE = os.path.join(BASE_DIR, "users.json")


# =========================
# 유틸
# =========================
def safe_get(d, key, default=""):
    v = d.get(key, default)
    return default if v is None else v


def is_expired(deadline_str: str) -> bool:
    if not deadline_str:
        return False
    try:
        d = datetime.strptime(deadline_str, "%Y-%m-%d").date()
        return d < date.today()
    except:
        return False


def parse_csv_list(text: str) -> list:
    if not text:
        return []
    return [x.strip() for x in text.split(",") if x.strip()]


# =========================
# 프로젝트/추천 결과 로더
# =========================
@st.cache_data
def load_projects_index(project_path: str) -> dict:
    idx = {}
    if not os.path.exists(project_path):
        return idx
    with open(project_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            pid = obj.get("project_id")
            if pid:
                idx[pid] = obj
    return idx


@st.cache_data
def load_results(result_path: str) -> list:
    with open(result_path, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================
# users.json 로드/저장 (중첩 구조 upsert)
# =========================
def load_users_dataset() -> list:
    if not os.path.exists(USERS_FILE):
        return []
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except:
        return []


def save_users_dataset(users: list) -> None:
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def find_user(users: list, user_id: str):
    for u in users:
        if u.get("user_id") == user_id:
            return u
    return None


def upsert_user(users: list, user_obj: dict) -> list:
    target_id = user_obj.get("user_id")
    if not target_id:
        return users

    for i, u in enumerate(users):
        if u.get("user_id") == target_id:
            users[i] = user_obj
            return users

    users.append(user_obj)
    return users


def default_user_obj(user_id: str) -> dict:
    return {
        "user_id": user_id,
        "name": "",
        "student_num": "",
        "profile": {"major": [], "skills": [], "interests": [], "bio": ""},
        "history": [],
        "prefer_roll": ""
    }


# =========================
# UI
# =========================
st.set_page_config(page_title="Hybrid Recommender", layout="wide")
st.title("📌 프로젝트 추천 결과 (Hybrid Top 100)")

projects_idx = load_projects_index(PROJECT_FILE)

# -------------------------
# 로그인 UI
# -------------------------
colA, colB, colC = st.columns([2, 2, 6])

with colA:
    # ✅ 초기값(placeholder)을 선택된 상태로
    uid = st.selectbox("User 선택(= 로그인 계정)", USERS, index=0)

is_logged_in = uid != "로그인할 계정 선택"

# -------------------------
# 로그인 전/후 UI 분기
# -------------------------
if not is_logged_in:
    st.info("👈 먼저 **좌측 상단에서 로그인할 계정**을 선택하면 추천 결과를 보여줄게요.")
    st.markdown("---")
    st.subheader("🔎 프로젝트 추천 결과")
    st.write("로그인 후 확인할 수 있어요.")
    st.stop()

# 이제부터는 로그인 된 상태
current_user_id = uid.upper()  # u00001 -> U00001
users_dataset = load_users_dataset()
existing_user = find_user(users_dataset, current_user_id) or default_user_obj(current_user_id)

# 유저가 바뀔 때만 세션 초기화
if "profile_last_uid" not in st.session_state:
    st.session_state.profile_last_uid = None

if st.session_state.profile_last_uid != uid:
    st.session_state[f"{uid}_name"] = existing_user.get("name", "")
    st.session_state[f"{uid}_student_num"] = existing_user.get("student_num", "")

    prof = existing_user.get("profile", {}) or {}
    st.session_state[f"{uid}_major_text"] = ", ".join(prof.get("major", []) or [])
    st.session_state[f"{uid}_skills_text"] = ", ".join(prof.get("skills", []) or [])
    st.session_state[f"{uid}_interests_text"] = ", ".join(prof.get("interests", []) or [])
    st.session_state[f"{uid}_bio"] = prof.get("bio", "")

    st.session_state[f"{uid}_prefer_roll"] = existing_user.get("prefer_roll", "")

    hist = existing_user.get("history", []) or []
    for i in range(5):
        item = hist[i] if i < len(hist) else {"type": "", "desc": ""}
        st.session_state[f"{uid}_hist_type_{i}"] = item.get("type", "")
        st.session_state[f"{uid}_hist_desc_{i}"] = item.get("desc", "")

    st.session_state.profile_last_uid = uid

# -------------------------
# 사이드바: 유저 정보 입력(시연용)
# -------------------------
with st.sidebar:
    st.header("🧑‍💻 유저 정보 입력 (시연용)")
    st.caption("입력값은 users.json에 저장되지만, **추천 결과(뷰어)는 기존 결과 파일을 그대로 보여줍니다.**")

    with st.form(key=f"profile_form_{uid}", clear_on_submit=False):
        name = st.text_input("이름 (name)", value=st.session_state.get(f"{uid}_name", ""))
        student_num = st.text_input("학번 (student_num)", value=st.session_state.get(f"{uid}_student_num", ""))

        st.markdown("### Profile")
        major_text = st.text_input(
            "전공 (major) - 쉼표로 여러 개",
            value=st.session_state.get(f"{uid}_major_text", ""),
            placeholder="예: 컴퓨터공학, 수학"
        )
        skills_text = st.text_input(
            "스킬 (skills) - 쉼표로 여러 개",
            value=st.session_state.get(f"{uid}_skills_text", ""),
            placeholder="예: 파이썬, Django, 리액트"
        )
        interests_text = st.text_input(
            "관심사 (interests) - 쉼표로 여러 개",
            value=st.session_state.get(f"{uid}_interests_text", ""),
            placeholder="예: 강화학습, 추천시스템"
        )
        bio = st.text_area("소개 (bio)", value=st.session_state.get(f"{uid}_bio", ""), height=90)

        st.markdown("### History (최대 5개)")
        history_rows = []
        for i in range(5):
            c1, c2 = st.columns([1, 2])
            with c1:
                h_type = st.text_input(
                    f"type #{i+1}",
                    value=st.session_state.get(f"{uid}_hist_type_{i}", ""),
                    key=f"{uid}_hist_type_input_{i}"
                )
            with c2:
                h_desc = st.text_input(
                    f"desc #{i+1}",
                    value=st.session_state.get(f"{uid}_hist_desc_{i}", ""),
                    key=f"{uid}_hist_desc_input_{i}"
                )
            history_rows.append((h_type, h_desc))

        prefer_roll = st.text_input(
            "선호 역할 (prefer_roll)",
            value=st.session_state.get(f"{uid}_prefer_roll", ""),
            placeholder="예: 개발"
        )

        submitted = st.form_submit_button("✅ 저장 (users.json)")

    if submitted:
        st.session_state[f"{uid}_name"] = name
        st.session_state[f"{uid}_student_num"] = student_num
        st.session_state[f"{uid}_major_text"] = major_text
        st.session_state[f"{uid}_skills_text"] = skills_text
        st.session_state[f"{uid}_interests_text"] = interests_text
        st.session_state[f"{uid}_bio"] = bio
        st.session_state[f"{uid}_prefer_roll"] = prefer_roll

        for i, (h_type, h_desc) in enumerate(history_rows):
            st.session_state[f"{uid}_hist_type_{i}"] = h_type
            st.session_state[f"{uid}_hist_desc_{i}"] = h_desc

        history = []
        for h_type, h_desc in history_rows:
            if (h_type or "").strip() or (h_desc or "").strip():
                history.append({"type": (h_type or "").strip(), "desc": (h_desc or "").strip()})

        user_obj = {
            "user_id": current_user_id,
            "name": name,
            "student_num": student_num,
            "profile": {
                "major": parse_csv_list(major_text),
                "skills": parse_csv_list(skills_text),
                "interests": parse_csv_list(interests_text),
                "bio": bio
            },
            "history": history,
            "prefer_roll": prefer_roll
        }

        users_dataset = upsert_user(load_users_dataset(), user_obj)
        save_users_dataset(users_dataset)
        st.success(f"저장 완료: {USERS_FILE}")

    st.subheader("📦 현재 유저 JSON 미리보기")
    st.json({
        "user_id": current_user_id,
        "name": st.session_state.get(f"{uid}_name", ""),
        "student_num": st.session_state.get(f"{uid}_student_num", ""),
        "profile": {
            "major": parse_csv_list(st.session_state.get(f"{uid}_major_text", "")),
            "skills": parse_csv_list(st.session_state.get(f"{uid}_skills_text", "")),
            "interests": parse_csv_list(st.session_state.get(f"{uid}_interests_text", "")),
            "bio": st.session_state.get(f"{uid}_bio", ""),
        },
        "history": [
            {"type": st.session_state.get(f"{uid}_hist_type_{i}", ""),
             "desc": st.session_state.get(f"{uid}_hist_desc_{i}", "")}
            for i in range(5)
            if (st.session_state.get(f"{uid}_hist_type_{i}", "").strip()
                or st.session_state.get(f"{uid}_hist_desc_{i}", "").strip())
        ],
        "prefer_roll": st.session_state.get(f"{uid}_prefer_roll", ""),
    })

# -------------------------
# 로그인 상태 표시 + 추천 결과 영역 타이틀
# -------------------------
with colB:
    hide_expired = st.checkbox("마감 프로젝트 숨기기", value=True)

st.markdown(f"### ✅ 로그인 계정: `{uid}`")
st.caption("아래 추천 결과는 **미리 생성된 hybrid_results_{uid}.json**을 그대로 표시합니다.")

# =========================
# 결과 파일 로드
# =========================
result_path = os.path.join(BASE_DIR, RESULT_PATTERN.format(uid=uid))
if not os.path.exists(result_path):
    st.error(f"결과 파일이 없습니다: {result_path}")
    st.stop()

results = load_results(result_path)

if hide_expired:
    results = [r for r in results if not is_expired(r.get("deadline"))]

total = len(results)
total_pages = max(1, ceil(total / PAGE_SIZE))

# 페이지 상태
if "page" not in st.session_state:
    st.session_state.page = 1

# 유저 바뀌면 1페이지로 리셋
if st.session_state.get("last_uid") != uid:
    st.session_state.page = 1
    st.session_state.last_uid = uid

# 페이지 UI
with colC:
    st.markdown(" ")
    left, mid, right = st.columns([1, 2, 1])

    with left:
        if st.button("⬅ 이전"):
            st.session_state.page = max(1, st.session_state.page - 1)

    with mid:
        st.session_state.page = st.number_input(
            "페이지",
            min_value=1,
            max_value=total_pages,
            value=st.session_state.page,
            step=1
        )

    with right:
        if st.button("다음 ➡"):
            st.session_state.page = min(total_pages, st.session_state.page + 1)

page = st.session_state.page
start = (page - 1) * PAGE_SIZE
end = min(start + PAGE_SIZE, total)

st.caption(f"총 {total}개 / {total_pages}페이지  •  현재 {page}페이지 ( {start+1} ~ {end} )")

# =========================
# 리스트 출력
# =========================
for rank, r in enumerate(results[start:end], start=start + 1):
    pid = r.get("project_id")
    proj = projects_idx.get(pid, {})

    final_score = r.get("final_score", r.get("final", 0.0))
    cbf_norm = r.get("cbf_norm", r.get("cbf", 0.0))
    cf_norm = r.get("cf_norm", r.get("cf", 0.0))
    cbf_raw = r.get("cbf_score", 0.0)
    cf_raw = r.get("cf_score", 0.0)

    deadline = r.get("deadline") or proj.get("deadline")

    st.markdown("---")
    header_cols = st.columns([2, 2, 2, 2, 2])
    header_cols[0].markdown(f"### {rank}. `{pid}`")
    header_cols[1].metric("Final", f"{final_score:.4f}")
    header_cols[2].metric("CBF (norm)", f"{cbf_norm:.4f}")
    header_cols[3].metric("CF (norm)", f"{cf_norm:.4f}")
    header_cols[4].markdown(
        f"**Deadline**  \n`{deadline}`{' 🔴' if is_expired(str(deadline)) else ''}"
    )

    st.caption(f"raw → cbf: {cbf_raw:.4f}, cf: {cf_raw:.4f}")

    with st.expander("📄 프로젝트 정보 보기", expanded=False):
        p_text = safe_get(proj, "p_text", safe_get(r, "p_text", ""))
        p_skill = safe_get(proj, "p_skill", safe_get(r, "p_skill", ""))
        p_role = safe_get(proj, "p_role", safe_get(r, "p_role", ""))
        p_field = safe_get(proj, "p_field", safe_get(r, "p_field", ""))

        st.markdown("**설명**")
        st.write(p_text if p_text else "설명 텍스트 없음")

        info_cols = st.columns(3)
        with info_cols[0]:
            st.markdown("**필요 스킬**")
            st.write(p_skill if p_skill else "-")
        with info_cols[1]:
            st.markdown("**모집 역할**")
            st.write(p_role if p_role else "-")
        with info_cols[2]:
            st.markdown("**분야**")
            st.write(p_field if p_field else "-")

        st.markdown("**원본 JSON**")
        st.json(proj if proj else {"message": "project_textified.jsonl에 해당 project_id가 없습니다."})
