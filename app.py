import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_LINE_SPACING
from docx.oxml.ns import qn
import re
import base64
import os
import tempfile

# ====================== CẤU HÌNH ======================
st.set_page_config(page_title="Soạn Đề Trắc Nghiệm - THCS Tân Hội Đông", page_icon="test_tube", layout="wide")

st.markdown("""
<style>
    .main-title {font-size: 3rem; color: #c62828; text-align: center; font-weight: bold; margin: 20px 0;}
    .sub-title {font-size: 1.5rem; color: #1565c0; text-align: center; font-weight: bold; margin-bottom: 40px;}
    .stButton>button {background: linear-gradient(45deg, #c62828, #e53935); color: white; font-weight: bold; height: 60px; font-size: 20px; border-radius: 12px;}
</style>
""", unsafe_allow_html=True)

# ====================== API KEY ======================
if "GEMIMI_API_KEY" not in st.secrets:
    st.error("Vui lòng thêm GEMIMI_API_KEY vào Secrets trên Streamlit!")
    st.stop()
genai.configure(api_key=st.secrets["GEMIMI_API_KEY"])

# ====================== ĐỌC FILE ======================
def read_file(file):
    if file.name.endswith(".pdf"):
        try: return " ".join([p.extract_text() or "" for p in PdfReader(file).pages])
        except: return None
    else:
        try: return "\n".join([p.text for p in Document(file).paragraphs if p.text.strip()])
        except: return None

