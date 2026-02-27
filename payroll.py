import streamlit as st
import pandas as pd
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.helpers import load_employees, save_employees, load_config

def render():
    config = load_config()
    st.markdown("""
    <div class="page-header">
        <h1>👤 Employee Master</h1>
        <p>Manage all employee records, personal details, and salary structure</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 Employee List", "➕ Add / Edit Employee", "📤 Bulk Import"])

    emp_df = load_employees()

    # ── TAB 1: EMPLOYEE LIST ─────────────────────────────────────────────────
    with tab1:
        col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
        with col_f1:
            search = st.text_input("🔍 Search by Name or E-Code", "")
        with col_f2:
            dept_filter = st.selectbox("Filter by Department", ["All"] + sorted(emp_df["department"].dropna().unique().tolist()) if not emp_df.empty else ["All"])
        with col_f3:
            status_filter = st.selectbox("Status", ["All", "Active", "Inactive"])

        display_df = emp_df.copy()
        if search:
            display_df = display_df[
                display_df["name"].str.contains(search, case=False, na=False) |
                display_df["ecode"].str.contains(search, case=False, na=False)
            ]
        if dept_filter != "All":
            display_df = display_df[display_df["department"] == dept_filter]
        if status_filter != "All":
            display_df = display_df[display_df["status"] == status_filter]

        st.markdown(f"**{len(display_df)} employees found**")

        show_cols = ["ecode", "name", "department", "designation", "shift", "gross_salary", "status", "doj"]
        show_cols = [c for c in show_cols if c in display_df.columns]

        st.dataframe(display_df[show_cols], use_container_width=True, hide_index=True)

        # Download
        if not display_df.empty:
            csv = display_df.to_csv(index=False)
            st.download_button("📥 Download Employee List", csv, "employees.csv", "text/csv")

    # ── TAB 2: ADD/EDIT ──────────────────────────────────────────────────────
    with tab2:
        mode = st.radio("Mode", ["Add New Employee", "Edit Existing Employee"], horizontal=True)

        if mode == "Edit Existing Employee" and not emp_df.empty:
            ecode_list = emp_df["ecode"].tolist()
            selected_ecode = st.selectbox("Select Employee E-Code", ecode_list)
            existing = emp_df[emp_df["ecode"] == selected_ecode].iloc[0].to_dict()
        else:
            existing = {}

        def val(key, default=""):
            return existing.get(key, default) or default

        shifts = [s["name"] for s in config["shifts"]["fixed"]] + ["Open Shift"]

        with st.form("employee_form"):
            st.markdown("#### 🆔 Basic Information")
            c1, c2, c3 = st.columns(3)
            ecode = c1.text_input("E-Code *", val("ecode"))
            name = c2.text_input("Full Name *", val("name"))
            doj = c3.date_input("Date of Joining", value=pd.to_datetime(val("doj")) if val("doj") else None)
            
            c1, c2, c3 = st.columns(3)
            dept = c1.text_input("Department", val("department"))
            desig = c2.text_input("Designation", val("designation"))
            gender = c3.selectbox("Gender", ["Male", "Female", "Other"],
                                   index=["Male", "Female", "Other"].index(val("gender", "Male")) if val("gender") in ["Male", "Female", "Other"] else 0)
            
            c1, c2, c3 = st.columns(3)
            mobile = c1.text_input("Mobile", val("mobile"))
            email = c2.text_input("Email", val("email"))
            dob = c3.date_input("Date of Birth", value=pd.to_datetime(val("dob")) if val("dob") else None)

            address = st.text_area("Address", val("address"), height=60)

            st.markdown("#### 👨‍👩‍👧 Family Details")
            c1, c2, c3 = st.columns(3)
            father = c1.text_input("Father's Name", val("father_name"))
            mother = c2.text_input("Mother's Name", val("mother_name"))
            spouse = c3.text_input("Spouse Name", val("spouse_name"))

            st.markdown("#### 📋 Nominee Details")
            c1, c2, c3 = st.columns(3)
            nominee_name = c1.text_input("Nominee Name", val("nominee_name"))
            nominee_rel = c2.text_input("Nominee Relation", val("nominee_relation"))
            nominee_dob_val = c3.date_input("Nominee DOB", value=pd.to_datetime(val("nominee_dob")) if val("nominee_dob") else None)

            st.markdown("#### 🏦 Bank & PF Details")
            c1, c2, c3 = st.columns(3)
            bank = c1.text_input("Bank Name", val("bank_name"))
            acc = c2.text_input("Account Number", val("account_no"))
            ifsc = c3.text_input("IFSC Code", val("ifsc"))

            c1, c2, c3 = st.columns(3)
            uan = c1.text_input("UAN Number", val("uan"))
            pf_no = c2.text_input("PF Number", val("pf_no"))
            esic_no = c3.text_input("ESIC Number", val("esic_no"))

            st.markdown("#### ⏰ Shift & Attendance")
            c1, c2 = st.columns(2)
            shift_idx = shifts.index(val("shift", shifts[0])) if val("shift") in shifts else 0
            shift = c1.selectbox("Shift", shifts, index=shift_idx)
            is_open = c2.selectbox("Shift Type", ["Fixed", "Open"],
                                   index=1 if str(val("is_open_shift")).lower() in ["true", "1", "yes", "open"] else 0)

            st.markdown("#### 💰 Salary Structure")
            c1, c2, c3 = st.columns(3)
            gross = c1.number_input("Gross Salary (₹)", value=float(val("gross_salary", 0)), min_value=0.0, step=100.0)
            basic = c2.number_input("Basic (₹)", value=float(val("basic", 0)), min_value=0.0, step=100.0)
            hra = c3.number_input("HRA (₹)", value=float(val("hra", 0)), min_value=0.0, step=100.0)

            c1, c2, c3 = st.columns(3)
            conv = c1.number_input("Conveyance (₹)", value=float(val("conveyance", 0)), min_value=0.0, step=100.0)
            special = c2.number_input("Special Allowance (₹)", value=float(val("special_allowance", 0)), min_value=0.0, step=100.0)
            medical = c3.number_input("Medical Allowance (₹)", value=float(val("medical_allowance", 0)), min_value=0.0, step=100.0)

            c1, c2 = st.columns(2)
            food = c1.number_input("Food Allowance (₹)", value=float(val("food_allowance", 0)), min_value=0.0, step=100.0)
            status_emp = c2.selectbox("Employee Status", ["Active", "Inactive"],
                                       index=0 if val("status", "Active") == "Active" else 1)

            c1, c2 = st.columns(2)
            pf_app = c1.selectbox("PF Applicable", ["Yes", "No"],
                                   index=0 if val("pf_applicable", "Yes") == "Yes" else 1)
            esic_app = c2.selectbox("ESIC Applicable", ["Yes", "No"],
                                    index=0 if val("esic_applicable", "No") == "Yes" else 1)

            submitted = st.form_submit_button("💾 Save Employee", use_container_width=True)

        if submitted:
            if not ecode or not name:
                st.error("E-Code and Name are required!")
            else:
                new_row = {
                    "ecode": ecode.upper().strip(),
                    "name": name.strip(),
                    "department": dept,
                    "designation": desig,
                    "doj": str(doj) if doj else "",
                    "dob": str(dob) if dob else "",
                    "gender": gender,
                    "mobile": mobile,
                    "email": email,
                    "address": address,
                    "father_name": father,
                    "mother_name": mother,
                    "spouse_name": spouse,
                    "nominee_name": nominee_name,
                    "nominee_relation": nominee_rel,
                    "nominee_dob": str(nominee_dob_val) if nominee_dob_val else "",
                    "bank_name": bank,
                    "account_no": acc,
                    "ifsc": ifsc,
                    "uan": uan,
                    "pf_no": pf_no,
                    "esic_no": esic_no,
                    "shift": shift,
                    "is_open_shift": "Yes" if is_open == "Open" else "No",
                    "gross_salary": gross,
                    "basic": basic,
                    "hra": hra,
                    "conveyance": conv,
                    "special_allowance": special,
                    "medical_allowance": medical,
                    "food_allowance": food,
                    "pf_applicable": pf_app,
                    "esic_applicable": esic_app,
                    "status": status_emp,
                    "exit_date": ""
                }

                emp_df = load_employees()
                if mode == "Edit Existing Employee" and ecode.upper().strip() in emp_df["ecode"].values:
                    emp_df = emp_df[emp_df["ecode"] != ecode.upper().strip()]

                new_df = pd.DataFrame([new_row])
                emp_df = pd.concat([emp_df, new_df], ignore_index=True)
                save_employees(emp_df)
                st.success(f"✅ Employee {name} ({ecode}) saved successfully!")
                st.rerun()

    # ── TAB 3: BULK IMPORT ────────────────────────────────────────────────────
    with tab3:
        st.markdown("#### 📤 Bulk Import Employees via Excel/CSV")
        st.info("""
        **Instructions:**
        1. Download the template below
        2. Fill in employee data
        3. Upload the filled template
        
        **Required columns:** ecode, name, department, designation, doj, gross_salary, basic, shift
        """)

        # Template download
        from utils.helpers import EMPLOYEE_COLUMNS
        template_df = pd.DataFrame(columns=EMPLOYEE_COLUMNS)
        csv_template = template_df.to_csv(index=False)
        st.download_button("📥 Download Import Template", csv_template,
                          "employee_import_template.csv", "text/csv")

        uploaded = st.file_uploader("Upload Filled Template (CSV or Excel)", type=["csv", "xlsx"])
        if uploaded:
            if uploaded.name.endswith(".csv"):
                import_df = pd.read_csv(uploaded, dtype=str)
            else:
                import_df = pd.read_excel(uploaded, dtype=str)

            st.dataframe(import_df.head(10), use_container_width=True)
            if st.button("✅ Confirm Import"):
                emp_df = load_employees()
                # Merge - update existing, add new
                for _, row in import_df.iterrows():
                    ecode_val = str(row.get("ecode", "")).upper().strip()
                    if ecode_val and ecode_val in emp_df["ecode"].values:
                        emp_df = emp_df[emp_df["ecode"] != ecode_val]
                emp_df = pd.concat([emp_df, import_df], ignore_index=True)
                save_employees(emp_df)
                st.success(f"✅ {len(import_df)} employees imported successfully!")
                st.rerun()
