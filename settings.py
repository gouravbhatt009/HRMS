import streamlit as st
import pandas as pd
from datetime import date, datetime
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.helpers import (load_employees, load_leaves, save_leaves,
                            load_config, get_leave_balance, LEAVE_COLUMNS)

def render():
    config = load_config()
    emp_df = load_employees()
    leaves_df = load_leaves()

    st.markdown("""
    <div class="page-header">
        <h1>🌴 Leave Management</h1>
        <p>Manage PL, CL, SL leaves and track balances for all employees</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "📋 Leave Register",
        "➕ Apply / Approve Leave",
        "📊 Leave Balance Report"
    ])

    # ── TAB 1: LEAVE REGISTER ────────────────────────────────────────────────
    with tab1:
        c1, c2, c3 = st.columns(3)
        
        months = ["All","January","February","March","April","May","June",
                  "July","August","September","October","November","December"]
        lr_month = c1.selectbox("Month", months)
        lr_year = c2.number_input("Year", value=date.today().year, min_value=2020, max_value=2030, key="lr_y")
        lr_type = c3.selectbox("Leave Type", ["All", "PL", "CL", "SL"])
        lr_status = st.selectbox("Status", ["All", "Approved", "Pending", "Rejected"])

        filtered = leaves_df.copy()
        if not filtered.empty:
            filtered["from_date"] = pd.to_datetime(filtered["from_date"], errors="coerce")
            if lr_month != "All":
                month_num = months.index(lr_month)
                filtered = filtered[filtered["from_date"].dt.month == month_num]
            filtered = filtered[filtered["from_date"].dt.year == int(lr_year)]
            if lr_type != "All":
                filtered = filtered[filtered["leave_type"] == lr_type]
            if lr_status != "All":
                filtered = filtered[filtered["status"] == lr_status]

            st.markdown(f"**{len(filtered)} leave records**")
            st.dataframe(filtered, use_container_width=True, hide_index=True)

            if not filtered.empty:
                csv_dl = filtered.to_csv(index=False)
                st.download_button("📥 Download Leave Register", csv_dl, "leave_register.csv", "text/csv")
        else:
            st.info("No leave records found.")

    # ── TAB 2: APPLY/APPROVE ─────────────────────────────────────────────────
    with tab2:
        col_l, col_r = st.columns([1, 1])

        with col_l:
            st.markdown("#### ➕ Apply Leave")
            ecode_opts = emp_df["ecode"].tolist() if not emp_df.empty else []
            
            with st.form("apply_leave"):
                al_ecode = st.selectbox("Employee", ecode_opts) if ecode_opts else st.text_input("E-Code")
                al_type = st.selectbox("Leave Type", ["PL", "CL", "SL"])
                al_from = st.date_input("From Date")
                al_to = st.date_input("To Date")
                al_reason = st.text_area("Reason", height=80)

                if st.form_submit_button("Submit Leave", use_container_width=True):
                    if al_to < al_from:
                        st.error("To date cannot be before From date!")
                    else:
                        days = (al_to - al_from).days + 1
                        emp_name = ""
                        if not emp_df.empty:
                            emp_row = emp_df[emp_df["ecode"] == al_ecode]
                            if not emp_row.empty:
                                emp_name = emp_row.iloc[0].get("name", "")

                        new_leave = {
                            "ecode": al_ecode,
                            "name": emp_name,
                            "leave_type": al_type,
                            "from_date": str(al_from),
                            "to_date": str(al_to),
                            "days": days,
                            "reason": al_reason,
                            "status": "Pending",
                            "applied_on": str(date.today())
                        }
                        leaves_df = load_leaves()
                        leaves_df = pd.concat([leaves_df, pd.DataFrame([new_leave])], ignore_index=True)
                        save_leaves(leaves_df)
                        st.success(f"✅ Leave applied for {days} day(s)!")
                        st.rerun()

        with col_r:
            st.markdown("#### ✅ Pending Approvals")
            leaves_df = load_leaves()
            pending = leaves_df[leaves_df["status"] == "Pending"] if not leaves_df.empty else pd.DataFrame()

            if not pending.empty:
                for idx, row in pending.iterrows():
                    with st.expander(f"🔔 {row.get('name','')} ({row.get('ecode','')}) - {row.get('leave_type','')} | {row.get('from_date','')} to {row.get('to_date','')}"):
                        st.write(f"**Days:** {row.get('days', '')}")
                        st.write(f"**Reason:** {row.get('reason', '')}")
                        st.write(f"**Applied on:** {row.get('applied_on', '')}")

                        c1, c2 = st.columns(2)
                        if c1.button("✅ Approve", key=f"app_{idx}", use_container_width=True):
                            leaves_df.loc[idx, "status"] = "Approved"
                            save_leaves(leaves_df)
                            st.success("Approved!")
                            st.rerun()
                        if c2.button("❌ Reject", key=f"rej_{idx}", use_container_width=True):
                            leaves_df.loc[idx, "status"] = "Rejected"
                            save_leaves(leaves_df)
                            st.warning("Rejected!")
                            st.rerun()
            else:
                st.success("✅ No pending leaves!")

    # ── TAB 3: LEAVE BALANCE ─────────────────────────────────────────────────
    with tab3:
        st.markdown("#### 📊 Leave Balance Report")

        bal_year = st.number_input("Year", value=date.today().year, min_value=2020, max_value=2030, key="bal_y")

        if not emp_df.empty:
            balances = []
            active_emp = emp_df[emp_df["status"] == "Active"] if "status" in emp_df.columns else emp_df
            
            for _, emp in active_emp.iterrows():
                bal = get_leave_balance(emp["ecode"], int(bal_year), config)
                balances.append({
                    "E-Code": emp["ecode"],
                    "Name": emp.get("name", ""),
                    "Department": emp.get("department", ""),
                    "PL Entitled": bal["pl_entitled"],
                    "PL Taken": bal["pl_taken"],
                    "PL Balance": bal["pl_balance"],
                    "CL Entitled": bal["cl_entitled"],
                    "CL Taken": bal["cl_taken"],
                    "CL Balance": bal["cl_balance"],
                    "SL Entitled": bal["sl_entitled"],
                    "SL Taken": bal["sl_taken"],
                    "SL Balance": bal["sl_balance"],
                })

            bal_df = pd.DataFrame(balances)
            st.dataframe(bal_df, use_container_width=True, hide_index=True)

            csv_dl = bal_df.to_csv(index=False)
            st.download_button("📥 Download Leave Balances", csv_dl, f"leave_balance_{bal_year}.csv", "text/csv")
        else:
            st.info("No employee data found.")
