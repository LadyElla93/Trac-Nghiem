import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document

# ====================== CẤU HÌNH ======================
st.set_page_config(page_title="Trợ Lý Soạn Trắc Nghiệm", page_icon="test_tube", layout="wide")

st.markdown("""
<style>
    .main {background-color: #f8f9fa;}
    .stButton>button {background-color: #0068c9; color: white; font-weight: bold; height: 60px; font-size: 18px;}
    .stButton>button:hover {background-color: #004b8d;}
</style>
""", unsafe_allow_html=True)

# ====================== API KEY ======================
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    key = st.sidebar.text_input("Gemini API Key", type="password")
    if key:
        genai.configure(api_key=key)
    else:
        st.error("Vui lòng nhập API Key!")
        st.stop()

# ====================== ĐỌC FILE ======================
def read_file(file):
    if file.name.endswith(".pdf"):
        return " ".join([p.extract_text() or "" for p in PdfReader(file).pages])
    else:
        return "\n".join([p.text for p in Document(file).paragraphs if p.text])

# ====================== GIAO DIỆN ======================
st.title("TRỢ LÝ SOẠN ĐỀ TRẮC NGHIỆM AI")

c1, c2 = st.columns(2)

with c1:
    st.subheader("1. Nhập dữ liệu")
    objectives = st.text_area("Yêu cầu cần đạt (bắt buộc)", height=140)
    uploaded = st.file_uploader("Tải giáo án (PDF/DOCX)", type=["pdf", "docx"])
    content = read_file(uploaded) if uploaded else ""

    if uploaded and content:
        st.success(f"Đã đọc: {uploaded.name} ({len(content.split())} từ)")

with c2:
    st.subheader("2. Cấu hình")
    levels = st.multiselect("Mức độ", ["Biết", "Hiểu", "Vận dụng"], default=["Hiểu"])
    types = st.multiselect("Loại câu hỏi", ["4 đáp án", "Đúng/Sai", "Nhiều đáp án đúng"], default=["4 đáp án"])
    num = st.slider("Số câu hỏi", 5, 30, 15)

# ====================== TẠO ĐỀ ======================
if st.button("SOẠN ĐỀ NGAY", use_container_width=True):
    if not objectives or not content:
        st.error("Thiếu yêu cầu cần đạt hoặc file giáo án!")
    else:
        with st.spinner("AI đang soạn đề... (10-25 giây)"):
            # DÒNG DUY NHẤT HOẠT ĐỘNG ỔN ĐỊNH 100% THÁNG 12/2025
            model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
            
            prompt = f"""
            Soạn đúng {num} câu trắc nghiệm bám sát:
            YÊU CẦU CẦN ĐẠT: {objectives}
            NỘI DUNG BÀI HỌC: {content[:32000]}

            Mức độ: {", ".join(levels)}
            Loại: {", ".join(types)}

            Định dạng rõ ràng, có đáp án + giải thích.
            """
            try:
                response = model.generate_content(prompt)
                result = response.text
                st.session_state.result = result
                st.success("HOÀN TẤT!")
            except Exception as e:
                st.error(f"Lỗi: {e}")

# ====================== HIỂN THỊ ======================
if "result" in st.session_state:
    st.markdown("---")
    st.subheader("KẾT QUẢ ĐỀ TRẮC NGHIỆM")
    st.markdown(st.session_state.result)

    st.download_button(
        "TẢI VỀ (.txt)",
        st.session_state.result,
        "De_Trac_Nghiem_Gemini.txt",
        type="primary",
        use_container_width=True
    )