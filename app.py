import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_LINE_SPACING
import re
import base64
import tempfile
import os

# ====================== CẤU HÌNH ======================
st.set_page_config(page_title="Soạn Đề Trắc Nghiệm - THCS Tân Hội Đông", page_icon="test_tube", layout="centered")

st.markdown("""
<style>
    .main-title {font-size: 3rem; color: #c62828; text-align: center; font-weight: bold; margin: 20px 0;}
    .sub-title {font-size: 1.5rem; color: #1565c0; text-align: center; font-weight: bold; margin-bottom: 40px;}
    .stButton>button {background: linear-gradient(45deg, #c62828, #e53935); color: white; font-weight: bold; height: 60px; font-size: 20px; border-radius: 12px;}
</style>
""", unsafe_allow_html=True)

# ====================== API KEY (ĐÃ SỬA ĐÚNG) ======================
if "GEMINI_API_KEY" not in st.secrets:
    st.error("⚠️ Chưa tìm thấy GEMINI_API_KEY trong Secrets!")
    st.info("Vào Settings → Secrets → thêm dòng:\nGEMINI_API_KEY = \"AIzaSy...\"")
    st.stop()
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

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
    uploaded = st.file_uploader("Tải giáo án (PDF hoặc Word)", type=["pdf", "docx"])
    content = read_file(uploaded) if uploaded else ""
    if uploaded and content:
        st.success(f"Đã đọc: {uploaded.name} ✓")

with col2:
    st.subheader("2. Cấu hình đề")
    levels = st.multiselect("Mức độ", ["Biết", "Hiểu", "Vận dụng"], default=["Hiểu"])
    types = st.multiselect("Loại câu hỏi", ["4 đáp án", "Đúng/Sai", "Nhiều lựa chọn đúng"], default=["4 đáp án"])
    num = st.slider("Số lượng câu hỏi", 5, 25, 15)
    add_image = st.checkbox("Tự động thêm hình minh hoạ cho câu Hình học", value=True)

# ====================== TẠO ĐỀ ======================
if st.button("XUẤT ĐỀ WORD / PDF NGAY", use_container_width=True):
    if not objectives or not content:
        st.error("Thiếu yêu cầu cần đạt hoặc file giáo án!")
    elif not levels or not types:
        st.error("Chọn ít nhất 1 mức độ và 1 loại câu hỏi!")
    else:
        with st.spinner("Đang soạn đề + vẽ hình (nếu có)... khoảng 15–30 giây"):
            model = genai.GenerativeModel("gemini-2.5-flash")
            prompt = f"""
            Soạn đúng {num} câu trắc nghiệm chất lượng cao, bám sát:
            Yêu cầu cần đạt: {objectives}
            Nội dung bài học: {content[:28000]}

            Mức độ: {', '.join(levels)}
            Loại câu hỏi: {', '.join(types)}

            QUAN TRỌNG:
            - KHÔNG chào hỏi, KHÔNG giải thích, KHÔNG lời thừa.
            - Công thức toán viết rõ: √(x+1), x², △ABC, ∠A=90°...
            - Nếu là câu HÌNH HỌC → ghi ngay dưới câu hỏi: [HÌNH MINH HỌA]
            - Mỗi đáp án 1 dòng riêng.
            - Đáp án đúng ghi ở cuối: → Đáp án: B

            Ví dụ:
            Câu 1. Cho tam giác ABC vuông tại A...
            [HÌNH MINH HỌA]
            A. 30°
            B. 45°
            C. 60°
            D. 90°
            → Đáp án: B
            ---
            """
            try:
                resp = model.generate_content(prompt)
                raw = resp.text
                st.session_state.raw = raw
                st.success("ĐÃ SOẠN XONG! Đang tạo file Word/PDF...")
            except Exception as e:
                st.error(f"Lỗi AI: {e}")
                st.stop()

        # ====================== TẠO FILE WORD + PDF ======================
        doc = Document()
        section = doc.sections[0]
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = section.right_margin = Inches(0.8)

        # Font + giãn dòng
        style = doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = Pt(13)

        lines = st.session_state.raw.split('\n')
        for line in lines:
            line = line.strip()
            if not line: continue

            if line.lower().startswith("câu"):
                p = doc.add_paragraph(line, style='Normal')
                p.runs[0].bold = True
                p.paragraph_format.line_spacing = 1.5

            elif "[HÌNH MINH HỌA]" in line and add_image:
                with st.spinner("Đang vẽ hình minh hoạ..."):
                    try:
                        img_model = genai.GenerativeModel("gemini-2.5-flash")
                        img_resp = img_model.generate_content(
                            [f"Vẽ hình minh hoạ sạch, rõ nét cho câu hỏi hình học sau (chỉ hình, không chữ): {line.replace('[HÌNH MINH HỌA]', '')[:300]}"],
                            generation_config={"response_mime_type": "image/jpeg"}
                        )
                        img_data = img_resp.candidates[0].content.parts[0].inline_data.data
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
                            f.write(base64.b64decode(img_data))
                            img_path = f.name
                        doc.add_picture(img_path, width=Inches(4))
                        os.unlink(img_path)
                        doc.add_paragraph()
                    except:
                        doc.add_paragraph("(Hình minh hoạ tạm thời không tạo được)")

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
                run.bold = True
                run.font.color.rgb = docx.shared.RGBColor(255, 0, 0)
                run.font.size = Pt(13)

            elif "---" in line:
                doc.add_page_break() if num > 15 else doc.add_paragraph()

        # Lưu file tạm
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            doc.save(tmp.name)
            docx_path = tmp.name

        with open(docx_path, "rb") as f:
            docx_bytes = f.read()
        os.unlink(docx_path)

        # Tạo PDF (nếu được)
        try:
            from docx2pdf import convert
            pdf_path = docx_path.replace(".docx", ".pdf")
            convert(docx_path.replace(".docx", ".docx"), pdf_path)  # fix path
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            os.unlink(pdf_path)
        except:
            pdf_bytes = None

        # Nút tải
        c1, c2 = st.columns(2)
        c1.download_button(
            "TẢI FILE WORD (.docx)",
            data=docx_bytes,
            file_name="De_Trac_Nghiem_Tan_Hoi_Dong.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
        if pdf_bytes:
            c2.download_button(
                "TẢI FILE PDF (để in luôn)",
                data=pdf_bytes,
                file_name="De_Trac_Nghiem_Tan_Hoi_Dong.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            c2.info("PDF chỉ tạo được khi chạy trên máy Windows/Mac")

        st.balloons()
        st.success("XONG! Tải về và in cho học sinh thôi thầy/cô ơi ❤️")
