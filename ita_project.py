import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
import io
import sqlite3
import datetime
from hashlib import sha256


st.set_page_config(page_title="IT Risk Dashboard", layout="wide")

USERS = {
    "admin": sha256("admin123".encode()).hexdigest(),
    "analyst": sha256("analyst123".encode()).hexdigest(),
}

@st.cache_data(show_spinner=False)
def authenticate(username, password):
    hashed = sha256(password.encode()).hexdigest()
    return USERS.get(username) == hashed

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    with st.form("login_form"):
        st.subheader("🔐 ورود به سیستم")
        username = st.text_input("نام کاربری")
        password = st.text_input("رمز عبور", type="password")
        submit = st.form_submit_button("ورود")
        if submit:
            if authenticate(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("❌ اطلاعات ورود نادرست است.")
    st.stop()


st.sidebar.title("🌐 Language / زبان")
lang = st.sidebar.radio("Select language / انتخاب زبان", ["فارسی", "English"])


texts = {
    "فارسی": {
        "title": "📊 داشبورد تحلیل ریسک‌های فناوری اطلاعات",
        "upload": "⬆️ فایل اکسل را بارگذاری کنید",
        "filters": "🎛 فیلترها",
        "risk_level": "سطح ریسک",
        "risk_type": "نوع ریسک",
        "summary": "📌 خلاصه آماری",
        "total": "تعداد کل ریسک‌ها",
        "high": "ریسک‌های زیاد",
        "percent_high": "درصد ریسک زیاد",
        "table_tab": "📋 جدول داده‌ها",
        "charts_tab": "📊 نمودارها",
        "export_tab": "📤 خروجی",
        "pie_chart": "نمودار دایره‌ای سطح ریسک",
        "bar_chart": "نمودار ستونی نوع ریسک",
        "download_excel": "📥 دریافت فایل Excel",
        "download_pdf": "📄 دریافت فایل PDF",
        "no_file": "👆 لطفاً یک فایل اکسل بارگذاری کنید.",
        "report_title": "گزارش تحلیل ریسک",
        "report_date": "تاریخ گزارش",
        "saved_to_db": "✅ داده‌ها ذخیره شدند.",
        "search": "🔎 جستجو در جدول",
        "admin_dashboard": "📂 داشبورد مدیریتی",
        "select_table": "انتخاب جدول از پایگاه داده",
    },
    "English": {
        "title": "📊 IT Risk Analysis Dashboard",
        "upload": "⬆️ Upload Excel file",
        "filters": "🎛 Filters",
        "risk_level": "Risk Level",
        "risk_type": "Risk Type",
        "summary": "📌 Summary",
        "total": "Total Risks",
        "high": "High Risk",
        "percent_high": "High Risk %",
        "table_tab": "📋 Data Table",
        "charts_tab": "📊 Charts",
        "export_tab": "📤 Export",
        "pie_chart": "Risk Level Pie Chart",
        "bar_chart": "Risk Type Bar Chart",
        "download_excel": "📥 Download Excel",
        "download_pdf": "📄 Download PDF",
        "no_file": "👆 Please upload an Excel file.",
        "report_title": "IT Risk Analysis Report",
        "report_date": "Report Date",
        "saved_to_db": "✅ Data saved.",
        "search": "🔎 Search in table",
        "admin_dashboard": "📂 Admin Dashboard",
        "select_table": "Select table from database",
    }
}
t = texts[lang]

st.title(t["title"])

uploaded_file = st.file_uploader(t["upload"], type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.dropna(how='all', inplace=True)
    df.fillna("-", inplace=True)


    st.sidebar.header(t["filters"])
    if t["risk_level"] in df.columns:
        levels = df[t["risk_level"]].unique()
        selected_levels = st.sidebar.multiselect(t["risk_level"], levels, default=levels)
        df = df[df[t["risk_level"]].isin(selected_levels)]

    if t["risk_type"] in df.columns:
        types = df[t["risk_type"]].unique()
        selected_types = st.sidebar.multiselect(t["risk_type"], types, default=types)
        df = df[df[t["risk_type"]].isin(selected_types)]


    st.subheader(t["summary"])
    col1, col2, col3 = st.columns(3)
    col1.metric(t["total"], len(df))
    high_val = "زیاد" if lang == "فارسی" else "High"
    col2.metric(t["high"], (df[t["risk_level"]] == high_val).sum())
    col3.metric(t["percent_high"], f"{(df[t["risk_level"]] == high_val).mean()*100:.1f}%")


    keyword = st.text_input(t["search"])
    if keyword:
        df = df[df.astype(str).apply(lambda row: keyword.lower() in row.to_string().lower(), axis=1)]


    tabs = st.tabs([t["table_tab"], t["charts_tab"], t["export_tab"]])

    with tabs[0]:
        st.dataframe(df, use_container_width=True)

    with tabs[1]:
        st.subheader(t["pie_chart"])
        pie_data = df[t["risk_level"]].value_counts()
        fig1, ax1 = plt.subplots()
        ax1.pie(pie_data, labels=pie_data.index, autopct="%1.1f%%", startangle=90)
        ax1.axis("equal")
        st.pyplot(fig1)

        if t["risk_type"] in df.columns:
            st.subheader(t["bar_chart"])
            fig2, ax2 = plt.subplots(figsize=(10, 4))
            sns.countplot(data=df, x=t["risk_type"], order=df[t["risk_type"]].value_counts().index, palette="Set2", ax=ax2)
            plt.xticks(rotation=45, ha="right")
            st.pyplot(fig2)

    with tabs[2]:
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)
        st.download_button(label=t["download_excel"], data=excel_buffer, file_name="risk_report.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        def convert_df_to_pdf(dataframe):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt=t["report_title"], ln=True, align='C')
            pdf.set_font("Arial", '', 10)
            pdf.cell(200, 10, txt=f"{t['report_date']}: {datetime.datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", 'B', 9)
            col_width = 190 // len(dataframe.columns)
            for col in dataframe.columns:
                pdf.cell(col_width, 10, str(col), border=1, align='C')
            pdf.ln()
            pdf.set_font("Arial", size=8)
            for _, row in dataframe.iterrows():
                for item in row:
                    pdf.cell(col_width, 10, str(item)[:30], border=1)
                pdf.ln()
            output = io.BytesIO()
            pdf.output(output)
            output.seek(0)
            return output

        if not df.empty:
            pdf_file = convert_df_to_pdf(df)
            st.download_button(label=t["download_pdf"], data=pdf_file, file_name="risk_report.pdf", mime="application/pdf")

        conn = sqlite3.connect("risk_data.db")
        table_name = f"risk_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        df.to_sql(table_name, conn, index=False)
        conn.close()
        st.success(t["saved_to_db"])

else:
    st.info(t["no_file"])