# ====================== TIÊU ĐỀ ======================
st.markdown('<div class="main-title">SOẠN ĐỀ TRẮC NGHIỆM</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Bản Demo của Trường THCS Tân Hội Đông - Đồng Tháp</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Nội dung đầu vào")
    objectives = st.text_area("Yêu cầu cần đạt (bắt buộc)", height=140)
    uploaded = st.file_uploader("Tải giáo án (PDF/Word)", type=["pdf", "docx"])
    content = read_file(uploaded) if uploaded else ""

with col2:
    st.subheader("2. Cấu hình")
    levels = st.multiselect("Mức độ", ["Biết", "Hiểu", "Vận dụng"], default=["Hiểu"])
    types = st.multiselect("Loại câu hỏi", ["4 đáp án", "Đúng/Sai", "Nhiều lựa chọn đúng"], default=["4 đáp án"])
    num = st.slider("Số lượng câu hỏi", 5, 20, 10)
    include_images = st.checkbox("Tự động thêm hình minh hoạ cho câu hỏi Hình học", value=True)

# ====================== TẠO ĐỀ ======================
if st.button("XUẤT FILE WORD / PDF", use_container_width=True):
    if not objectives or not content:
        st.error("Vui lòng nhập đầy đủ thông tin!")
    else:
        with st.spinner("AI đang soạn đề + vẽ hình (nếu có)..."):
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            prompt = f"""
            Soạn đúng {num} câu trắc nghiệm chất lượng cao, bám sát:
            - Yêu cầu cần đạt: {objectives}
            - Nội dung bài học: {content[:28000]}

            Mức độ: {', '.join(levels)}
            Loại câu hỏi: {', '.join(types)}

            QUAN TRỌNG:
            - KHÔNG chào hỏi, KHÔNG giải thích.
            - Công thức toán viết rõ: √(x+1), x² + 2x + 1 = 0, △ABC, ∠A = 90°...
            - Nếu là câu hỏi HÌNH HỌC → đánh dấu: [HÌNH MINH HỌA]
            - Đáp án đúng ghi ở cuối: → Đáp án: B
            - Mỗi đáp án 1 dòng.

            Ví dụ:
            Câu 1. Cho tam giác ABC vuông tại A...
            [HÌNH MINH HỌA]
            A. 3   B. 4   C. 5   D. 6
            → Đáp án: C
            ---
            """
            try:
                response = model.generate_content(prompt)
                raw_text = response.text
                st.session_state.raw = raw_text
                st.success("ĐÃ TẠO THÀNH CÔNG! Đang xuất file...")
            except Exception as e:
                st.error(f"Lỗi: {e}")
                st.stop()

        # ====================== XỬ LÝ XUẤT FILE DOCX + PDF ======================
        doc = Document()
        doc.sections[0].top_margin = Inches(0.8)
        doc.sections[0].bottom_margin = Inches(0.8)
        doc.sections[0].left_margin = Inches(0.8)
        doc.sections[0].right_margin = Inches(0.8)

        # Font chuẩn
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Times New Roman'
        font.size = Pt(13)

        # Giãn dòng 1.5
        for paragraph in doc.paragraphs:
            paragraph.paragraph_format.line_spacing = 1.5
            paragraph.paragraph_format.space_after = Pt(6)

        lines = raw_text.split('\n')
        current_q = None

        for line in lines:
            line = line.strip()
            if not line: continue

            if line.lower().startswith("câu"):
                p = doc.add_paragraph()
                run = p.add_run(line)
                run.bold = True
                run.font.size = Pt(13)
                current_q = p
                p.paragraph_format.line_spacing = 1.5

            elif "[HÌNH MINH HỌA]" in line and include_images:
                with st.spinner("Đang vẽ hình minh hoạ..."):
                    img_model = genai.GenerativeModel("gemini-2.5-flash")
                    img_prompt = f"Vẽ hình minh hoạ cho câu hỏi hình học sau (chỉ hình, không chữ): {line.replace('[HÌNH MINH HỌA]', '')[:200]}"
                    try:
                        img_resp = img_model.generate_content([img_prompt], generation_config={"response_mime_type": "image/jpeg"})
                        img_bytes = img_resp.candidates[0].content.parts[0].inline_data.data
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                            tmp.write(base64.b64decode(img_bytes))
                            tmp_path = tmp.name
                        doc.add_picture(tmp_path, width=Inches(3.5))
                        os.unlink(tmp_path)
                    except:
                        doc.add_paragraph("(Hình minh hoạ không tạo được)")

            elif re.match(r'^[A-D]\.', line) or re.match(r'^[A-D]\)', line):
                p = doc.add_paragraph(line, style='List Bullet')
                p.paragraph_format.left_indent = Inches(0.5)
                p.paragraph_format.line_spacing = 1.5

            elif "→ Đáp án:" in line:
                match = re.search(r'[A-EĐúngSai]', line, re.IGNORECASE)
                ans = match.group(0).upper() if match else "?"
                if ans == "ĐÚNG": ans = "Đúng"
                if ans == "SAI": ans = "Sai"
                p = doc.add_paragraph()
                run = p.add_run(f"→ {ans}")
                run.font.color.rgb = docx.shared.RGBColor(255, 0, 0)
                run.bold = True
                run.font.size = Pt(13)

            elif "---" in line:
                doc.add_paragraph()

        # Lưu file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            doc.save(tmp.name)
            docx_path = tmp.name

        with open(docx_path, "rb") as f:
            docx_bytes = f.read()

        # Tạo PDF (nếu có)
        try:
            from docx2pdf import convert
            pdf_path = docx_path.replace(".docx", ".pdf")
            convert(docx_path, pdf_path)
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            os.unlink(pdf_path)
        except:
            pdf_bytes = None

        os.unlink(docx_path)

        col_a, col_b = st.columns(2)
        with col_a:
            st.download_button(
                "TẢI FILE WORD (.docx)",
                data=docx_bytes,
                file_name="De_Trac_Nghiem_THCS_Tan_Hoi_Dong.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        with col_b:
            if pdf_bytes:
                st.download_button(
                    "TẢI FILE PDF (để in)",
                    data=pdf_bytes,
                    file_name="De_Trac_Nghiem_THCS_Tan_Hoi_Dong.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.info("PDF không tạo được (cài docx2pdf trên máy nếu cần)")

        st.success("XUẤT FILE THÀNH CÔNG! Mở Word là đẹp như in")