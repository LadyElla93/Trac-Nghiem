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

# --- 6. XỬ LÝ AI (ĐÃ SỬA MODEL THÀNH GEMINI 2.5 FLASH) ---
st.markdown("---")
if st.button("🚀 BẮT ĐẦU SOẠN ĐỀ", use_container_width=True):
    if not learning_objectives or not file_content or not levels or not q_types:
        st.warning("⚠️ Vui lòng nhập đầy đủ thông tin và tải file.")
    else:
        prompt = f"""
        Bạn là giáo viên chuyên soạn đề trắc nghiệm. Sử dụng reasoning để đảm bảo chất lượng.
        
        Soạn đúng {num_questions} câu hỏi trắc nghiệm dựa trên:
        1. TÀI LIỆU GIÁO ÁN: {file_content[:10000]}... (tóm tắt nếu cần)
        2. YÊU CẦU CẦN ĐẠT (bám sát): {learning_objectives}
        3. CẤU TRÚC: Mức độ {', '.join(levels)} | Loại {', '.join(q_types)}
        
        Quy tắc:
        - 4 đáp án: A/B/C/D, chỉ 1 đúng.
        - Đúng-Sai: Nhận định + Đúng/Sai.
        - Nhiều lựa chọn: A/B/C/D/E, chỉ rõ số đúng.
        
        Định dạng Markdown: Mỗi câu cách nhau bằng ---. Bao gồm:
        **Câu [số]:** [Nội dung] ([Mức độ] - [Loại])
        Các đáp án...
        > **Đáp án:** ...
        > **Giải thích:** ...
        """
        
        with st.spinner('🤖 Đang kết nối AI (Gemini 2.5 Flash)...'):
            try:
                # Model mới nhất ổn định (tháng 12/2025)
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(prompt)
                st.session_state['result'] = response.text
                st.success("🎉 Thành công với Gemini 2.5 Flash!")
            except Exception as e:
                # Fallback sang model preview mạnh hơn nếu Flash bận
                try:
                    st.warning("⚠️ Flash bận, chuyển sang Gemini 3 Pro Preview...")
                    model_backup = genai.GenerativeModel('gemini-3-pro-preview')
                    response = model_backup.generate_content(prompt)
                    st.session_state['result'] = response.text
                    st.success("🎉 Thành công với Gemini 3 Pro!")
                except Exception as e2:
                    st.error(f"❌ Lỗi: {e}. Kiểm tra API Key hoặc quota. Gợi ý: Tạo key mới tại aistudio.google.com.")

# --- 7. KẾT QUẢ ---
if 'result' in st.session_state:
    st.markdown("---")
    st.markdown('<div class="sub-header">Kết quả soạn đề</div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(st.session_state['result'])
    st.download_button("📥 Tải về (.txt)", st.session_state['result'], "ket_qua_trac_nghiem.txt", mime="text/plain")