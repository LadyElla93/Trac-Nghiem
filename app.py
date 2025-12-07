import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document
from docx.shared import Pt, Inches, RGBColor
import re
import base64
import tempfile
import os

# ====================== CẤU HÌNH ======================
st.set_page_config(page_title="Soạn Đề Siêu Dễ - THCS Tân Hội Đông", page_icon="test_tube", layout="wide")

st.markdown("""
<style>
    .main-title {font-size: 3.2rem; color: #c62828; text-align: center; font-weight: bold; margin: 30px 0;}
    .sub-title {font-size: 1.6rem; color: #1565c0; text-align: center; font-weight: bold; margin-bottom: 40px;}
    .stButton>button {background: linear-gradient(45deg, #c62828, #e53935); color: white; font-weight: bold; height: 70px; font-size: 22px; border-radius: 15px;}
    .big-checkbox {font-size: 1.4rem !important; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# ====================== API KEY ======================
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Lỗi: Chưa có GEMINI_API_KEY trong Secrets!")
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

# ====================== GIAO DIỆN SIÊU DỄ ======================
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Nhập nội dung bài học")
    objectives = st.text_area("Yêu cầu cần đạt (bắt buộc):", height=160,
        placeholder="VD: HS biết định nghĩa tam giác, hiểu tính chất, vận dụng định lý cosin...")
    
    uploaded = st.file_uploader("Tải giáo án (PDF hoặc Word)", type=["pdf", "docx"])
    content = read_file(uploaded) if uploaded else ""
    if uploaded and content:
        st.success(f"Đã đọc file: {uploaded.name}")

with col2:
    st.subheader("2. Chỉ cần TÍCH vào ô vuông")

    # ================= MỨC ĐỘ - CHECKBOX TO RÕ =================
    st.markdown("#### Mức độ nhận thức (tích vào ô vuông):")
    lv1 = st.checkbox("**Biết**", value=True, help="Câu hỏi nhớ, nhận biết")
    lv2 = st.checkbox("**Hiểu**", value=True, help="Câu hỏi hiểu bản chất")
    lv3 = st.checkbox("**Vận dụng**", value=False, help="Câu hỏi giải bài tập")

    selected_levels = []
    if lv1: selected_levels.append("Biết")
    if lv2: selected_levels.append("Hiểu")
    if lv3: selected_levels.append("Vận dụng")
    st.success(f"Đã chọn mức độ: **{', '.join(selected_levels) if selected_levels else 'Chưa chọn'}**")

    st.markdown("---")

    # ================= LOẠI CÂU HỎI - CHECKBOX TO RÕ =================
    st.markdown("#### Loại câu hỏi (tích vào ô vuông):")
    t1 = st.checkbox("**4 đáp án (1 đúng)**", value=True)
    t2 = st.checkbox("**Đúng - Sai**", value=False)
    t3 = st.checkbox("**Nhiều lựa chọn đúng** (chọn nhiều trong 5)", value=False)

    selected_types = []
    if t1: selected_types.append("4 đáp án")
    if t2: selected_types.append("Đúng/Sai")
    if t3: selected_types.append("Nhiều lựa chọn đúng")
    st.success(f"Đã chọn loại: **{', '.join(selected_types) if selected_types else 'Chưa chọn'}**")

    st.markdown("---")
    num_questions = st.slider("Số lượng câu hỏi:", 5, 25, 12, help="Thường 10–15 câu là đẹp")
    add_image = st.checkbox("Tự động thêm hình minh hoạ cho câu hỏi hình học", value=True)

# ====================== TẠO ĐỀ ======================
if st.button("TẠO ĐỀ & XUẤT FILE WORD NGAY", use_container_width=True):
    if not objectives.strip():
        st.error("Vui lòng nhập Yêu cầu cần đạt!")
    elif not content:
        st.error("Vui lòng tải file giáo án!")
    elif not selected_levels:
        st.error("Vui lòng chọn ít nhất 1 mức độ!")
    elif not selected_types:
        st.error("Vui lòng chọn ít nhất 1 loại câu hỏi!")
    else:
        with st.spinner("AI đang soạn đề chất lượng cao..."):
            model = genai.GenerativeModel("gemini-2.5-flash")
            prompt = f"""
            Soạn đúng {num_questions} câu trắc nghiệm, KHÔNG chào hỏi, KHÔNG giải thích.
            Bám sát yêu cầu cần đạt: {objectives}
            Nội dung bài học: {content[:25000]}

            Mức độ: {', '.join(selected_levels)}
            Loại câu hỏi: {', '.join(selected_types)}

            - Nếu là hình học → thêm dòng: [HÌNH MINH HỌA]
            - Công thức viết rõ: x², √2, △ABC, ∠A=90°
            - Mỗi đáp án 1 dòng
            - Đáp án đúng ở cuối: → Đáp án: B
            """
            try:
                response = model.generate_content(prompt)
                st.session_state.raw = response.text
                st.success("ĐÃ SOẠN XONG! Đang tạo file Word...")
            except Exception as e:
                st.error(f"Lỗi AI: {e}")
                st.stop()

        # ====================== TẠO FILE WORD (ĐÃ FIX RGBColor) ======================
        doc = Document()
        for sec in doc.sections:
            sec.top_margin = sec.bottom_margin = sec.left_margin = sec.right_margin = Inches(0.8)

        style = doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = Pt(13)

        lines = st.session_state.raw.split('\n')
        for line in lines:
            line = line.strip()
            if not line: continue

            p = doc.add_paragraph()
            p.paragraph_format.line_spacing = 1.5
            p.paragraph_format.space_after = Pt(6)

            if line.lower().startswith("câu"):
                run = p.add_run(line)
                run.bold = True

            elif "[hình minh họa" in line.lower() and add_image:
                try:
                    img_model = genai.GenerativeModel("gemini-2.5-flash")
                    img_resp = img_model.generate_content(
                        [f"Vẽ hình minh hoạ rõ nét cho câu hỏi hình học: {line.replace('[HÌNH MINH HỌA]', '')[:200]}"],
                        generation_config={"response_mime_type": "image/jpeg"}
                    )
                    img_data = img_resp.candidates[0].content.parts[0].inline_data.data
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                        tmp.write(base64.b64decode(img_data))
                        doc.add_picture(tmp.name, width=Inches(4))
                        os.unlink(tmp.name)
                    doc.add_paragraph()
                except:
                    p.add_run(" (Hình vẽ tay nếu cần)")

            elif re.match(r'^[A-E]\.', line):
                p.add_run(line)
                p.paragraph_format.left_indent = Inches(0.5)
                p.style = 'List Bullet'

            elif "đáp án:" in line.lower():
                match = re.search(r'[A-EĐúngSai]', line, re.IGNORECASE)
                ans = match.group(0).upper() if match else "?"
                if ans in ["ĐÚNG", "SAI"]: ans = ans.title()
                run = p.add_run(f"→ {ans}")
                run.bold = True
                run.font.color.rgb = RGBColor(255, 0, 0)

            else:
                p.add_run(line)

        # Lưu file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            doc.save(tmp.name)
            docx_path = tmp.name

        with open(docx_path, "rb") as f:
            docx_bytes = f.read()
        os.unlink(docx_path)

        # Nút tải
        st.download_button(
            label="TẢI FILE WORD (.docx) - MỞ LÀ ĐẸP NHƯ IN",
            data=docx_bytes,
            file_name="De_Trac_Nghiem_Tan_Hoi_Dong.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )

        st.success("XONG 100%! Tải về → Mở Word → In cho học sinh thôi thầy/cô ơi!")
        st.balloons()

        with st.expander("Xem trước đề (text)"):
            st.markdown(st.session_state.raw)