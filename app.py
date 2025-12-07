import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document
import re

# ====================== CẤU HÌNH ======================
st.set_page_config(page_title="Soạn Đề Trắc Nghiệm Đẹp Như Word", page_icon="test_tube", layout="wide")

st.markdown("""
<style>
    .main-header {font-size: 2.6rem; color: #0068C9; text-align: center; font-weight: bold; margin: 30px 0;}
    .stButton>button {background: linear-gradient(45deg, #0068C9, #0080FF); color: white; font-weight: bold; height: 60px; font-size: 19px; border-radius: 12px;}
    .correct-answer {color: red; font-weight: bold; font-size: 1.4em;}
    .question-block {background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 6px solid #0068C9; margin: 15px 0;}
    .checkbox-box {background-color: #e8f4fc; padding: 12px; border-radius: 8px; border: 1px solid #0068C9;}
</style>
""", unsafe_allow_html=True)

# ====================== API KEY ======================
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    key = st.sidebar.text_input("Gemini API Key", type="password", help="Lấy miễn phí tại: aistudio.google.com")
    if key: genai.configure(api_key=key)
    else:
        st.error("Nhập API Key để tiếp tục!")
        st.stop()

# ====================== ĐỌC FILE ======================
def read_file(file):
    if file.name.endswith(".pdf"):
        try: return " ".join([p.extract_text() or "" for p in PdfReader(file).pages])
        except: return None
    else:
        try: return "\n".join([p.text for p in Document(file).paragraphs if p.text.strip()])
        except: return None

# ====================== GIAO DIỆN ======================
st.markdown('<div class="main-header">SOẠN ĐỀ TRẮC NGHIỆM ĐẸP NHƯ WORD</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Nhập nội dung")
    objectives = st.text_area("Yêu cầu cần đạt (bắt buộc)", height=140)
    uploaded = st.file_uploader("Tải giáo án (PDF hoặc Word)", type=["pdf", "docx"])
    content = read_file(uploaded) if uploaded else ""
    if uploaded and content:
        st.success(f"Đã đọc: {uploaded.name}")

with col2:
    st.subheader("2. Cấu hình câu hỏi")
    
    # Mức độ - checkbox đẹp
    st.markdown("**Mức độ nhận thức:**")
    c1, c2, c3 = st.columns(3)
    lv1 = c1.checkbox("Biết", True)
    lv2 = c2.checkbox("Hiểu", True)
    lv3 = c3.checkbox("Vận dụng", False)
    selected_levels = [x for x, y in zip(["Biết","Hiểu","Vận dụng"], [lv1,lv2,lv3]) if y]
    if selected_levels:
        st.markdown(f"<div class='checkbox-box'>Mức độ: **{', '.join(selected_levels)}**</div>", unsafe_allow_html=True)

    # Loại câu hỏi
    st.markdown("**Loại câu hỏi:**")
    t1 = st.checkbox("4 đáp án (1 đúng)", True)
    t2 = st.checkbox("Đúng - Sai", False)
    t3 = st.checkbox("Nhiều lựa chọn đúng", False)
    selected_types = []
    if t1: selected_types.append("4 đáp án")
    if t2: selected_types.append("Đúng/Sai")
    if t3: selected_types.append("Nhiều lựa chọn")
    if selected_types:
        st.markdown(f"<div class='checkbox-box'>Loại: **{', '.join(selected_types)}**</div>", unsafe_allow_html=True)

    num = st.slider("Số lượng câu hỏi", 5, 30, 15)

# ====================== SOẠN ĐỀ ======================
if st.button("TẠO ĐỀ NGAY", use_container_width=True):
    if not objectives or not content or not selected_levels or not selected_types:
        st.error("Vui lòng nhập đầy đủ thông tin!")
    else:
        with st.spinner("Gemini 2.5 Flash đang soạn đề đẹp cho bạn..."):
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            prompt = f"""
            Bạn là giáo viên giỏi nhất Việt Nam. Soạn đúng {num} câu trắc nghiệm chất lượng cao.
            BÁM SÁT:
            - Yêu cầu cần đạt: {objectives}
            - Nội dung bài học: {content[:30000]}

            Mức độ: {', '.join(selected_levels)}
            Loại câu hỏi: {', '.join(selected_types)}

            QUAN TRỌNG:
            - Công thức toán PHẢI viết dưới dạng văn bản thuần (VD: a² + b² = c², √(x+1), tam giác ABC, ∠A = 90°...) → để giáo viên copy vào Word vẫn đẹp (không dùng LaTeX).
            - Không giải thích.
            - Đáp án đúng ghi riêng ở cuối mỗi câu: → Đáp án: B

            Định dạng:
            **Câu 1.** Tam giác ABC có a = 3, b = 4, c = 5. Tam giác này là tam giác gì?
            A. Thường
            B. Vuông
            C. Cân
            D. Đều
            → Đáp án: B
            ---
            """
            try:
                resp = model.generate_content(prompt)
                st.session_state.result = resp.text
                st.success("HOÀN TẤT! Đề đẹp sẵn sàng!")
            except Exception as e:
                st.error(f"Lỗi: {e}")

# ====================== HIỂN THỊ ĐẸP (Đáp án đỏ, không dòng thừa) ======================
if "result" in st.session_state:
    st.markdown("---")
    st.markdown("### ĐỀ TRẮC NGHIỆM ĐÃ HOÀN THIỆN")

    lines = st.session_state.result.split('\n')
    output = []

    for line in lines:
        line = line.strip()
        if not line: 
            continue

        # Phát hiện dòng đáp án
        if "→" in line or "Đáp án:" in line:
            # Lấy chữ cái đáp án đúng
            match = re.search(r'[A-E]|Đúng|Sai', line, re.IGNORECASE)
            if match:
                ans = match.group(0).upper()
                if ans == "ĐÚNG": ans = "Đúng"
                if ans == "SAI": ans = "Sai"
                output.append(f"<div class='correct-answer'>→ {ans}</div>")
            else:
                output.append(f"<div class='correct-answer'>{line}</div>")
        elif line.startswith(("A.", "B.", "C.", "D.", "E.", "A)", "B)", "C)", "D)", "E)")):
            output.append(f"**{line}**")
        elif line.startswith("Câu") or line.startswith("**Câu"):
            output.append(f"<div class='question-block'><strong>{line}</strong></div>")
        elif "---" in line:
            output.append("<hr>")
        else:
            output.append(line)

    st.markdown("\n".join(output), unsafe_allow_html=True)

    # Nút tải về
    st.download_button(
        "TẢI VỀ ĐỀ (Copy vào Word đẹp 100%)",
        data=st.session_state.result,
        file_name="De_Trac_Nghiem_Dep_Nhu_Word.txt",
        mime="text/plain",
        use_container_width=True,
        type="primary"
    )