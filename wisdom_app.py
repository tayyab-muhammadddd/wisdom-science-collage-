import streamlit as st
import sqlite3
import pandas as pd

# Page Configuration
st.set_page_config(page_title="School Management System", page_icon="🏫", layout="wide")

# Database Setup
def init_db():
    conn = sqlite3.connect("school_database.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            parent_name TEXT,
            class_name TEXT,
            section TEXT,
            total_fee REAL,
            paid_fee REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_connection():
    return sqlite3.connect("school_database.db")

# Header Section
st.markdown("<h1 style='text-align: center; color: #1E88E5;'>🏫 Advanced School & Fee Management System</h1>", unsafe_allow_html=True)
st.markdown("---")

# Navigation Sidebar
menu = ["📊 Dashboard & Summary", "➕ Add New Student", "📋 View All Students Sheet", "🔍 Search & Fee Update"]
choice = st.sidebar.selectbox("Navigation Menu", menu)

# 1. DASHBOARD & SUMMARY
if choice == "📊 Dashboard & Summary":
    st.subheader("📌 School Financial & Enrolment Dashboard")
    
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM students", conn)
    conn.close()

    if df.empty:
        st.info("Abhi tak koi student record database me shamil nahi hai.")
    else:
        df['Pending_Fee'] = df['total_fee'] - df['paid_fee']
        
        total_students = len(df)
        total_expected = df['total_fee'].sum()
        total_collected = df['paid_fee'].sum()
        total_pending = df['Pending_Fee'].sum()

        # Metric Cards
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Students", f"{total_students}")
        col2.metric("Total Expected Dues", f"PKR {total_expected:,.0f}")
        col3.metric("Total Collected Fee", f"PKR {total_collected:,.0f}")
        col4.metric("Total Pending Dues", f"PKR {total_pending:,.0f}")

        st.markdown("---")
        st.subheader("📚 Class-wise Summary Report")
        
        class_summary = df.groupby('class_name').agg(
            Total_Students=('id', 'count'),
            Collected_Fee=('paid_fee', 'sum'),
            Pending_Fee=('Pending_Fee', 'sum')
        ).reset_index()

        st.dataframe(class_summary, use_container_width=True)

# 2. ADD NEW STUDENT
elif choice == "➕ Add New Student":
    st.subheader("📝 Enter New Student Details")
    
    with st.form("add_student_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Student Name")
            class_name = st.text_input("Class (e.g. Grade 5)")
            total_fee = st.number_input("Total Fee Amount (PKR)", min_value=0.0, step=500.0)
        with col2:
            parent_name = st.text_input("Father / Parent Name")
            section = st.text_input("Section (e.g. A, B)")
            paid_fee = st.number_input("Paid Fee Amount (PKR)", min_value=0.0, step=500.0)

        submit = st.form_submit_button("Save Student Record")

        if submit:
            if name and class_name:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO students (name, parent_name, class_name, section, total_fee, paid_fee)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, parent_name, class_name, section, total_fee, paid_fee))
                conn.commit()
                conn.close()
                st.success(f"✅ Student '{name}' successfully database me save ho gaya!")
            else:
                st.error("⚠️ Kripya Student Name aur Class zaroor fill karein.")

# 3. VIEW ALL STUDENTS SHEET
elif choice == "📋 View All Students Sheet":
    st.subheader("📄 All Registered Student Records")
    
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM students", conn)
    conn.close()

    if df.empty:
        st.info("Koi student records nahi miley.")
    else:
        df['Pending_Fee'] = df['total_fee'] - df['paid_fee']
        
        def get_status(row):
            if row['Pending_Fee'] <= 0:
                return '✅ PAID'
            elif row['paid_fee'] > 0:
                return '⚠️ PARTIAL'
            else:
                return '❌ UNPAID'

        df['Status'] = df.apply(get_status, axis=1)

        # Class Filter
        classes = ["All"] + list(df['class_name'].unique())
        selected_class = st.selectbox("Filter by Class", classes)

        if selected_class != "All":
            df = df[df['class_name'] == selected_class]

        st.dataframe(df[['id', 'name', 'parent_name', 'class_name', 'section', 'total_fee', 'paid_fee', 'Pending_Fee', 'Status']], use_container_width=True)

# 4. SEARCH & FEE UPDATE
elif choice == "🔍 Search & Fee Update":
    st.subheader("💳 Search Student & Update Fee Payment")
    
    search_id = st.number_input("Enter Student ID", min_value=1, step=1)
    
    if st.button("Search Student"):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE id = ?", (search_id,))
        record = cursor.fetchone()
        conn.close()

        if record:
            st.session_state['found_student'] = record
        else:
            st.error("❌ Iss Student ID ka koi record nahi mila.")

    if 'found_student' in st.session_state:
        s = st.session_state['found_student']
        pending = s[5] - s[6]
        
        st.write(f"**Student ID:** {s[0]}")
        st.write(f"**Name:** {s[1]} | **Father Name:** {s[2]}")
        st.write(f"**Class:** {s[3]} ({s[4]})")
        st.write(f"**Total Fee:** PKR {s[5]:,.0f} | **Current Paid:** PKR {s[6]:,.0f}")
        st.write(f"**Remaining Dues:** PKR {pending:,.0f}")

        new_payment = st.number_input("Enter Additional Fee Received (PKR)", min_value=0.0, step=500.0)
        if st.button("Update Payment"):
            updated_paid = s[6] + new_payment
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE students SET paid_fee = ? WHERE id = ?", (updated_paid, s[0]))
            conn.commit()
            conn.close()
            st.success("🎉 Payment updated successfully!")
            del st.session_state['found_student']