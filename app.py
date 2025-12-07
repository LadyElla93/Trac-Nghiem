import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document
import io

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="Hệ Thống Soạn Trắc Nghiệm AI",
    page_icon="📝",
    layout="wide"
)

# --- 2. CSS LÀM ĐẸP GIAO DIỆN ---
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        color: #0068C9;
        text-align: center;
        font-weight: 700;
        margin-bottom: 20px;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #333;
        font-weight: 600;
        margin-top: 10px;
    }
    .stButton>button {
        background-color: #0068C9;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        height: 50px;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #004B91;
    }
    .success-box {
        padding: 15px;
        background-color: #D4EDDA;
        color: #155724;
        border-radius: 5px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. CÁC HÀM XỬ LÝ FILE ---
def read_pdf(file):
    try:
        pdf_reader = PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception:
        return None

def read_docx(file):
    try:
        doc = Document(file)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception:
        return None

# --- 4. XỬ LÝ API KEY TỪ SECRETS (QUAN TRỌNG) ---
# Đoạn này giúp lấy Key ngầm, giáo viên không cần nhập
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        api_ready = True
    else:
        api_ready = False
except Exception:
    api_ready = False

# --- 5. GIAO DIỆN CHÍNH ---
st.markdown('<div class="main-header">📝 TRỢ LÝ SOẠN ĐỀ TRẮC NGHIỆM THÔNG MINH</div>', unsafe_allow_html=True)

# Kiểm tra Key trước khi cho dùng
if not api_ready:
    st.error("⚠️ Lỗi cấu hình: Chưa tìm thấy API Key trong hệ thống.")
    st.info("👉 Hướng dẫn cho Admin: Vào Settings của App trên Streamlit -> Tab Secrets -> Thêm dòng: GEMINI_API_KEY = 'mã_key_của_bạn'")
    st.stop()

col1, col2 = st.columns([1, 1], gap="medium")

with col1:
    st.markdown('<div class="sub-header">1. Dữ liệu đầu vào</div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.write("Vui lòng cung cấp nội dung bài học và yêu cầu:")
        
        # Nhập YCCĐ
        learning_objectives = st.text_area(
            "Yêu cầu cần đạt (Bắt buộc dán vào): (*)",
            height=150,
            placeholder="Ví dụ: Học sinh cần nắm được định nghĩa, vận dụng công thức tính..."
        )

        # Tải file
        uploaded_file = st.file_uploader("Tải file Giáo án (PDF/Word):", type=['pdf', 'docx'])
        
        # Xử lý đọc file ngay khi tải lên
        file_content = ""
        if uploaded_file is not None:
            if uploaded_file.name.endswith('.pdf'):
                file_content = read_pdf(uploaded_file)
            elif uploaded_file.name.endswith('.docx'):
                file_content = read_docx(uploaded_file)
            
            if file_content:
                st.markdown(f'<div class="success-box">✅ Đã đọc file: {uploaded_file.name}</div>', unsafe_allow_html=True)
            else:
                st.error("File không đọc được nội dung.")

with col2:
    st.markdown('<div class="sub-header">2. Cấu hình câu hỏi</div>', unsafe_allow_html=True)
    with st.container(border=True):
        # Chọn mức độ
        st.write("**Mức độ nhận thức:**")
        levels = st.multiselect(
            "Chọn mức độ:",
            ["Biết", "Hiểu", "Vận dụng"],
            default=["Biết", "Hiểu"],
            label_visibility="collapsed"
        )
        
        st.write("---")
        
        # Chọn loại câu hỏi
        st.write("**Loại câu hỏi:**")
        q_types = st.multiselect(
            "Chọn loại:",
            [
                "4 đáp án (1 đúng)", 
                "Đúng - Sai", 
                "Nhiều lựa chọn đúng (Chọn n trong 5)"
            ],
            default=["4 đáp án (1 đúng)"],
            label_visibility="collapsed"
        )
        
        st.write("---")
        
        # Số lượng
        num_questions = st.slider("Số lượng câu hỏi:", 1, 30, 10)

# --- 6. NÚT XỬ LÝ VÀ GỌI AI ---
st.markdown("---")
if st.button("🚀 BẮT ĐẦU SOẠN ĐỀ NGAY", use_container_width=True):
    if not learning_objectives.strip():
        st.warning("⚠️ Vui lòng nhập 'Yêu cầu cần đạt'.")
    elif not file_content:
        st.warning("⚠️ Vui lòng tải file giáo án lên.")
    elif not levels:
        st.warning("⚠️ Hãy chọn ít nhất một mức độ.")
    elif not q_types:
        st.warning("⚠️ Hãy chọn ít nhất một loại câu hỏi.")
    else:
        # Prompt gửi cho AI
        prompt = f"""
        Bạn là trợ lý giáo dục chuyên nghiệp. Hãy soạn {num_questions} câu hỏi trắc nghiệm dựa trên:
        
        1. NỘI DUNG TÀI LIỆU:
        {file_content}
        
        2. YÊU CẦU CẦN ĐẠT (QUAN TRỌNG - PHẢI BÁM SÁT):
        {learning_objectives}
        
        3. CẤU TRÚC:
        - Mức độ: {', '.join(levels)}
        - Loại câu hỏi: {', '.join(q_types)}
        
        4. QUY TẮC SOẠN CÂU HỎI:
        - "4 đáp án": 4 lựa chọn A,B,C,D. 1 đúng.
        - "Đúng - Sai": Nhận định -> Đúng/Sai.
        - "Nhiều lựa chọn": 5 lựa chọn A,B,C,D,E. Tối đa 4 đúng.
        
        YÊU CẦU ĐẦU RA (Markdown):
        Trả về kết quả rõ ràng, mỗi câu hỏi cách nhau bởi dòng kẻ ngang (---).
        Định dạng:
        **Câu [số]:** [Nội dung] ([Mức độ] - [Loại])
        [Các đáp án]
        > **Đáp án đúng:** ...
        > **Giải thích:** ...
        """
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        with st.spinner('🤖 AI đang phân tích giáo án và soạn đề... Vui lòng đợi...'):
            try:
                response = model.generate_content(prompt)
                st.session_state['result'] = response.text
                st.success("🎉 Đã soạn xong! Kéo xuống để xem kết quả.")
            except Exception as e:
                st.error(f"Lỗi kết nối AI: {e}")

# --- 7. HIỂN THỊ KẾT QUẢ ---
if 'result' in st.session_state:
    st.markdown('<div class="sub-header">📋 Kết quả soạn thảo</div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(st.session_state['result'])
    
    # Nút tải về
    st.download_button(
        label="📥 Tải bộ câu hỏi về máy (.txt)",
        data=st.session_state['result'],
        file_name="bo_cau_hoi_trac_nghiem.txt",
        mime="text/plain",
        type="primary"
    )