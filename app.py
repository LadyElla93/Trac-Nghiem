import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document

# ====================== CẤU HÌNH ======================
st.set_page_config(page_title="Trợ Lý Soạn Đề Trắc Nghiệm", page_icon="test_tube", layout="wide")

st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #0068C9; text-align: center; font-weight: bold; margin-bottom: 30px;}
    .stButton>button {background-color: #0068C9; color: white; font-weight: bold; height: 60px; font-size: 18px; border-radius: 10px;}
    .stButton>button:hover {background-color: #004B91;}
    .answer-correct {color: red; font-weight: bold; font-size: 1.3em;}
    .checkbox-container {background-color: #f0f8ff; padding: 15px; border-radius: 10px; border-left: 5px solid #0068C9;}
</style>
""", unsafe_allow_html=True)

# ====================== API KEY ======================
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    key = st.sidebar.text_input("Gemini API Key (lấy tại aistudio.google.com)", type="password")
    if key:
        genai.configure(api_key=key)
    else:
        st.error("Vui lòng nhập API Key để sử dụng!")
        st.stop()

# ====================== ĐỌC FILE ======================
def read_file(file):
    if file.name.endswith(".pdf"):
        try:
            return " ".join([p.extract_text() or "" for p in PdfReader(file).pages])
        except: return None
    else:
        try:
            return "\n".join([p.text for p in Document(file).paragraphs if p.text.strip()])
        except: return None

# ====================== GIAO DIỆN ======================
st.markdown('<div class="main-header">TRỢ LÝ SOẠN ĐỀ TRẮC NGHIỆM AI</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Nhập nội dung bài học")
    objectives = st.text_area("Yêu cầu cần đạt (bắt buộc)", height=140, placeholder="VD: Học sinh biết định nghĩa, hiểu công thức, vận dụng giải bài tập...")
    
    uploaded = st.file_uploader("Tải giáo án (PDF hoặc Word)", type=["pdf", "docx"])
    content = ""
    if uploaded:
        content = read_file(uploaded)
        if content and len(content) > 100:
            st.success(f"Đã đọc file: {uploaded.name} ({len(content.split())} từ)")
        else:
            st.error("Không đọc được nội dung file.")
            content = ""

with col2:
    st.subheader("2. Chọn cấu hình câu hỏi")
    
    # --- MỨC ĐỘ - DẠNG CHECKBOX ---
    st.markdown("**Mức độ nhận thức:**")
    with st.container(border=True):
        col_a, col_b, col_c = st.columns(3)
        level_know = col_a.checkbox("Biết", value=True)
        level_understand = col_b.checkbox("Hiểu", value=True)
        level_apply = col_c.checkbox("Vận dụng", value=False)
        
        selected_levels = []
        if level_know: selected_levels.append("Biết")
        if level_understand: selected_levels.append("Hiểu")
        if level_apply: selected_levels.append("Vận dụng")
        
        if selected_levels:
            st.markdown(f"<div class='checkbox-container'>Đã chọn mức độ: **{', '.join(selected_levels)}**</div>", unsafe_allow_html=True)
        else:
            st.warning("Vui lòng chọn ít nhất 1 mức độ")

    st.markdown("---")
    
    # --- LOẠI CÂU HỎI - DẠNG CHECKBOX ---
    st.markdown("**Loại câu hỏi:**")
    with st.container(border=True):
        type_a = st.checkbox("4 đáp án (1 đúng)", value=True)
        type_b = st.checkbox("Đúng - Sai", value=False)
        type_c = st.checkbox("Nhiều lựa chọn đúng (chọn nhiều trong 5)", value=False)
        
        selected_types = []
        if type_a: selected_types.append("4 đáp án (1 đúng)")
        if type_b: selected_types.append("Đúng - Sai")
        if type_c: selected_types.append("Nhiều lựa chọn đúng")
        
        if selected_types:
            st.markdown(f"<div class='checkbox-container'>Đã chọn loại: **{', '.join(selected_types)}**</div>", unsafe_allow_html=True)
        else:
            st.warning("Vui lòng chọn ít nhất 1 loại câu hỏi")

    num_questions = st.slider("Số lượng câu hỏi", 5, 30, 12, help="Tối đa 30 câu để đảm bảo chất lượng")

# ====================== TẠO ĐỀ ======================
if st.button("SOẠN ĐỀ NGAY", use_container_width=True):
    if not objectives.strip():
        st.error("Vui lòng nhập Yêu cầu cần đạt!")
    elif not content:
        st.error("Vui lòng tải file giáo án!")
    elif not selected_levels:
        st.error("Vui lòng chọn ít nhất 1 mức độ!")
    elif not selected_types:
        st.error("Vui lòng chọn ít nhất 1 loại câu hỏi!")
    else:
        with st.spinner("AI đang soạn đề chất lượng cao... (15-25 giây)"):
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            prompt = f"""
            Soạn đúng {num_questions} câu trắc nghiệm chất lượng cao, bám sát:
            - Yêu cầu cần đạt: {objectives}
            - Nội dung giáo án: {content[:32000]}

            Mức độ: {', '.join(selected_levels)}
            Loại câu hỏi: {', '.join(selected_types)}

            QUAN TRỌNG: Chỉ trả về câu hỏi + đáp án, KHÔNG giải thích.
            Định dạng rõ ràng:
            **Câu X:** [nội dung]
            A. ...
            B. ...
            C. ...
            D. ...
            → Đáp án: B
            ---
            """
            try:
                response = model.generate_content(prompt)
                st.session_state.result = response.text
                st.success("HOÀN TẤT! Đề đã sẵn sàng bên dưới")
            except Exception as e:
                st.error(f"Lỗi kết nối AI: {e}")

# ====================== HIỂN THỊ KẾT QUẢ ĐẸP ======================
if "result" in st.session_state:
    st.markdown("---")
    st.markdown("### KẾT QUẢ ĐỀ TRẮC NGHIỆM")

    lines = st.session_state.result.split('\n')
    formatted = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Phát hiện dòng đáp án
        if "đáp án" in line.lower() or "→" in line or "answer" in line.lower():
            # Lấy chữ cái đáp án đúng
            import re
            match = re.search(r'[A-EĐúngSai]', line.upper())
            if match:
                answer = match.group(0)
                if answer == "ĐÚNG": answer = "Đúng"
                if answer == "SAI": answer = "Sai"
                formatted.append(f"<div class='answer-correct'>Đáp án đúng: {answer}</div>")
            else:
                formatted.append(f"<div class='answer-correct'>{line}</div>")
        elif line.startswith(("A.", "B.", "C.", "D.", "E.", "A)", "B)", "C)", "D)", "E)")) or "Đúng" in line or "Sai" in line:
            formatted.append(f"**{line}**")
        elif line.startswith("Câu") or line.startswith("**Câu"):
            formatted.append(f"### {line}")
        elif "---" in line:
            formatted.append("---")
        else:
            formatted.append(line)

    st.markdown("\n\n".join(formatted), unsafe_allow_html=True)

    st.download_button(
        "TẢI VỀ ĐỀ (có đáp án đỏ)",
        data=st.session_state.result,
        file_name="De_Trac_Nghiem_Dap_An_Do.txt",
        mime="text/plain",
        use_container_width=True,
        type="primary"
    )