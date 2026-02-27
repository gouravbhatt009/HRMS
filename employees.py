import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.helpers import (load_employees, load_attendance, save_attendance,
                            load_config, calculate_working_hours, apply_sandwich_rule,
                            ATTENDANCE_COLUMNS)

def render():
    config = load_config()
    emp_df = load_employees()
    att_df = load_attendance()

    st.markdown("""
    <div class="page-header">
        <h1>🕐 Attendance Management</h1>
        <p>Track daily attendance, punch details, overtime, and apply attendance rules</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📤 Upload / Enter Attendance",
        "📋 View & Edit Attendance",
        "⚠️ Missing Punches",
        "📊 Attendance Analytics"
    ])

    # ── TAB 1: UPLOAD ATTENDANCE ─────────────────────────────────────────────
    with tab1:
        st.markdown("### Upload Punch Data")
        st.info("""
        **Template Columns:** ecode, date (YYYY-MM-DD), in_time (HH:MM), out_time (HH:MM)
        
        The system will auto-calculate: Working Hours, Overtime, Late Entry, Early Going, Status
        """)

        # Template
        template = pd.DataFrame({
            "ecode": ["EMP001", "EMP002"],
            "date": ["2024-01-15", "2024-01-15"],
            "in_time": ["09:05", "09:30"],
            "out_time": ["18:35", "18:00"]
        })
        csv_t = template.to_csv(index=False)
        st.download_button("📥 Download Attendance Template", csv_t, "attendance_template.csv", "text/csv")

        uploaded = st.file_uploader("Upload Attendance File (CSV/Excel)", type=["csv", "xlsx"])

        if uploaded:
            if uploaded.name.endswith(".csv"):
                raw_df = pd.read_csv(uploaded, dtype=str)
            else:
                raw_df = pd.read_excel(uploaded, dtype=str)

            st.markdown(f"**Preview: {len(raw_df)} records**")
            st.dataframe(raw_df.head(10), use_container_width=True)

            if st.button("⚙️ Process & Calculate Attendance", use_container_width=True):
                with st.spinner("Processing attendance data..."):
                    processed = []
                    for _, row in raw_df.iterrows():
                        ecode = str(row.get("ecode", "")).upper().strip()
                        dt = str(row.get("date", "")).strip()
                        in_t = str(row.get("in_time", "")).strip()
                        out_t = str(row.get("out_time", "")).strip()

                        # Get employee info
                        emp_row = emp_df[emp_df["ecode"] == ecode]
                        if emp_row.empty:
                            continue
                        emp = emp_row.iloc[0]
                        emp_name = emp.get("name", "")
                        shift = emp.get("shift", config["shifts"]["fixed"][0]["name"])

                        try:
                            day_name = datetime.strptime(dt, "%Y-%m-%d").strftime("%A")
                        except:
                            day_name = ""

                        # Calculate hours
                        calc = calculate_working_hours(in_t, out_t, shift, config)

                        processed.append({
                            "ecode": ecode,
                            "name": emp_name,
                            "date": dt,
                            "day": day_name,
                            "shift": shift,
                            "in_time": in_t,
                            "out_time": out_t,
                            "working_hours": calc["working_hours"],
                            "overtime_hours": calc["overtime_hours"],
                            "early_going_minutes": calc["early_going_minutes"],
                            "late_entry_minutes": calc["late_entry_minutes"],
                            "status": calc["status"],
                            "remarks": ""
                        })

                    new_att = pd.DataFrame(processed)

                    # Apply sandwich rule per employee
                    if config["attendance"]["sandwich_rule"] and not new_att.empty:
                        results = []
                        for ecode_val, grp in new_att.groupby("ecode"):
                            grp["remarks"] = grp.get("remarks", "")
                            grp_processed = apply_sandwich_rule(grp, config)
                            results.append(grp_processed)
                        if results:
                            new_att = pd.concat(results, ignore_index=True)

                    # Merge with existing (remove duplicates)
                    if not att_df.empty:
                        keys = new_att[["ecode", "date"]].apply(tuple, axis=1)
                        existing_keys = att_df[["ecode", "date"]].apply(tuple, axis=1)
                        att_df = att_df[~existing_keys.isin(keys)]
                        att_df = pd.concat([att_df, new_att], ignore_index=True)
                    else:
                        att_df = new_att

                    save_attendance(att_df)
                    st.success(f"✅ {len(new_att)} attendance records processed and saved!")
                    st.dataframe(new_att, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("### ✏️ Manual Entry")
        with st.form("manual_att"):
            c1, c2, c3 = st.columns(3)
            ecode_opts = emp_df["ecode"].tolist() if not emp_df.empty else []
            m_ecode = c1.selectbox("Employee E-Code", ecode_opts) if ecode_opts else c1.text_input("E-Code")
            m_date = c2.date_input("Date", value=date.today())
            m_status = c3.selectbox("Status", ["Present", "Absent", "Half Day", "Week Off", "Holiday", "On Leave"])

            c1, c2 = st.columns(2)
            m_in = c1.text_input("IN Time (HH:MM)", "09:00")
            m_out = c2.text_input("OUT Time (HH:MM)", "18:00")
            m_remarks = st.text_input("Remarks", "")

            if st.form_submit_button("💾 Save Entry", use_container_width=True):
                emp_row = emp_df[emp_df["ecode"] == m_ecode]
                if not emp_row.empty:
                    emp = emp_row.iloc[0]
                    shift = emp.get("shift", "")
                    calc = calculate_working_hours(m_in, m_out, shift, config)

                    try:
                        day_name = m_date.strftime("%A")
                    except:
                        day_name = ""

                    new_row = {
                        "ecode": m_ecode,
                        "name": emp.get("name", ""),
                        "date": str(m_date),
                        "day": day_name,
                        "shift": shift,
                        "in_time": m_in,
                        "out_time": m_out,
                        "working_hours": calc["working_hours"] if m_status == "Present" else 0,
                        "overtime_hours": calc["overtime_hours"] if m_status == "Present" else 0,
                        "early_going_minutes": calc["early_going_minutes"],
                        "late_entry_minutes": calc["late_entry_minutes"],
                        "status": m_status,
                        "remarks": m_remarks
                    }
                    att_df = load_attendance()
                    att_df = att_df[~((att_df["ecode"] == m_ecode) & (att_df["date"] == str(m_date)))]
                    att_df = pd.concat([att_df, pd.DataFrame([new_row])], ignore_index=True)
                    save_attendance(att_df)
                    st.success("✅ Attendance saved!")

    # ── TAB 2: VIEW & EDIT ───────────────────────────────────────────────────
    with tab2:
        st.markdown("### View Attendance Records")
        c1, c2, c3, c4 = st.columns(4)
        
        months = ["January","February","March","April","May","June",
                  "July","August","September","October","November","December"]
        sel_month = c1.selectbox("Month", months, index=date.today().month - 1)
        sel_year = c2.number_input("Year", value=date.today().year, min_value=2020, max_value=2030)
        
        ecode_list = ["All"] + sorted(emp_df["ecode"].tolist()) if not emp_df.empty else ["All"]
        sel_emp = c3.selectbox("Employee", ecode_list)
        sel_status = c4.selectbox("Status Filter", ["All", "Present", "Absent", "Missing Punch", "Half Day"])

        if not att_df.empty:
            att_df["date"] = pd.to_datetime(att_df["date"], errors="coerce")
            month_num = months.index(sel_month) + 1

            filtered = att_df[
                (att_df["date"].dt.month == month_num) &
                (att_df["date"].dt.year == int(sel_year))
            ]
            if sel_emp != "All":
                filtered = filtered[filtered["ecode"] == sel_emp]
            if sel_status != "All":
                filtered = filtered[filtered["status"].str.contains(sel_status, na=False)]

            filtered = filtered.sort_values(["ecode", "date"])
            filtered["date"] = filtered["date"].dt.strftime("%Y-%m-%d")

            st.markdown(f"**{len(filtered)} records**")
            
            # Summary row
            if not filtered.empty:
                s_col1, s_col2, s_col3, s_col4 = st.columns(4)
                s_col1.metric("Present Days", len(filtered[filtered["status"] == "Present"]))
                s_col2.metric("Absent Days", len(filtered[filtered["status"] == "Absent"]))
                s_col3.metric("Total OT Hours", round(pd.to_numeric(filtered["overtime_hours"], errors="coerce").sum(), 2))
                s_col4.metric("Late Entries", len(filtered[pd.to_numeric(filtered["late_entry_minutes"], errors="coerce") > 0]))

            st.dataframe(
                filtered[["ecode","name","date","day","shift","in_time","out_time",
                           "working_hours","overtime_hours","late_entry_minutes",
                           "early_going_minutes","status","remarks"]],
                use_container_width=True, hide_index=True
            )

            # Download
            csv_dl = filtered.to_csv(index=False)
            st.download_button("📥 Download Report", csv_dl,
                               f"attendance_{sel_month}_{sel_year}.csv", "text/csv")
        else:
            st.info("No attendance records yet. Upload data in the first tab.")

    # ── TAB 3: MISSING PUNCHES ───────────────────────────────────────────────
    with tab3:
        st.markdown("### ⚠️ Missing Punch Details")
        st.info("Filter and fix employees who have missing IN or OUT punch")

        c1, c2 = st.columns(2)
        filter_date = c1.date_input("Filter by Date", value=date.today())
        miss_type = c2.selectbox("Missing Type", ["All Missing", "Missing IN Punch", "Missing OUT Punch", "Missing Both"])

        if not att_df.empty:
            att_df["date"] = pd.to_datetime(att_df["date"], errors="coerce")
            missing_df = att_df[att_df["status"].str.contains("Missing", na=False)]

            if miss_type == "Missing IN Punch":
                missing_df = att_df[(att_df["in_time"].isna() | (att_df["in_time"] == ""))]
            elif miss_type == "Missing OUT Punch":
                missing_df = att_df[(att_df["out_time"].isna() | (att_df["out_time"] == ""))]

            missing_df = missing_df[missing_df["date"].dt.date == filter_date]

            st.markdown(f"**{len(missing_df)} missing punch records on {filter_date}**")
            
            if not missing_df.empty:
                st.dataframe(
                    missing_df[["ecode","name","date","shift","in_time","out_time","status"]],
                    use_container_width=True, hide_index=True
                )

                st.markdown("#### ✏️ Fix a Missing Punch")
                with st.form("fix_punch"):
                    fx_ecode = st.selectbox("Select Employee", missing_df["ecode"].tolist())
                    fc1, fc2 = st.columns(2)
                    fx_in = fc1.text_input("IN Time (HH:MM)", "09:00")
                    fx_out = fc2.text_input("OUT Time (HH:MM)", "18:00")
                    fx_remark = st.text_input("Remarks", "Manual entry by HR")
                    
                    if st.form_submit_button("✅ Update Punch", use_container_width=True):
                        att_df = load_attendance()
                        att_df["date"] = pd.to_datetime(att_df["date"], errors="coerce")
                        mask = ((att_df["ecode"] == fx_ecode) &
                                (att_df["date"].dt.date == filter_date))
                        
                        emp_row = emp_df[emp_df["ecode"] == fx_ecode]
                        if not emp_row.empty:
                            shift = emp_row.iloc[0].get("shift", "")
                            calc = calculate_working_hours(fx_in, fx_out, shift, config)
                            att_df.loc[mask, "in_time"] = fx_in
                            att_df.loc[mask, "out_time"] = fx_out
                            att_df.loc[mask, "working_hours"] = calc["working_hours"]
                            att_df.loc[mask, "overtime_hours"] = calc["overtime_hours"]
                            att_df.loc[mask, "late_entry_minutes"] = calc["late_entry_minutes"]
                            att_df.loc[mask, "early_going_minutes"] = calc["early_going_minutes"]
                            att_df.loc[mask, "status"] = "Present"
                            att_df.loc[mask, "remarks"] = fx_remark
                            att_df["date"] = att_df["date"].dt.strftime("%Y-%m-%d")
                            save_attendance(att_df)
                            st.success("✅ Punch updated successfully!")
                            st.rerun()
            else:
                st.success("✅ No missing punches on this date!")
        else:
            st.info("No attendance data available.")

    # ── TAB 4: ANALYTICS ─────────────────────────────────────────────────────
    with tab4:
        st.markdown("### 📊 Attendance Analytics")

        if att_df.empty:
            st.info("No attendance data to analyze.")
            return

        import plotly.express as px
        import plotly.graph_objects as go

        att_df["date"] = pd.to_datetime(att_df["date"], errors="coerce")
        att_df["late_entry_minutes"] = pd.to_numeric(att_df["late_entry_minutes"], errors="coerce").fillna(0)
        att_df["early_going_minutes"] = pd.to_numeric(att_df["early_going_minutes"], errors="coerce").fillna(0)
        att_df["overtime_hours"] = pd.to_numeric(att_df["overtime_hours"], errors="coerce").fillna(0)
        att_df["working_hours"] = pd.to_numeric(att_df["working_hours"], errors="coerce").fillna(0)

        months = ["January","February","March","April","May","June",
                  "July","August","September","October","November","December"]
        c1, c2 = st.columns(2)
        an_month = c1.selectbox("Month", months, index=date.today().month - 1, key="an_month")
        an_year = c2.number_input("Year", value=date.today().year, min_value=2020, max_value=2030, key="an_year")
        month_num = months.index(an_month) + 1

        month_data = att_df[
            (att_df["date"].dt.month == month_num) &
            (att_df["date"].dt.year == int(an_year))
        ]

        if month_data.empty:
            st.warning("No data for selected period.")
            return

        col1, col2 = st.columns(2)

        with col1:
            # Top late entries
            late_df = month_data[month_data["late_entry_minutes"] > 0].groupby("name")["late_entry_minutes"].sum().reset_index().sort_values("late_entry_minutes", ascending=False).head(10)
            if not late_df.empty:
                fig = px.bar(late_df, x="name", y="late_entry_minutes",
                             title="🕐 Top 10 Late Entries (Minutes)",
                             color_discrete_sequence=["#e53935"])
                fig.update_layout(height=300, paper_bgcolor="white", plot_bgcolor="white")
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Top OT
            ot_df = month_data[month_data["overtime_hours"] > 0].groupby("name")["overtime_hours"].sum().reset_index().sort_values("overtime_hours", ascending=False).head(10)
            if not ot_df.empty:
                fig2 = px.bar(ot_df, x="name", y="overtime_hours",
                              title="⏰ Top 10 Overtime Hours",
                              color_discrete_sequence=["#2e7d32"])
                fig2.update_layout(height=300, paper_bgcolor="white", plot_bgcolor="white")
                st.plotly_chart(fig2, use_container_width=True)

        # Early going
        early_df = month_data[month_data["early_going_minutes"] > 0].groupby("name")["early_going_minutes"].sum().reset_index().sort_values("early_going_minutes", ascending=False).head(10)
        if not early_df.empty:
            fig3 = px.bar(early_df, x="name", y="early_going_minutes",
                          title="🏃 Early Going Employees (Minutes)",
                          color_discrete_sequence=["#f57c00"])
            fig3.update_layout(height=300, paper_bgcolor="white", plot_bgcolor="white")
            st.plotly_chart(fig3, use_container_width=True)

        # Employee wise summary table
        summary = month_data.groupby(["ecode", "name"]).agg(
            present_days=("status", lambda x: (x == "Present").sum()),
            absent_days=("status", lambda x: (x == "Absent").sum()),
            total_hours=("working_hours", "sum"),
            total_ot=("overtime_hours", "sum"),
            total_late=("late_entry_minutes", "sum"),
            total_early=("early_going_minutes", "sum")
        ).reset_index()

        st.markdown("#### 📋 Employee Attendance Summary")
        st.dataframe(summary, use_container_width=True, hide_index=True)
        csv_dl = summary.to_csv(index=False)
        st.download_button("📥 Download Summary", csv_dl, f"att_summary_{an_month}_{an_year}.csv", "text/csv")
