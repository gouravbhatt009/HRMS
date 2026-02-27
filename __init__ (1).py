import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.helpers import (load_employees, load_attendance, load_config,
                            calculate_payroll, get_leave_balance)

def render():
    config = load_config()
    emp_df = load_employees()
    att_df = load_attendance()

    st.markdown("""
    <div class="page-header">
        <h1>💰 Payroll Management</h1>
        <p>Calculate monthly salary, PF, ESIC, overtime, and generate payslips</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "🧮 Run Payroll",
        "📄 Payslip Generator",
        "📊 Payroll Reports"
    ])

    months = ["January","February","March","April","May","June",
              "July","August","September","October","November","December"]

    # ── TAB 1: RUN PAYROLL ───────────────────────────────────────────────────
    with tab1:
        st.markdown("### Run Monthly Payroll")

        c1, c2 = st.columns(2)
        sel_month = c1.selectbox("Month", months, index=date.today().month - 2 if date.today().month > 1 else 0)
        sel_year = c2.number_input("Year", value=date.today().year, min_value=2020, max_value=2030)
        month_num = months.index(sel_month) + 1

        # Working days in month
        import calendar
        _, total_days_in_month = calendar.monthrange(int(sel_year), month_num)
        week_off = config["attendance"]["week_off"]
        
        # Count actual working days (exclude Sundays)
        working_days = sum(
            1 for d in range(1, total_days_in_month + 1)
            if date(int(sel_year), month_num, d).strftime("%A") != week_off
        )

        st.info(f"📅 **{sel_month} {sel_year}** | Total Days: {total_days_in_month} | Working Days: {working_days} (excl. {week_off}s)")

        if st.button("⚙️ Calculate Payroll for All Employees", use_container_width=True):
            if emp_df.empty:
                st.error("No employees found!")
            elif att_df.empty:
                st.error("No attendance data found for this month!")
            else:
                with st.spinner("Calculating payroll..."):
                    att_df_copy = att_df.copy()
                    att_df_copy["date"] = pd.to_datetime(att_df_copy["date"], errors="coerce")
                    
                    month_att = att_df_copy[
                        (att_df_copy["date"].dt.month == month_num) &
                        (att_df_copy["date"].dt.year == int(sel_year))
                    ]

                    payroll_results = []
                    active_emp = emp_df[emp_df["status"] == "Active"] if "status" in emp_df.columns else emp_df

                    for _, emp in active_emp.iterrows():
                        ecode = emp["ecode"]
                        emp_att = month_att[month_att["ecode"] == ecode]

                        present_days = len(emp_att[emp_att["status"] == "Present"])
                        overtime_hours = pd.to_numeric(emp_att["overtime_hours"], errors="coerce").sum()

                        result = calculate_payroll(emp, present_days, working_days, overtime_hours, config)
                        payroll_results.append(result)

                    payroll_df = pd.DataFrame(payroll_results)
                    st.session_state[f"payroll_{sel_month}_{sel_year}"] = payroll_df
                    st.success(f"✅ Payroll calculated for {len(payroll_df)} employees!")

                    st.markdown("### 💰 Payroll Summary")

                    # Summary metrics
                    s1, s2, s3, s4 = st.columns(4)
                    s1.metric("Total Gross", f"₹{payroll_df['earned_gross'].sum():,.0f}")
                    s2.metric("Total PF (Employer)", f"₹{payroll_df['pf_employer'].sum():,.0f}")
                    s3.metric("Total OT Pay", f"₹{payroll_df['overtime_pay'].sum():,.0f}")
                    s4.metric("Total Net Pay", f"₹{payroll_df['net_pay'].sum():,.0f}")

                    st.dataframe(payroll_df, use_container_width=True, hide_index=True)

                    # Download
                    csv_dl = payroll_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Payroll Sheet",
                        csv_dl,
                        f"payroll_{sel_month}_{sel_year}.csv",
                        "text/csv"
                    )

                    # Save payroll
                    payroll_path = os.path.join(
                        os.path.dirname(os.path.dirname(__file__)),
                        "data", f"payroll_{sel_month}_{sel_year}.csv"
                    )
                    payroll_df.to_csv(payroll_path, index=False)

        # Load previous if exists
        elif f"payroll_{sel_month}_{sel_year}" in st.session_state:
            payroll_df = st.session_state[f"payroll_{sel_month}_{sel_year}"]
            st.dataframe(payroll_df, use_container_width=True, hide_index=True)

    # ── TAB 2: PAYSLIP ───────────────────────────────────────────────────────
    with tab2:
        st.markdown("### 📄 Generate Payslip")

        c1, c2, c3 = st.columns(3)
        ps_month = c1.selectbox("Month", months, index=date.today().month - 2 if date.today().month > 1 else 0, key="ps_m")
        ps_year = c2.number_input("Year", value=date.today().year, key="ps_y", min_value=2020, max_value=2030)
        
        ecode_opts = emp_df["ecode"].tolist() if not emp_df.empty else []
        ps_ecode = c3.selectbox("Employee E-Code", ecode_opts) if ecode_opts else c3.text_input("E-Code")

        if st.button("🖨️ Generate Payslip", use_container_width=True):
            payroll_key = f"payroll_{ps_month}_{ps_year}"
            
            # Try to load from session or file
            payroll_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "data", f"payroll_{ps_month}_{ps_year}.csv"
            )
            
            payroll_df_ps = None
            if payroll_key in st.session_state:
                payroll_df_ps = st.session_state[payroll_key]
            elif os.path.exists(payroll_path):
                payroll_df_ps = pd.read_csv(payroll_path)
            
            if payroll_df_ps is None:
                st.error("Please run payroll first for this month!")
            else:
                emp_data = payroll_df_ps[payroll_df_ps["ecode"] == ps_ecode]
                if emp_data.empty:
                    st.error("No payroll data for this employee in selected month!")
                else:
                    p = emp_data.iloc[0]
                    emp_info = emp_df[emp_df["ecode"] == ps_ecode]
                    e = emp_info.iloc[0] if not emp_info.empty else {}

                    # Beautiful HTML Payslip
                    payslip_html = f"""
                    <div style="max-width:700px; margin:0 auto; font-family:'Segoe UI',sans-serif; border:1px solid #ddd; border-radius:12px; overflow:hidden;">
                        <div style="background:linear-gradient(135deg,#1a237e,#3949ab); color:white; padding:24px;">
                            <h2 style="margin:0; font-size:22px;">{config['company']['name']}</h2>
                            <p style="margin:4px 0; opacity:0.8;">SALARY SLIP - {ps_month.upper()} {ps_year}</p>
                        </div>
                        <div style="padding:20px; background:#f8f9fa;">
                            <table style="width:100%; font-size:14px;">
                                <tr>
                                    <td><b>Employee Name:</b> {p.get('name','')}</td>
                                    <td><b>E-Code:</b> {p.get('ecode','')}</td>
                                </tr>
                                <tr>
                                    <td><b>Department:</b> {e.get('department','') if hasattr(e,'get') else ''}</td>
                                    <td><b>Designation:</b> {e.get('designation','') if hasattr(e,'get') else ''}</td>
                                </tr>
                                <tr>
                                    <td><b>Bank:</b> {e.get('bank_name','') if hasattr(e,'get') else ''}</td>
                                    <td><b>Account No:</b> {e.get('account_no','') if hasattr(e,'get') else ''}</td>
                                </tr>
                                <tr>
                                    <td><b>UAN:</b> {e.get('uan','') if hasattr(e,'get') else ''}</td>
                                    <td><b>Days Worked:</b> {p.get('present_days',0)}</td>
                                </tr>
                            </table>
                        </div>
                        <div style="display:flex; padding:0 20px 20px;">
                            <div style="flex:1; margin-right:12px;">
                                <h4 style="color:#1a237e; border-bottom:2px solid #3949ab; padding-bottom:6px;">💚 EARNINGS</h4>
                                <table style="width:100%; font-size:13px;">
                                    <tr><td>Basic Salary</td><td align="right">₹{p.get('earned_basic',0):,.2f}</td></tr>
                                    <tr><td>HRA</td><td align="right">₹{p.get('earned_hra',0):,.2f}</td></tr>
                                    <tr><td>Conveyance</td><td align="right">₹{p.get('earned_conveyance',0):,.2f}</td></tr>
                                    <tr><td>Special Allowance</td><td align="right">₹{p.get('earned_special',0):,.2f}</td></tr>
                                    <tr><td>Medical Allowance</td><td align="right">₹{p.get('earned_medical',0):,.2f}</td></tr>
                                    <tr><td>Food Allowance</td><td align="right">₹{p.get('earned_food',0):,.2f}</td></tr>
                                    <tr><td>Overtime Pay</td><td align="right">₹{p.get('overtime_pay',0):,.2f}</td></tr>
                                    <tr style="font-weight:bold; border-top:1px solid #ddd;">
                                        <td>Gross Earned</td><td align="right">₹{p.get('earned_gross',0):,.2f}</td>
                                    </tr>
                                </table>
                            </div>
                            <div style="flex:1; margin-left:12px;">
                                <h4 style="color:#c62828; border-bottom:2px solid #e53935; padding-bottom:6px;">❤️ DEDUCTIONS</h4>
                                <table style="width:100%; font-size:13px;">
                                    <tr><td>PF Employee (12%)</td><td align="right">₹{p.get('pf_employee',0):,.2f}</td></tr>
                                    <tr><td>ESIC Employee (0.75%)</td><td align="right">₹{p.get('esic_employee',0):,.2f}</td></tr>
                                    <tr style="font-weight:bold; border-top:1px solid #ddd;">
                                        <td>Total Deductions</td><td align="right">₹{p.get('total_deductions',0):,.2f}</td>
                                    </tr>
                                </table>
                                <br/>
                                <h4 style="color:#1a237e; border-bottom:2px solid #3949ab; padding-bottom:6px;">🏢 EMPLOYER CONTRIBUTION</h4>
                                <table style="width:100%; font-size:13px;">
                                    <tr><td>PF Employer (12%)</td><td align="right">₹{p.get('pf_employer',0):,.2f}</td></tr>
                                    <tr><td>EPS (8.33%)</td><td align="right">₹{p.get('eps',0):,.2f}</td></tr>
                                    <tr><td>ESIC Employer (3.25%)</td><td align="right">₹{p.get('esic_employer',0):,.2f}</td></tr>
                                </table>
                            </div>
                        </div>
                        <div style="background:linear-gradient(135deg,#1a237e,#3949ab); color:white; padding:16px 20px; text-align:center;">
                            <h3 style="margin:0; font-size:20px;">💵 NET PAY: ₹{p.get('net_pay',0):,.2f}</h3>
                        </div>
                        <div style="padding:12px 20px; background:#f8f9fa; font-size:11px; color:#777; text-align:center;">
                            This is a computer generated payslip. | Generated on {date.today()}
                        </div>
                    </div>
                    """
                    st.markdown(payslip_html, unsafe_allow_html=True)

    # ── TAB 3: REPORTS ───────────────────────────────────────────────────────
    with tab3:
        st.markdown("### 📊 Payroll Reports")

        import plotly.express as px

        # List available payroll files
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        payroll_files = [f for f in os.listdir(data_dir) if f.startswith("payroll_") and f.endswith(".csv")]

        if not payroll_files:
            st.info("No payroll data found. Run payroll first.")
            return

        sel_file = st.selectbox("Select Payroll Period", payroll_files)
        if sel_file:
            rpt_df = pd.read_csv(os.path.join(data_dir, sel_file))

            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Employees", len(rpt_df))
            r2.metric("Total Gross", f"₹{pd.to_numeric(rpt_df['earned_gross'], errors='coerce').sum():,.0f}")
            r3.metric("Total PF (Both)", f"₹{(pd.to_numeric(rpt_df['pf_employee'], errors='coerce') + pd.to_numeric(rpt_df['pf_employer'], errors='coerce')).sum():,.0f}")
            r4.metric("Total Net Pay", f"₹{pd.to_numeric(rpt_df['net_pay'], errors='coerce').sum():,.0f}")

            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(rpt_df.sort_values("net_pay", ascending=False).head(15),
                             x="name", y="net_pay", title="Top 15 Earners (Net Pay)",
                             color_discrete_sequence=["#1a237e"])
                fig.update_layout(height=350, paper_bgcolor="white", plot_bgcolor="white")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig2 = px.scatter(rpt_df, x="present_days", y="net_pay",
                                  hover_data=["name", "ecode"],
                                  title="Days Worked vs Net Pay",
                                  color_discrete_sequence=["#3949ab"])
                fig2.update_layout(height=350, paper_bgcolor="white", plot_bgcolor="white")
                st.plotly_chart(fig2, use_container_width=True)

            st.dataframe(rpt_df, use_container_width=True, hide_index=True)
            csv_dl = rpt_df.to_csv(index=False)
            st.download_button("📥 Download Report", csv_dl, sel_file, "text/csv")
