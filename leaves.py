import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.helpers import load_employees, load_attendance, load_config

def render():
    config = load_config()
    emp_df = load_employees()
    att_df = load_attendance()

    st.markdown("""
    <div class="page-header">
        <h1>🏠 Dashboard</h1>
        <p>Welcome to the HR & Payroll Management System</p>
    </div>
    """, unsafe_allow_html=True)

    today = date.today()
    today_str = str(today)

    # ── Top KPIs ────────────────────────────────────────────────────────────
    total_emp = len(emp_df[emp_df["status"] == "Active"]) if "status" in emp_df.columns else len(emp_df)
    
    today_att = att_df[att_df["date"] == today_str] if not att_df.empty else pd.DataFrame()
    present_today = len(today_att[today_att["status"] == "Present"]) if not today_att.empty else 0
    absent_today = total_emp - present_today
    missing_punch = len(today_att[today_att["status"].str.contains("Missing", na=False)]) if not today_att.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card">
            <h3>👥 Total Employees</h3><h1>{total_emp}</h1></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card" style="border-left-color:#2e7d32">
            <h3>✅ Present Today</h3><h1>{present_today}</h1></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card" style="border-left-color:#c62828">
            <h3>❌ Absent Today</h3><h1>{absent_today}</h1></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="metric-card" style="border-left-color:#f57c00">
            <h3>⚠️ Missing Punch</h3><h1>{missing_punch}</h1></div>""", unsafe_allow_html=True)

    st.markdown("---")

    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.markdown("### 📅 Monthly Attendance Overview")
        if not att_df.empty:
            att_df["date"] = pd.to_datetime(att_df["date"], errors="coerce")
            month_att = att_df[att_df["date"].dt.month == today.month]
            if not month_att.empty:
                daily = month_att.groupby("date")["status"].apply(
                    lambda x: (x == "Present").sum()
                ).reset_index()
                daily.columns = ["Date", "Present Count"]
                fig = px.bar(daily, x="Date", y="Present Count",
                             color_discrete_sequence=["#3949ab"],
                             title="Daily Present Count This Month")
                fig.update_layout(showlegend=False, height=300,
                                  plot_bgcolor="white", paper_bgcolor="white")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No attendance data for this month yet.")
        else:
            st.info("No attendance data yet. Start by uploading attendance in the Attendance module.")

    with col_r:
        st.markdown("### 🏢 Department Wise Employees")
        if not emp_df.empty and "department" in emp_df.columns:
            dept = emp_df[emp_df["status"] == "Active"]["department"].value_counts().reset_index()
            dept.columns = ["Department", "Count"]
            fig2 = px.pie(dept, values="Count", names="Department",
                          color_discrete_sequence=px.colors.sequential.Blues_r)
            fig2.update_layout(height=300, paper_bgcolor="white")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Add employees to see department breakdown.")

    # ── Quick Actions ─────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    qc1, qc2, qc3, qc4 = st.columns(4)
    with qc1:
        if st.button("➕ Add New Employee", use_container_width=True):
            st.session_state.current_page = "employees"
            st.rerun()
    with qc2:
        if st.button("📤 Upload Attendance", use_container_width=True):
            st.session_state.current_page = "attendance"
            st.rerun()
    with qc3:
        if st.button("💰 Run Payroll", use_container_width=True):
            st.session_state.current_page = "payroll"
            st.rerun()
    with qc4:
        if st.button("⚙️ Configure Rules", use_container_width=True):
            st.session_state.current_page = "settings"
            st.rerun()

    # ── Recent Attendance Issues ──────────────────────────────────────────
    if not att_df.empty:
        st.markdown("---")
        st.markdown("### ⚠️ Missing Punch Alerts (Last 7 Days)")
        att_df["date"] = pd.to_datetime(att_df["date"], errors="coerce")
        recent = att_df[att_df["date"] >= pd.Timestamp(today) - pd.Timedelta(days=7)]
        missing = recent[recent["status"].str.contains("Missing", na=False)]
        if not missing.empty:
            st.dataframe(
                missing[["ecode", "name", "date", "in_time", "out_time", "status"]].sort_values("date", ascending=False),
                use_container_width=True, hide_index=True
            )
        else:
            st.success("✅ No missing punch issues in the last 7 days!")
