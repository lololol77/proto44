
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import uuid

FIREBASE_URL = "https://project2-5d28e-default-rtdb.asia-southeast1.firebasedatabase.app/"

# 사용자 고유 ID (세션 기반)
def get_user_id():
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = str(uuid.uuid4())
    return st.session_state["user_id"]

# 청원 등록 함수
def add_petition(title, content, email):
    petition_id = str(uuid.uuid4())
    data = {
        "id": petition_id,
        "title": title,
        "content": content,
        "email": email,
        "likes": 0,
        "liked_by": [],
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    res = requests.put(f"{FIREBASE_URL}/petitions/{petition_id}.json", json=data)
    return res.ok

# 청원 목록 조회
def get_petitions(order_by="date"):
    res = requests.get(f"{FIREBASE_URL}/petitions.json")
    if res.ok and res.json():
        data = res.json()
        if order_by == "likes":
            return sorted(data.values(), key=lambda x: (x.get("likes", 0), x.get("date", "")), reverse=True)
        else:
            return sorted(data.values(), key=lambda x: x.get("date", ""), reverse=True)
    return []

# 좋아요 처리
def like_petition(petition, user_id):
    petition_id = petition["id"]
    if "liked_by" not in petition:
        petition["liked_by"] = []
    if user_id in petition["liked_by"]:
        return False
    petition["likes"] += 1
    petition["liked_by"].append(user_id)
    res = requests.patch(f"{FIREBASE_URL}/petitions/{petition_id}.json", json={
        "likes": petition["likes"],
        "liked_by": petition["liked_by"]
    })
    return res.ok

# 청원 삭제
def delete_petition(petition_id):
    res = requests.delete(f"{FIREBASE_URL}/petitions/{petition_id}.json")
    return res.ok

# CSV 다운로드
def get_petitions_csv():
    data = get_petitions()
    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode('utf-8')

# Streamlit UI
st.title("📢 동탄국제고 청원 시스템")

menu = ["청원 작성", "청원 목록", "CSV 다운로드"]
choice = st.sidebar.selectbox("메뉴 선택", menu)

if choice == "청원 작성":
    st.header("✍️ 새로운 청원 등록")
    title = st.text_input("제목")
    content = st.text_area("내용")
    email = st.text_input("이메일")
    if st.button("제출"):
        if title and content and email:
            if add_petition(title, content, email):
                st.success("✅ 청원이 등록되었습니다.")
            else:
                st.error("❌ 등록 실패. 다시 시도해주세요.")
        else:
            st.warning("모든 항목을 입력해주세요.")

elif choice == "청원 목록":
    st.header("📄 청원 목록")

    order_option = st.selectbox("정렬 기준", ["최신순", "좋아요순"])
    order_by = "likes" if order_option == "좋아요순" else "date"
    petitions = get_petitions(order_by=order_by)
    petitions = get_petitions(order_by=order_by)
    st.write("🔥 petitions:", petitions) 
    user_id = get_user_id()

    for p in petitions:
        st.subheader(p["title"])
        st.write(p["content"])
        st.caption(f"등록일: {p['date']} | 이메일: {p['email']} | 좋아요: {p['likes']}")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button(f"👍 좋아요 ({p['likes']})", key=f"like_{p['id']}"):
                if like_petition(p, user_id):
                    st.success("좋아요를 눌렀습니다!")
                else:
                    st.warning("이미 좋아요를 눌렀습니다!")

        with col2:
            with st.expander(f"삭제 (비밀번호 필요)", expanded=False):
                input_pw = st.text_input(f"청원 삭제 비밀번호 입력 (id: {p['id']})", type="password", key=f"pw_{p['id']}")
                if st.button("🗑️ 삭제", key=f"delete_{p['id']}"):
                    if input_pw == "777":
                        if delete_petition(p["id"]):
                            st.success("청원이 삭제되었습니다.")
                            st.rerun()
                        else:
                            st.error("❌ 삭제 실패. 다시 시도해주세요.")
                    else:
                        st.error("❌ 비밀번호가 틀렸습니다.")

elif choice == "CSV 다운로드":
    st.header("⬇️ 전체 청원 데이터 다운로드")
    csv = get_petitions_csv()
    st.download_button("📄 CSV 다운로드", data=csv, file_name="petitions.csv", mime="text/csv")
