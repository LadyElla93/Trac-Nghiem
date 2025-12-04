import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document
import io

# --- Cấu hình trang ---
st.set_page_config(
    page_title="Trợ Lý Soạn Trắc Nghiệm",
    page_icon="📝",
    layout="wide"
)

# --- CSS tùy chỉnh để giao diện đẹp hơn ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4CAF50;
        text-align: center;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #333;
        margin-top: 20px;
    }
    .question-box {
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #2196F3;
        margin-bottom: 20px;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- Hàm đọc nội dung file ---
def read_pdf(file):
    try:
        pdf_reader = PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Lỗi đọc file PDF: {e}")
        return None

def read_docx(file):
    try:
        doc = Document(file)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        st.error(f"Lỗi đọc file Word: {e}")
        return None

# --- Giao diện chính ---
st.markdown('<p class="main-header">📝 Ứng Dụng Soạn Trắc Nghiệm Tự Động</p>', unsafe_allow_html=True)
st.markdown("---")

# 1. Cài đặt API Key
with st.sidebar:
    st.header("⚙️ Cấu hình")
    api_key = st.text_input("Nhập Google Gemini API Key", type="password", help="Bạn cần lấy API Key miễn phí tại aistudio.google.com")
    if not api_key:
        st.warning("Vui lòng nhập API Key để bắt đầu.")
    
    st.markdown("---")
    st.info("Hướng dẫn:\n1. Nhập API Key.\n2. Dán 'Yêu cầu cần đạt'.\n3. Tải file giáo án lên.\n4. Chọn cấu hình câu hỏi và bấm 'Soạn đề'.")

# 2. Khu vực nhập liệu (Bắt buộc)
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<p class="sub-header">1. Nội dung đầu vào</p>', unsafe_allow_html=True)
    
    # Nhập yêu cầu cần đạt (Bắt buộc)
    learning_objectives = st.text_area(
        "Yêu cầu cần đạt (Bắt buộc dán vào đây): (*)",
        height=150,
        placeholder="Ví dụ: Học sinh cần nắm vững định nghĩa, biết vận dụng công thức tính..."
    )

    # Tải file
    uploaded_file = st.file_uploader("Tải lên giáo án (PDF hoặc DOCX)", type=['pdf', 'docx'])
    
    file_content = ""
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.pdf'):
            file_content = read_pdf(uploaded_file)
        elif uploaded_file.name.endswith('.docx'):
            file_content = read_docx(uploaded_file)
        
        if file_content:
            st.success(f"Đã đọc xong file: {uploaded_file.name}")
            with st.expander("Xem trước nội dung file"):
                st.text(file_content[:500] + "...")

with col2:
    st.markdown('<p class="sub-header">2. Cấu hình câu hỏi</p>', unsafe_allow_html=True)
    
    # Chọn mức độ
    levels = st.multiselect(
        "Chọn mức độ nhận thức:",
        ["Biết", "Hiểu", "Vận dụng"],
        default=["Biết", "Hiểu"]
    )
    
    # Chọn loại câu hỏi
    q_types = st.multiselect(
        "Chọn loại trắc nghiệm:",
        [
            "4 đáp án (1 đúng)", 
            "Đúng - Sai", 
            "Nhiều lựa chọn đúng (Chọn n trong 5)"
        ],
        default=["4 đáp án (1 đúng)"]
    )
    
    num_questions = st.slider("Số lượng câu hỏi dự kiến:", 1, 20, 5)

# 3. Xử lý logic tạo câu hỏi
if st.button("🚀 SOẠN ĐỀ NGAY"):
    if not api_key:
        st.error("Vui lòng nhập API Key trước.")
    elif not learning_objectives.strip():
        st.error("❌ BẮT BUỘC: Bạn chưa nhập 'Yêu cầu cần đạt'.")
    elif not file_content:
        st.error("❌ Vui lòng tải lên file giáo án.")
    elif not levels:
        st.error("Vui lòng chọn ít nhất một mức độ.")
    elif not q_types:
        st.error("Vui lòng chọn ít nhất một loại câu hỏi.")
    else:
        # Cấu hình AI
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        with st.spinner('Đang phân tích giáo án và yêu cầu cần đạt... Vui lòng đợi...'):
            try:
                # Tạo prompt (câu lệnh cho AI)
                prompt = f"""
                Bạn là một giáo viên giỏi. Hãy soạn {num_questions} câu hỏi trắc nghiệm dựa trên thông tin sau:
                
                1. **Nội dung bài học (Giáo án):**
                {file_content}
                
                2. **Yêu cầu cần đạt (Bắt buộc bám sát):**
                {learning_objectives}
                
                3. **Yêu cầu về cấu trúc:**
                - Mức độ câu hỏi: {', '.join(levels)}.
                - Loại câu hỏi cần soạn: {', '.join(q_types)}.
                
                **Quy định chi tiết từng loại:**
                - Nếu là "4 đáp án (1 đúng)": Tạo câu hỏi có 4 lựa chọn A, B, C, D. Chỉ 1 đúng.
                - Nếu là "Đúng - Sai": Đưa ra một nhận định và hỏi Đúng hay Sai.
                - Nếu là "Nhiều lựa chọn đúng": Tạo 5 lựa chọn (A, B, C, D, E). Số lượng đáp án đúng tối đa là 4.
                
                **Định dạng đầu ra mong muốn (Markdown):**
                Vui lòng trả về kết quả rõ ràng, tách biệt từng câu hỏi. Mỗi câu hỏi cần ghi rõ:
                - [Mức độ]
                - [Loại câu hỏi]
                - Nội dung câu hỏi
                - Các phương án
                - **Đáp án đúng**
                - **Giải thích ngắn gọn**
                """
                
                response = model.generate_content(prompt)
                st.session_state['result'] = response.text
                st.success("Đã soạn xong!")
                
            except Exception as e:
                st.error(f"Có lỗi khi gọi AI: {e}")

# 4. Hiển thị kết quả
if 'result' in st.session_state:
    st.markdown("---")
    st.markdown('<p class="sub-header">3. Kết quả soạn thảo</p>', unsafe_allow_html=True)
    
    # Hiển thị kết quả trong khung
    st.markdown(st.session_state['result'])
    
    # Nút tải về
    st.download_button(
        label="📥 Tải về kết quả (.txt)",
        data=st.session_state['result'],
        file_name="trac_nghiem.txt",
        mime="text/plain"
    )