import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="Trợ Lý Soạn Đề Trắc Nghiệm AI",
    page_icon="test_tube",
    layout="wide"
)

# --- 2. CSS LÀM ĐẸP ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        color: #0068C9;
        text-align: center;
        font-weight: 700;
        margin-bottom: 20px;
    }
    .stButton>button {
        background-color: #0068C9;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        height: 55px;
        font-size: 1.1rem;
    }
    .stButton>button:hover {
        background-color: #004B91;
    }
    .success-box {
        padding: 15px;
        background-color: #D4EDDA;
        color: #155724;
        border-radius: 8px;
        border-left: 6px solid #28a745;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. HÀM ĐỌC FILE ---
def read_pdf(file):
    try:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except:
        return None

def read_docx(file):
    try:
        doc = Document(file)
        text = "\n".join([para.text for para in doc.paragraphs if para.text])
        return text
    except:
        return None

# --- 4. LẤY API KEY TỪ SECRETS (khuyến khích) HOẶC NHẬP TAY ---
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    api_ready = True
else:
    api_key = st.sidebar.text_input("Google Gemini API Key", type="password", help="Lấy miễn phí tại https://aistudio.google.com/app/apikey")
    if api_key:
        genai.configure(api_key=api_key)
        api_ready = True
    else:
        api_ready = False

if not api_ready:
    st.error("API Key chưa được cấu hình!")
    st.info("👉 Cách 1 (khuyên dùng): Vào **Settings → Secrets** thêm dòng:\n`GEMINI_API_KEY = \"aiZa...\"`\n👉 Cách 2: Dán key vào ô bên trái.")
    st.stop()

# --- 5. GIAO DIỆN CHÍNH ---
st.markdown('<div class="main-header">TRỢ LÝ SOẠN ĐỀ TRẮC NGHIỆM THÔNG MINH</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("1. Dữ liệu đầu vào")
    with st.container(border=True):
        learning_objectives = st.text_area(
            "Yêu cầu cần đạt (BẮT BUỘC):",
            height=150,
            placeholder="VD: HS biết định nghĩa, hiểu công thức, vận dụng giải bài tập..."
        )

        uploaded_file = st.file_uploader("Tải giáo án (PDF hoặc Word)", type=["pdf", "docx"])
        file_content = ""

        if uploaded_file:
            if uploaded_file.name.endswith('.pdf'):
                file_content = read_pdf(uploaded_file)
            else:
                file_content = read_docx(uploaded_file)

            if file_content and len(file_content.strip()) > 100:
                st.markdown(f'<div class="success-box">Đã tải thành công: {uploaded_file.name}</div>', unsafe_allow_html=True)
            else:
                st.error("Không đọc được nội dung file. Hãy thử file khác.")
                file_content = ""

with col2:
    st.subheader("2. Cấu hình câu hỏi")
    with st.container(border=True):
        levels = st.multiselect("Mức độ nhận thức", ["Biết", "Hiểu", "Vận dụng"], default=["Biết", "Hiểu"])
        q_types = st.multiselect("Loại câu hỏi", [
            "4 đáp án (1 đúng)",
            "Đúng - Sai", 
            "Nhiều lựa chọn đúng (Chọn nhiều trong 5)"
        ], default=["4 đáp án (1 đúng)"])
        
        num_questions = st.slider("Số lượng câu hỏi", 1, 30, 12)

# --- 6. NÚT TẠO ĐỀ ---
if st.button("BẮT ĐẦU SOẠN ĐỀ NGAY", use_container_width=True):
    if not learning_objectives.strip():
        st.warning("Vui lòng nhập Yêu cầu cần đạt!")
    elif not file_content:
        st.warning("Vui lòng tải file giáo án!")
    elif not levels or not q_types:
        st.warning("Vui lòng chọn mức độ và loại câu hỏi!")
    else:
        # <<< DÒNG QUAN TRỌNG NHẤT – MODEL ĐÃ ĐƯỢC SỬA >>>
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        prompt = f"""
        Bạn là giáo viên giỏi chuyên soạn đề trắc nghiệm.
        Hãy tạo đúng {num_questions} câu hỏi dựa trên:

        YÊU CẦU CẦN ĐẠT (phải bám sát 100%): 
        {learning_objectives}

        NỘI DUNG GIÁO ÁN:
        {file_content[:30000]}  <!-- Giới hạn độ dài tránh quá tải -->

        YÊU CẦU:
        - Mức độ: {', '.join(levels)}
        - Loại câu hỏi: {', '.join(q_types)}

        Định dạng Markdown rõ ràng, mỗi câu cách nhau bằng ---
        Ví dụ:
        **Câu 1** [Mức độ: Hiểu - Loại: 4 đáp án]
        Câu hỏi...
        A. ...   B. ...   C. ...   D. ...
        > **Đáp án:** B
        > **Giải thích:** ...
        """

        with st.spinner("AI đang phân tích và soạn đề... (khoảng 10-20 giây)"):
            try:
                response = model.generate_content(prompt)
                result = response.text
                st.session_state.result = result
                st.success("HOÀN THÀNH! Kết quả nằm bên dưới")
            except Exception as e:
                st.error(f"Lỗi: {e}")

# --- 7. HIỂN THỊ KẾT QUẢ ---
if "result" in st.session_state:
    st.markdown("---")
    st.subheader("KẾT QUẢ ĐỀ TRẮC NGHIỆM")
    with st.container(border=True):
        st.markdown(st.session_state.result)

    st.download_button(
        label="TẢI VỀ ĐỀ TRẮC NGHIỆM (.txt)",
        data=st.session_state.result,
        file_name="De_Trac_Nghiem_AI.txt",
        mime="text/plain",
        type="primary",
        use_container_width=True
    )