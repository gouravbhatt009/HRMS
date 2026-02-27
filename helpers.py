import streamlit as st
import json
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.helpers import load_config, save_config

def render():
    config = load_config()

    st.markdown("""
    <div class="page-header">
        <h1>⚙️ Settings & Rules Configuration</h1>
        <p>Customize all rules, shifts, salary components, PF, ESIC, leave policies — fully flexible</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏢 Company",
        "⏰ Shifts & Attendance",
        "💰 Salary Components",
        "🏛️ PF & ESIC",
        "🌴 Leave Policy",
        "📋 View Raw Config"
    ])

    # ── TAB 1: COMPANY ───────────────────────────────────────────────────────
    with tab1:
        st.markdown("### Company Information")
        with st.form("company_form"):
            name = st.text_input("Company Name", config["company"]["name"])
            address = st.text_area("Address", config["company"].get("address", ""))
            if st.form_submit_button("💾 Save Company Info", use_container_width=True):
                config["company"]["name"] = name
                config["company"]["address"] = address
                save_config(config)
                st.success("✅ Company info saved!")

    # ── TAB 2: SHIFTS ────────────────────────────────────────────────────────
    with tab2:
        st.markdown("### Shift Configuration")

        with st.form("shift_form"):
            grace = st.number_input("Grace Period (Minutes)", value=config["shifts"]["grace_period_minutes"], min_value=0, max_value=30)
            ot_thresh = st.number_input("Overtime Threshold (Minutes after shift end)", value=config["shifts"]["overtime_threshold_minutes"], min_value=0, max_value=120)
            week_off = st.selectbox("Week Off Day", ["Sunday", "Saturday", "Monday"],
                                    index=["Sunday", "Saturday", "Monday"].index(config["attendance"]["week_off"]))
            sandwich = st.checkbox("Enable Sandwich Rule", value=config["attendance"]["sandwich_rule"])
            min_days = st.number_input("Minimum Working Days per Week (Sandwich Rule)", value=config["attendance"]["min_days_per_week"], min_value=1, max_value=6)

            if st.form_submit_button("💾 Save Attendance Rules", use_container_width=True):
                config["shifts"]["grace_period_minutes"] = grace
                config["shifts"]["overtime_threshold_minutes"] = ot_thresh
                config["attendance"]["week_off"] = week_off
                config["attendance"]["sandwich_rule"] = sandwich
                config["attendance"]["min_days_per_week"] = min_days
                save_config(config)
                st.success("✅ Attendance rules saved!")

        st.markdown("---")
        st.markdown("### Fixed Shifts")
        st.info("You can add, edit, or remove fixed shifts below.")

        shifts = config["shifts"]["fixed"]
        shifts_data = []
        for i, s in enumerate(shifts):
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            name_val = c1.text_input("Shift Name", s["name"], key=f"sn_{i}")
            start_val = c2.text_input("Start (HH:MM)", s["start"], key=f"ss_{i}")
            end_val = c3.text_input("End (HH:MM)", s["end"], key=f"se_{i}")
            hours_val = c4.number_input("Hours", value=float(s["total_hours"]), key=f"sh_{i}", min_value=0.0)
            shifts_data.append({"name": name_val, "start": start_val, "end": end_val, "total_hours": hours_val})

        # Add new shift
        st.markdown("#### ➕ Add New Shift")
        c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
        new_name = c1.text_input("Shift Name", "", key="new_sn")
        new_start = c2.text_input("Start", "09:00", key="new_ss")
        new_end = c3.text_input("End", "18:00", key="new_se")
        new_hours = c4.number_input("Hours", value=9.0, key="new_sh")

        col1, col2 = st.columns(2)
        if col1.button("💾 Save All Shifts", use_container_width=True):
            config["shifts"]["fixed"] = shifts_data
            if new_name.strip():
                config["shifts"]["fixed"].append({
                    "name": new_name, "start": new_start,
                    "end": new_end, "total_hours": new_hours
                })
            save_config(config)
            st.success("✅ Shifts saved!")
            st.rerun()
        if col2.button("🗑️ Remove Last Shift", use_container_width=True):
            if config["shifts"]["fixed"]:
                config["shifts"]["fixed"].pop()
                save_config(config)
                st.warning("Last shift removed!")
                st.rerun()

    # ── TAB 3: SALARY COMPONENTS ─────────────────────────────────────────────
    with tab3:
        st.markdown("### Salary Component Configuration")
        st.info("Configure which salary components are active and how they are calculated.")

        components = config["salary_components"]["components"]

        updated_components = []
        for i, comp in enumerate(components):
            with st.expander(f"{'✅' if comp.get('enabled') else '❌'} {comp['name']}", expanded=comp.get('enabled', False)):
                c1, c2, c3 = st.columns(3)
                comp_name = c1.text_input("Component Name", comp["name"], key=f"cn_{i}")
                comp_enabled = c2.checkbox("Enabled", comp.get("enabled", True), key=f"ce_{i}")
                comp_taxable = c3.checkbox("Taxable", comp.get("taxable", True), key=f"ct_{i}")

                comp_type = st.selectbox("Type", ["fixed", "percentage", "calculated"],
                                          index=["fixed", "percentage", "calculated"].index(comp.get("type", "fixed")),
                                          key=f"ctype_{i}")

                comp_pct = 0.0
                comp_pct_of = "Basic"
                if comp_type == "percentage":
                    c1, c2 = st.columns(2)
                    comp_pct = c1.number_input("Percentage %", value=float(comp.get("value", 40)), key=f"cpct_{i}")
                    comp_pct_of = c2.text_input("Percentage of", comp.get("percentage_of", "Basic"), key=f"cpof_{i}")

                updated_comp = {
                    "name": comp_name,
                    "type": comp_type,
                    "taxable": comp_taxable,
                    "enabled": comp_enabled
                }
                if comp_type == "percentage":
                    updated_comp["value"] = comp_pct
                    updated_comp["percentage_of"] = comp_pct_of

                updated_components.append(updated_comp)

        # Add new component
        st.markdown("#### ➕ Add New Salary Component")
        with st.form("add_component"):
            c1, c2, c3 = st.columns(3)
            nc_name = c1.text_input("Component Name")
            nc_type = c2.selectbox("Type", ["fixed", "percentage"])
            nc_taxable = c3.checkbox("Taxable", True)
            if st.form_submit_button("Add Component"):
                if nc_name:
                    updated_components.append({
                        "name": nc_name, "type": nc_type,
                        "taxable": nc_taxable, "enabled": True
                    })

        if st.button("💾 Save Salary Components", use_container_width=True):
            config["salary_components"]["components"] = updated_components
            save_config(config)
            st.success("✅ Salary components saved!")

        # Overtime settings
        st.markdown("---")
        st.markdown("### ⏰ Overtime Settings")
        with st.form("ot_form"):
            ot_enabled = st.checkbox("Overtime Enabled", config["overtime"]["enabled"])
            ot_rate = st.number_input("OT Rate Multiplier", value=float(config["overtime"]["rate_multiplier"]), min_value=1.0, max_value=3.0, step=0.5)
            ot_base = st.selectbox("OT Calculation Base", ["Basic", "Gross"],
                                    index=["Basic", "Gross"].index(config["overtime"]["calculation_base"]))
            if st.form_submit_button("💾 Save OT Settings"):
                config["overtime"]["enabled"] = ot_enabled
                config["overtime"]["rate_multiplier"] = ot_rate
                config["overtime"]["calculation_base"] = ot_base
                save_config(config)
                st.success("✅ Overtime settings saved!")

    # ── TAB 4: PF & ESIC ─────────────────────────────────────────────────────
    with tab4:
        st.markdown("### 🏛️ PF Configuration")
        with st.form("pf_form"):
            pf_enabled = st.checkbox("PF Enabled", config["pf"]["enabled"])
            c1, c2 = st.columns(2)
            pf_emp_pct = c1.number_input("Employee PF %", value=float(config["pf"]["employee_percentage"]), min_value=0.0, max_value=100.0, step=0.5)
            pf_er_pct = c2.number_input("Employer PF %", value=float(config["pf"]["employer_percentage"]), min_value=0.0, max_value=100.0, step=0.5)

            pf_base_options = ["Basic", "Basic + DA", "Gross"]
            pf_base = st.selectbox("PF Calculation Base",
                                    pf_base_options,
                                    index=pf_base_options.index(config["pf"]["pf_base"]) if config["pf"]["pf_base"] in pf_base_options else 0)
            
            pf_cap = st.checkbox("Cap PF at ₹15,000 Basic (Government Limit)", value=config["pf"]["cap_at_15000"])
            st.info("💡 If unchecked, PF will be calculated on actual basic salary (above ₹15,000 too)")

            eps_pct = st.number_input("EPS % (from Employer PF)", value=float(config["pf"]["eps_percentage"]), min_value=0.0, max_value=20.0, step=0.5)

            if st.form_submit_button("💾 Save PF Settings", use_container_width=True):
                config["pf"]["enabled"] = pf_enabled
                config["pf"]["employee_percentage"] = pf_emp_pct
                config["pf"]["employer_percentage"] = pf_er_pct
                config["pf"]["pf_base"] = pf_base
                config["pf"]["cap_at_15000"] = pf_cap
                config["pf"]["eps_percentage"] = eps_pct
                save_config(config)
                st.success("✅ PF settings saved!")

        st.markdown("---")
        st.markdown("### 🏥 ESIC Configuration")
        with st.form("esic_form"):
            esic_enabled = st.checkbox("ESIC Enabled", config["esic"]["enabled"])
            c1, c2 = st.columns(2)
            esic_emp = c1.number_input("Employee ESIC %", value=float(config["esic"]["employee_percentage"]), min_value=0.0, max_value=10.0, step=0.25)
            esic_er = c2.number_input("Employer ESIC %", value=float(config["esic"]["employer_percentage"]), min_value=0.0, max_value=10.0, step=0.25)
            esic_ceil = st.number_input("ESIC Wage Ceiling (₹)", value=int(config["esic"]["wage_ceiling"]), min_value=0, step=1000)

            if st.form_submit_button("💾 Save ESIC Settings", use_container_width=True):
                config["esic"]["enabled"] = esic_enabled
                config["esic"]["employee_percentage"] = esic_emp
                config["esic"]["employer_percentage"] = esic_er
                config["esic"]["wage_ceiling"] = esic_ceil
                save_config(config)
                st.success("✅ ESIC settings saved!")

        st.markdown("---")
        st.markdown("### 🔕 TDS & Professional Tax")
        st.info("Currently both TDS and Professional Tax are **disabled** as per your requirement. You can enable them below if needed in future.")
        with st.form("tds_pt_form"):
            tds_on = st.checkbox("Enable TDS", config["tds"]["enabled"])
            pt_on = st.checkbox("Enable Professional Tax", config["professional_tax"]["enabled"])
            if st.form_submit_button("Save"):
                config["tds"]["enabled"] = tds_on
                config["professional_tax"]["enabled"] = pt_on
                save_config(config)
                st.success("Saved!")

    # ── TAB 5: LEAVE POLICY ──────────────────────────────────────────────────
    with tab5:
        st.markdown("### 🌴 Leave Policy Configuration")
        with st.form("leave_form"):
            st.markdown("#### Privilege Leave (PL / EL)")
            c1, c2, c3 = st.columns(3)
            pl_annual = c1.number_input("PL Annual Days", value=int(config["leave"]["pl"]["annual"]), min_value=0)
            pl_cf = c2.checkbox("PL Carry Forward", config["leave"]["pl"]["carry_forward"])
            pl_max_cf = c3.number_input("Max Carry Forward Days", value=int(config["leave"]["pl"]["max_carry_forward"]), min_value=0)

            st.markdown("#### Casual Leave (CL)")
            c1, c2 = st.columns(2)
            cl_annual = c1.number_input("CL Annual Days", value=int(config["leave"]["cl"]["annual"]), min_value=0)
            cl_cf = c2.checkbox("CL Carry Forward", config["leave"]["cl"]["carry_forward"])

            st.markdown("#### Sick Leave (SL)")
            c1, c2 = st.columns(2)
            sl_annual = c1.number_input("SL Annual Days", value=int(config["leave"]["sl"]["annual"]), min_value=0)
            sl_cf = c2.checkbox("SL Carry Forward", config["leave"]["sl"]["carry_forward"])

            if st.form_submit_button("💾 Save Leave Policy", use_container_width=True):
                config["leave"]["pl"]["annual"] = pl_annual
                config["leave"]["pl"]["carry_forward"] = pl_cf
                config["leave"]["pl"]["max_carry_forward"] = pl_max_cf
                config["leave"]["cl"]["annual"] = cl_annual
                config["leave"]["cl"]["carry_forward"] = cl_cf
                config["leave"]["sl"]["annual"] = sl_annual
                config["leave"]["sl"]["carry_forward"] = sl_cf
                save_config(config)
                st.success("✅ Leave policy saved!")

    # ── TAB 6: RAW CONFIG ────────────────────────────────────────────────────
    with tab6:
        st.markdown("### 📋 Raw Configuration (JSON)")
        st.warning("⚠️ Advanced users only. Edit carefully!")
        raw = json.dumps(config, indent=2)
        edited = st.text_area("Configuration JSON", raw, height=500)
        if st.button("💾 Save Raw Config", use_container_width=True):
            try:
                new_config = json.loads(edited)
                save_config(new_config)
                st.success("✅ Configuration saved!")
                st.rerun()
            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON: {e}")
