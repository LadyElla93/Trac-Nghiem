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

# --- 2. CSS LÀM ĐẸP ---
st.markdown("""
<style>
    .main-header { font-size: 2rem; color: #0068C9; text-align: center; font-weight: 700; margin-bottom: 20px; }
    .sub-header { font-size: 1.2rem; color: #333; font-weight: 600; margin-top: 10px; }
    .stButton>button { background-color: #0068C9; color: white; font-weight: bold; border-radius: 8px; height: 50px; width: 100%; }
    .success-box { padding: 15px; background-color: #D4EDDA; color: #155724; border-radius: 5px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 3. CÁC HÀM ĐỌC FILE ---
def read_pdf(file):
    try:
        pdf_reader = PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except: return None

def read_docx(file):
    try:
        doc = Document(file)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except: return None

# --- 4. XỬ LÝ API KEY ---
try:
    # Ưu tiên lấy từ Secrets
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        api_ready = True
    else:
        api_ready = False
except Exception:
    api_ready = False

# --- 5. GIAO DIỆN ---
st.markdown('<div class="main-header">📝 TRỢ LÝ SOẠN ĐỀ TRẮC NGHIỆM AI</div>', unsafe_allow_html=True)

if not api_ready:
    st.error("⚠️ Chưa cấu hình API Key trong Secrets.")
    st.info("Vào Settings -> Secrets trên Streamlit để thêm key: GEMINI_API_KEY")
    st.stop()

col1, col2 = st.columns([1, 1], gap="medium")

with col1:
    st.markdown('<div class="sub-header">1. Dữ liệu đầu vào</div>', unsafe_allow_html=True)
    with st.container(border=True):
        learning_objectives = st.text_area("Yêu cầu cần đạt (*):", height=150)
        uploaded_file = st.file_uploader("Tải file Giáo án (PDF/Word):", type=['pdf', 'docx'])
        
        file_content = ""
        if uploaded_file:
            if uploaded_file.name.endswith('.pdf'): file_content = read_pdf(uploaded_file)
            elif uploaded_file.name.endswith('.docx'): file_content = read_docx(uploaded_file)
            
            if file_content: st.success(f"✅ Đã đọc file: {uploaded_file.name}")
            else: st.error("Lỗi đọc file.")

with col2:
    st.markdown('<div class="sub-header">2. Cấu hình câu hỏi</div>', unsafe_allow_html=True)
    with st.container(border=True):
        levels = st.multiselect("Mức độ:", ["Biết", "Hiểu", "Vận dụng"], default=["Biết", "Hiểu"])
        q_types = st.multiselect("Loại câu hỏi:", ["4 đáp án (1 đúng)", "Đúng - Sai", "Nhiều lựa chọn đúng"], default=["4 đáp án (1 đúng)"])
        num_questions = st.slider("Số lượng:", 1, 30, 10)

# --- 6. XỬ LÝ AI (ĐÃ SỬA LỖI MODEL) ---
st.markdown("---")
if st.button("🚀 BẮT ĐẦU SOẠN ĐỀ", use_container_width=True):
    if not learning_objectives or not file_content or not levels or not q_types:
        st.warning("⚠️ Vui lòng nhập đầy đủ thông tin và tải file.")
    else:
        prompt = f"""
        Bạn là giáo viên. Soạn {num_questions} câu trắc nghiệm.
        1. TÀI LIỆU: {file_content[:10000]}... (đã cắt bớt để tối ưu)
        2. YÊU CẦU: {learning_objectives}
        3. CẤU TRÚC: {', '.join(levels)} | {', '.join(q_types)}
        
        Xuất ra Markdown rõ ràng. Có đáp án và giải thích chi tiết.
        """
        
        with st.spinner('🤖 Đang kết nối AI...'):
            try:
                # Cố gắng dùng model mới nhất: Flash
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                st.session_state['result'] = response.text
                st.success("🎉 Thành công!")
            except Exception as e:
                # Nếu Flash lỗi, thử dùng model Pro cũ hơn
                try:
                    st.warning("⚠️ Model Flash đang bận, đang chuyển sang model dự phòng...")
                    model_backup = genai.GenerativeModel('gemini-pro')
                    response = model_backup.generate_content(prompt)
                    st.session_state['result'] = response.text
                    st.success("🎉 Thành công (Dùng model dự phòng)!")
                except Exception as e2:
                    st.error(f"❌ Lỗi kết nối: {e}")
                    st.error("Gợi ý: Hãy kiểm tra lại API Key hoặc tạo API Key mới.")

# --- 7. KẾT QUẢ ---
if 'result' in st.session_state:
    st.markdown(st.session_state['result'])
    st.download_button("📥 Tải về", st.session_state['result'], "ket_qua.txt")