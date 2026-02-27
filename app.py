# =============================================================================
#  HR & PAYROLL MANAGEMENT SYSTEM  —  Single File Version
#  Upload only this file + requirements.txt to GitHub, then deploy on Streamlit
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import calendar
from datetime import datetime, date, timedelta

st.set_page_config(
    page_title="HR & Payroll System",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #f0f2f6; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a237e 0%, #283593 50%, #3949ab 100%);
    }
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown p { color: white !important; }
    .metric-card {
        background: white; border-radius: 12px; padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid #3949ab; margin-bottom: 12px;
    }
    .metric-card h3 { color: #3949ab; font-size: 14px; margin: 0; }
    .metric-card h1 { color: #1a237e; font-size: 28px; margin: 4px 0; }
    .page-header {
        background: linear-gradient(135deg, #1a237e, #3949ab);
        color: white; padding: 20px 28px; border-radius: 12px; margin-bottom: 24px;
    }
    .page-header h1 { color: white; margin: 0; font-size: 26px; }
    .page-header p  { color: #c5cae9; margin: 4px 0 0 0; font-size: 14px; }
    .stButton > button {
        background: linear-gradient(135deg, #1a237e, #3949ab);
        color: white; border: none; border-radius: 8px;
        padding: 8px 20px; font-weight: 600;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #283593, #3f51b5);
        box-shadow: 0 4px 12px rgba(63,81,181,0.4);
    }
    .dataframe { font-size: 13px !important; }
    .stTabs [data-baseweb="tab"] { font-weight: 600; }
    .stTabs [aria-selected="true"] { color: #1a237e !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  DATA PATHS & DEFAULT CONFIG
# ══════════════════════════════════════════════════════════════════════════════

BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
DATA_DIR       = os.path.join(BASE_DIR, "data")
CONFIG_PATH    = os.path.join(DATA_DIR, "config.json")
EMPLOYEES_PATH = os.path.join(DATA_DIR, "employees.csv")
ATTENDANCE_PATH= os.path.join(DATA_DIR, "attendance.csv")
LEAVES_PATH    = os.path.join(DATA_DIR, "leaves.csv")

os.makedirs(DATA_DIR, exist_ok=True)

DEFAULT_CONFIG = {
    "company": {"name": "My Company", "address": ""},
    "shifts": {
        "fixed": [
            {"name": "Morning 9-6",   "start": "09:00", "end": "18:00", "total_hours": 9.0},
            {"name": "Morning 9-6:30","start": "09:00", "end": "18:30", "total_hours": 9.5},
            {"name": "Late 10-6:30",  "start": "10:00", "end": "18:30", "total_hours": 8.5},
            {"name": "Long 9-9",      "start": "09:00", "end": "21:00", "total_hours": 12.0}
        ],
        "grace_period_minutes": 5,
        "overtime_threshold_minutes": 30
    },
    "attendance": {
        "week_off": "Sunday",
        "working_days": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"],
        "sandwich_rule": True,
        "min_days_per_week": 3
    },
    "salary_components": {
        "components": [
            {"name": "Basic",               "type": "fixed",      "taxable": True,  "enabled": True},
            {"name": "HRA",                 "type": "percentage", "percentage_of": "Basic", "value": 40, "taxable": True,  "enabled": True},
            {"name": "Conveyance Allowance","type": "fixed",      "taxable": False, "enabled": True},
            {"name": "Special Allowance",   "type": "calculated", "taxable": True,  "enabled": True},
            {"name": "Medical Allowance",   "type": "fixed",      "taxable": False, "enabled": False},
            {"name": "Food Allowance",      "type": "fixed",      "taxable": False, "enabled": False}
        ]
    },
    "pf": {
        "enabled": True, "employee_percentage": 12, "employer_percentage": 12,
        "pf_base": "Basic", "cap_at_15000": False, "eps_percentage": 8.33, "edli_enabled": True
    },
    "esic": {"enabled": False, "employee_percentage": 0.75, "employer_percentage": 3.25, "wage_ceiling": 21000},
    "tds": {"enabled": False},
    "professional_tax": {"enabled": False},
    "leave": {
        "pl": {"annual": 12, "carry_forward": True,  "max_carry_forward": 30, "encashable": True},
        "cl": {"annual": 6,  "carry_forward": False, "max_carry_forward": 0,  "encashable": False},
        "sl": {"annual": 6,  "carry_forward": False, "encashable": False}
    },
    "overtime": {"enabled": True, "rate_multiplier": 1.5, "calculation_base": "Basic"}
}

EMPLOYEE_COLUMNS = [
    "ecode","name","department","designation","doj","dob","gender","mobile","email","address",
    "father_name","mother_name","spouse_name",
    "nominee_name","nominee_relation","nominee_dob",
    "bank_name","account_no","ifsc","uan","pf_no","esic_no",
    "shift","is_open_shift",
    "gross_salary","basic","hra","conveyance","special_allowance","medical_allowance","food_allowance",
    "pf_applicable","esic_applicable","status","exit_date"
]
ATTENDANCE_COLUMNS = [
    "ecode","name","date","day","shift","in_time","out_time",
    "working_hours","overtime_hours","early_going_minutes","late_entry_minutes","status","remarks"
]
LEAVE_COLUMNS = ["ecode","name","leave_type","from_date","to_date","days","reason","status","applied_on"]


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def load_config():
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
    with open(CONFIG_PATH) as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

def load_employees():
    if os.path.exists(EMPLOYEES_PATH):
        df = pd.read_csv(EMPLOYEES_PATH, dtype=str)
        for col in EMPLOYEE_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df
    return pd.DataFrame(columns=EMPLOYEE_COLUMNS)

def save_employees(df):
    df.to_csv(EMPLOYEES_PATH, index=False)

def load_attendance():
    if os.path.exists(ATTENDANCE_PATH):
        df = pd.read_csv(ATTENDANCE_PATH, dtype=str)
        for col in ATTENDANCE_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df
    return pd.DataFrame(columns=ATTENDANCE_COLUMNS)

def save_attendance(df):
    df.to_csv(ATTENDANCE_PATH, index=False)

def load_leaves():
    if os.path.exists(LEAVES_PATH):
        df = pd.read_csv(LEAVES_PATH, dtype=str)
        for col in LEAVE_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df
    return pd.DataFrame(columns=LEAVE_COLUMNS)

def save_leaves(df):
    df.to_csv(LEAVES_PATH, index=False)

# Bootstrap empty files
for _path, _cols in [(EMPLOYEES_PATH, EMPLOYEE_COLUMNS),
                     (ATTENDANCE_PATH, ATTENDANCE_COLUMNS),
                     (LEAVES_PATH, LEAVE_COLUMNS)]:
    if not os.path.exists(_path):
        pd.DataFrame(columns=_cols).to_csv(_path, index=False)


def parse_time(t_str):
    if pd.isna(t_str) or str(t_str).strip() == "":
        return None
    t_str = str(t_str).strip()
    for fmt in ["%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M%p"]:
        try:
            return datetime.strptime(t_str, fmt).time()
        except:
            pass
    return None

def time_to_minutes(t):
    return None if t is None else t.hour * 60 + t.minute

def calculate_working_hours(in_time_str, out_time_str, shift_name, config):
    result = {"working_hours": 0.0, "overtime_hours": 0.0,
              "late_entry_minutes": 0, "early_going_minutes": 0, "status": "Present"}
    in_t  = parse_time(in_time_str)
    out_t = parse_time(out_time_str)
    if in_t is None and out_t is None:
        result["status"] = "Missing Punch";  return result
    if in_t is None:
        result["status"] = "Missing IN Punch"; return result
    if out_t is None:
        result["status"] = "Missing OUT Punch"; return result

    in_mins  = time_to_minutes(in_t)
    out_mins = time_to_minutes(out_t)
    if out_mins < in_mins:
        out_mins += 24 * 60
    actual_work_mins = out_mins - in_mins

    grace       = config["shifts"]["grace_period_minutes"]
    ot_threshold= config["shifts"]["overtime_threshold_minutes"]
    shift_config= next((s for s in config["shifts"]["fixed"] if s["name"] == shift_name), None)

    if shift_config is None or shift_name == "Open Shift":
        result["working_hours"] = round(actual_work_mins / 60, 2)
        return result

    shift_start = time_to_minutes(parse_time(shift_config["start"]))
    shift_end   = time_to_minutes(parse_time(shift_config["end"]))

    if in_mins > shift_start + grace:
        result["late_entry_minutes"] = in_mins - shift_start
    if out_mins < shift_end:
        result["early_going_minutes"] = shift_end - out_mins
    if out_mins > shift_end + ot_threshold:
        result["overtime_hours"] = round((out_mins - shift_end) / 60, 2)

    result["working_hours"] = round(actual_work_mins / 60, 2)
    return result

def apply_sandwich_rule(df_emp, config):
    if not config["attendance"]["sandwich_rule"]:
        return df_emp
    df = df_emp.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    week_off = config["attendance"]["week_off"]
    min_days = config["attendance"]["min_days_per_week"]

    for i in range(1, len(df) - 1):
        if df.loc[i, "day"] == week_off:
            if df.loc[i-1, "status"] == "Absent" and df.loc[i+1, "status"] == "Absent":
                df.loc[i, "status"]  = "Absent (Sandwich)"
                df.loc[i, "remarks"] = "Sandwich Rule Applied"

    df["week"] = df["date"].dt.isocalendar().week
    for _, wdf in df.groupby("week"):
        wdays = wdf[wdf["day"] != week_off]
        if (wdays["status"] == "Present").sum() < min_days:
            for idx in wdays[wdays["status"] == "Present"].index:
                df.loc[idx, "remarks"] = str(df.loc[idx, "remarks"]) + " | Low Week Attendance"
    return df

def calculate_payroll(emp_row, present_days, total_working_days, overtime_hours, config):
    cfg_pf, cfg_esic, cfg_ot = config["pf"], config["esic"], config["overtime"]

    basic    = float(emp_row.get("basic",            0) or 0)
    hra      = float(emp_row.get("hra",              0) or 0)
    conv     = float(emp_row.get("conveyance",       0) or 0)
    special  = float(emp_row.get("special_allowance",0) or 0)
    medical  = float(emp_row.get("medical_allowance",0) or 0)
    food     = float(emp_row.get("food_allowance",   0) or 0)
    gross    = basic + hra + conv + special + medical + food

    ratio         = present_days / total_working_days if total_working_days > 0 else 0
    earned_gross  = gross * ratio
    earned_basic  = basic   * ratio
    earned_hra    = hra     * ratio
    earned_conv   = conv    * ratio
    earned_special= special * ratio
    earned_medical= medical * ratio
    earned_food   = food    * ratio

    ot_pay = 0.0
    if cfg_ot["enabled"] and overtime_hours > 0:
        base_for_ot = earned_basic if cfg_ot["calculation_base"] == "Basic" else earned_gross
        hourly_rate = base_for_ot / (26 * 8)
        ot_pay      = hourly_rate * overtime_hours * cfg_ot["rate_multiplier"]

    pf_employee = pf_employer = eps = 0.0
    if cfg_pf["enabled"] and str(emp_row.get("pf_applicable","Yes")).lower() in ["yes","true","1","y"]:
        pf_base = earned_basic if cfg_pf["pf_base"] == "Basic" else earned_gross
        if cfg_pf["cap_at_15000"]:
            pf_base = min(pf_base, 15000 * ratio)
        pf_employee = round(pf_base * cfg_pf["employee_percentage"] / 100, 2)
        pf_employer = round(pf_base * cfg_pf["employer_percentage"] / 100, 2)
        eps         = round(pf_base * cfg_pf["eps_percentage"]       / 100, 2)

    esic_employee = esic_employer = 0.0
    if cfg_esic["enabled"] and str(emp_row.get("esic_applicable","No")).lower() in ["yes","true","1","y"]:
        if gross <= cfg_esic["wage_ceiling"]:
            esic_employee = round(earned_gross * cfg_esic["employee_percentage"] / 100, 2)
            esic_employer = round(earned_gross * cfg_esic["employer_percentage"] / 100, 2)

    total_deductions = pf_employee + esic_employee
    net_pay          = round(earned_gross + ot_pay - total_deductions, 2)

    return {
        "ecode": emp_row.get("ecode",""), "name": emp_row.get("name",""),
        "present_days": present_days, "gross_salary": round(gross, 2),
        "earned_basic": round(earned_basic,2), "earned_hra": round(earned_hra,2),
        "earned_conveyance": round(earned_conv,2), "earned_special": round(earned_special,2),
        "earned_medical": round(earned_medical,2), "earned_food": round(earned_food,2),
        "earned_gross": round(earned_gross,2), "overtime_hours": round(overtime_hours,2),
        "overtime_pay": round(ot_pay,2), "pf_employee": pf_employee, "pf_employer": pf_employer,
        "eps": eps, "esic_employee": esic_employee, "esic_employer": esic_employer,
        "total_deductions": round(total_deductions,2), "net_pay": net_pay
    }

def get_leave_balance(ecode, year, config):
    leaves_df = load_leaves()
    cfg       = config["leave"]
    emp_leaves= leaves_df[
        (leaves_df["ecode"] == ecode) & (leaves_df["status"] == "Approved") &
        (pd.to_datetime(leaves_df["from_date"], errors="coerce").dt.year == year)
    ]
    def taken(lt): return emp_leaves[emp_leaves["leave_type"] == lt]["days"].astype(float).sum()
    pl_t, cl_t, sl_t = taken("PL"), taken("CL"), taken("SL")
    return {
        "pl_entitled": cfg["pl"]["annual"], "pl_taken": pl_t, "pl_balance": max(0, cfg["pl"]["annual"] - pl_t),
        "cl_entitled": cfg["cl"]["annual"], "cl_taken": cl_t, "cl_balance": max(0, cfg["cl"]["annual"] - cl_t),
        "sl_entitled": cfg["sl"]["annual"], "sl_taken": sl_t, "sl_balance": max(0, cfg["sl"]["annual"] - sl_t),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR NAVIGATION
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 👥 HR & Payroll")
    st.markdown("---")
    NAV = {
        "🏠 Dashboard":        "dashboard",
        "👤 Employee Master":  "employees",
        "🕐 Attendance":       "attendance",
        "📊 Payroll":          "payroll",
        "🌴 Leave Management": "leaves",
        "⚙️ Settings & Rules": "settings",
    }
    if "current_page" not in st.session_state:
        st.session_state.current_page = "dashboard"
    for label, key in NAV.items():
        if st.button(label, key=f"nav_{key}", use_container_width=True):
            st.session_state.current_page = key
            st.rerun()
    st.markdown("---")
    _cfg = load_config()
    st.markdown(f"**🏢 {_cfg['company']['name']}**")

PAGE = st.session_state.current_page
MONTHS = ["January","February","March","April","May","June",
          "July","August","September","October","November","December"]


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

if PAGE == "dashboard":
    config  = load_config()
    emp_df  = load_employees()
    att_df  = load_attendance()

    st.markdown('<div class="page-header"><h1>🏠 Dashboard</h1><p>Welcome to the HR & Payroll Management System</p></div>', unsafe_allow_html=True)

    today     = date.today()
    today_str = str(today)
    total_emp = len(emp_df[emp_df["status"] == "Active"]) if "status" in emp_df.columns else len(emp_df)
    today_att     = att_df[att_df["date"] == today_str] if not att_df.empty else pd.DataFrame()
    present_today = len(today_att[today_att["status"] == "Present"]) if not today_att.empty else 0
    absent_today  = total_emp - present_today
    missing_punch = len(today_att[today_att["status"].str.contains("Missing", na=False)]) if not today_att.empty else 0

    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f'<div class="metric-card"><h3>👥 Total Employees</h3><h1>{total_emp}</h1></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card" style="border-left-color:#2e7d32"><h3>✅ Present Today</h3><h1>{present_today}</h1></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card" style="border-left-color:#c62828"><h3>❌ Absent Today</h3><h1>{absent_today}</h1></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card" style="border-left-color:#f57c00"><h3>⚠️ Missing Punch</h3><h1>{missing_punch}</h1></div>', unsafe_allow_html=True)
    st.markdown("---")

    col_l, col_r = st.columns([3, 2])
    with col_l:
        st.markdown("### 📅 Monthly Attendance Overview")
        if not att_df.empty:
            att_df["date"] = pd.to_datetime(att_df["date"], errors="coerce")
            month_att = att_df[att_df["date"].dt.month == today.month]
            if not month_att.empty:
                daily = month_att.groupby("date")["status"].apply(lambda x:(x=="Present").sum()).reset_index()
                daily.columns = ["Date","Present Count"]
                fig = px.bar(daily, x="Date", y="Present Count", color_discrete_sequence=["#3949ab"], title="Daily Present Count This Month")
                fig.update_layout(showlegend=False, height=300, plot_bgcolor="white", paper_bgcolor="white")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No attendance data for this month yet.")
        else:
            st.info("No attendance data yet. Upload attendance data to get started.")

    with col_r:
        st.markdown("### 🏢 Department Wise Employees")
        if not emp_df.empty and "department" in emp_df.columns:
            dept = emp_df[emp_df["status"]=="Active"]["department"].value_counts().reset_index()
            dept.columns = ["Department","Count"]
            fig2 = px.pie(dept, values="Count", names="Department", color_discrete_sequence=px.colors.sequential.Blues_r)
            fig2.update_layout(height=300, paper_bgcolor="white")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Add employees to see department breakdown.")

    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    q1,q2,q3,q4 = st.columns(4)
    with q1:
        if st.button("➕ Add New Employee", use_container_width=True):
            st.session_state.current_page = "employees"; st.rerun()
    with q2:
        if st.button("📤 Upload Attendance", use_container_width=True):
            st.session_state.current_page = "attendance"; st.rerun()
    with q3:
        if st.button("💰 Run Payroll", use_container_width=True):
            st.session_state.current_page = "payroll"; st.rerun()
    with q4:
        if st.button("⚙️ Configure Rules", use_container_width=True):
            st.session_state.current_page = "settings"; st.rerun()

    if not att_df.empty:
        st.markdown("---")
        st.markdown("### ⚠️ Missing Punch Alerts (Last 7 Days)")
        att_df["date"] = pd.to_datetime(att_df["date"], errors="coerce")
        recent  = att_df[att_df["date"] >= pd.Timestamp(today) - pd.Timedelta(days=7)]
        missing = recent[recent["status"].str.contains("Missing", na=False)]
        if not missing.empty:
            st.dataframe(missing[["ecode","name","date","in_time","out_time","status"]].sort_values("date",ascending=False), use_container_width=True, hide_index=True)
        else:
            st.success("✅ No missing punch issues in the last 7 days!")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: EMPLOYEE MASTER
# ══════════════════════════════════════════════════════════════════════════════

elif PAGE == "employees":
    config = load_config()
    emp_df = load_employees()
    st.markdown('<div class="page-header"><h1>👤 Employee Master</h1><p>Manage all employee records, personal details, and salary structure</p></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 Employee List", "➕ Add / Edit Employee", "📤 Bulk Import"])

    with tab1:
        cf1,cf2,cf3 = st.columns([2,2,1])
        search       = cf1.text_input("🔍 Search by Name or E-Code","")
        dept_opts    = ["All"]+sorted(emp_df["department"].dropna().unique().tolist()) if not emp_df.empty else ["All"]
        dept_filter  = cf2.selectbox("Filter by Department", dept_opts)
        status_filter= cf3.selectbox("Status",["All","Active","Inactive"])

        disp = emp_df.copy()
        if search:
            disp = disp[disp["name"].str.contains(search,case=False,na=False)|disp["ecode"].str.contains(search,case=False,na=False)]
        if dept_filter!="All":
            disp = disp[disp["department"]==dept_filter]
        if status_filter!="All":
            disp = disp[disp["status"]==status_filter]

        st.markdown(f"**{len(disp)} employees found**")
        show = [c for c in ["ecode","name","department","designation","shift","gross_salary","status","doj"] if c in disp.columns]
        st.dataframe(disp[show], use_container_width=True, hide_index=True)
        if not disp.empty:
            st.download_button("📥 Download Employee List", disp.to_csv(index=False), "employees.csv","text/csv")

    with tab2:
        mode = st.radio("Mode",["Add New Employee","Edit Existing Employee"],horizontal=True)
        existing = {}
        if mode == "Edit Existing Employee" and not emp_df.empty:
            sel = st.selectbox("Select Employee E-Code", emp_df["ecode"].tolist())
            existing = emp_df[emp_df["ecode"]==sel].iloc[0].to_dict()

        def val(k, d=""):
            return existing.get(k,d) or d

        shifts = [s["name"] for s in config["shifts"]["fixed"]] + ["Open Shift"]

        with st.form("employee_form"):
            st.markdown("#### 🆔 Basic Information")
            c1,c2,c3 = st.columns(3)
            ecode  = c1.text_input("E-Code *", val("ecode"))
            name   = c2.text_input("Full Name *", val("name"))
            doj    = c3.date_input("Date of Joining", value=pd.to_datetime(val("doj")) if val("doj") else None)
            c1,c2,c3 = st.columns(3)
            dept   = c1.text_input("Department", val("department"))
            desig  = c2.text_input("Designation", val("designation"))
            gender = c3.selectbox("Gender",["Male","Female","Other"],index=["Male","Female","Other"].index(val("gender","Male")) if val("gender") in ["Male","Female","Other"] else 0)
            c1,c2,c3 = st.columns(3)
            mobile = c1.text_input("Mobile", val("mobile"))
            email  = c2.text_input("Email",  val("email"))
            dob    = c3.date_input("Date of Birth", value=pd.to_datetime(val("dob")) if val("dob") else None)
            address= st.text_area("Address", val("address"), height=60)

            st.markdown("#### 👨‍👩‍👧 Family Details")
            c1,c2,c3 = st.columns(3)
            father = c1.text_input("Father's Name", val("father_name"))
            mother = c2.text_input("Mother's Name", val("mother_name"))
            spouse = c3.text_input("Spouse Name",   val("spouse_name"))

            st.markdown("#### 📋 Nominee Details")
            c1,c2,c3 = st.columns(3)
            nom_name = c1.text_input("Nominee Name",     val("nominee_name"))
            nom_rel  = c2.text_input("Nominee Relation", val("nominee_relation"))
            nom_dob  = c3.date_input("Nominee DOB", value=pd.to_datetime(val("nominee_dob")) if val("nominee_dob") else None)

            st.markdown("#### 🏦 Bank & PF Details")
            c1,c2,c3 = st.columns(3)
            bank   = c1.text_input("Bank Name",      val("bank_name"))
            acc    = c2.text_input("Account Number", val("account_no"))
            ifsc   = c3.text_input("IFSC Code",      val("ifsc"))
            c1,c2,c3 = st.columns(3)
            uan    = c1.text_input("UAN Number", val("uan"))
            pf_no  = c2.text_input("PF Number",  val("pf_no"))
            esic_no= c3.text_input("ESIC Number",val("esic_no"))

            st.markdown("#### ⏰ Shift")
            c1,c2 = st.columns(2)
            shift_idx = shifts.index(val("shift",shifts[0])) if val("shift") in shifts else 0
            shift     = c1.selectbox("Shift", shifts, index=shift_idx)
            is_open   = c2.selectbox("Shift Type",["Fixed","Open"], index=1 if str(val("is_open_shift")).lower() in ["true","1","yes","open"] else 0)

            st.markdown("#### 💰 Salary Structure")
            c1,c2,c3 = st.columns(3)
            gross   = c1.number_input("Gross Salary (₹)",     value=float(val("gross_salary",0)),    min_value=0.0, step=100.0)
            basic_s = c2.number_input("Basic (₹)",            value=float(val("basic",0)),           min_value=0.0, step=100.0)
            hra_s   = c3.number_input("HRA (₹)",              value=float(val("hra",0)),             min_value=0.0, step=100.0)
            c1,c2,c3 = st.columns(3)
            conv_s  = c1.number_input("Conveyance (₹)",       value=float(val("conveyance",0)),      min_value=0.0, step=100.0)
            spec_s  = c2.number_input("Special Allowance (₹)",value=float(val("special_allowance",0)),min_value=0.0,step=100.0)
            med_s   = c3.number_input("Medical Allowance (₹)",value=float(val("medical_allowance",0)),min_value=0.0,step=100.0)
            c1,c2 = st.columns(2)
            food_s  = c1.number_input("Food Allowance (₹)",   value=float(val("food_allowance",0)),  min_value=0.0, step=100.0)
            emp_status = c2.selectbox("Employee Status",["Active","Inactive"], index=0 if val("status","Active")=="Active" else 1)
            c1,c2 = st.columns(2)
            pf_app  = c1.selectbox("PF Applicable",  ["Yes","No"], index=0 if val("pf_applicable","Yes")=="Yes" else 1)
            esic_app= c2.selectbox("ESIC Applicable",["Yes","No"], index=0 if val("esic_applicable","No")=="Yes" else 1)
            submitted = st.form_submit_button("💾 Save Employee", use_container_width=True)

        if submitted:
            if not ecode or not name:
                st.error("E-Code and Name are required!")
            else:
                new_row = {
                    "ecode":ecode.upper().strip(),"name":name.strip(),
                    "department":dept,"designation":desig,
                    "doj":str(doj) if doj else "","dob":str(dob) if dob else "",
                    "gender":gender,"mobile":mobile,"email":email,"address":address,
                    "father_name":father,"mother_name":mother,"spouse_name":spouse,
                    "nominee_name":nom_name,"nominee_relation":nom_rel,"nominee_dob":str(nom_dob) if nom_dob else "",
                    "bank_name":bank,"account_no":acc,"ifsc":ifsc,
                    "uan":uan,"pf_no":pf_no,"esic_no":esic_no,
                    "shift":shift,"is_open_shift":"Yes" if is_open=="Open" else "No",
                    "gross_salary":gross,"basic":basic_s,"hra":hra_s,"conveyance":conv_s,
                    "special_allowance":spec_s,"medical_allowance":med_s,"food_allowance":food_s,
                    "pf_applicable":pf_app,"esic_applicable":esic_app,
                    "status":emp_status,"exit_date":""
                }
                df = load_employees()
                if mode == "Edit Existing Employee":
                    df = df[df["ecode"] != ecode.upper().strip()]
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_employees(df)
                st.success(f"✅ Employee {name} ({ecode}) saved!")
                st.rerun()

    with tab3:
        st.markdown("#### 📤 Bulk Import via Excel/CSV")
        st.info("**Required columns:** ecode, name, department, designation, doj, gross_salary, basic, shift")
        st.download_button("📥 Download Import Template", pd.DataFrame(columns=EMPLOYEE_COLUMNS).to_csv(index=False), "employee_template.csv","text/csv")
        uploaded = st.file_uploader("Upload CSV/Excel", type=["csv","xlsx"])
        if uploaded:
            imp = pd.read_csv(uploaded,dtype=str) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded,dtype=str)
            st.dataframe(imp.head(10), use_container_width=True)
            if st.button("✅ Confirm Import"):
                df = load_employees()
                for _, row in imp.iterrows():
                    ec = str(row.get("ecode","")).upper().strip()
                    if ec and ec in df["ecode"].values:
                        df = df[df["ecode"]!=ec]
                df = pd.concat([df, imp], ignore_index=True)
                save_employees(df)
                st.success(f"✅ {len(imp)} employees imported!")
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: ATTENDANCE
# ══════════════════════════════════════════════════════════════════════════════

elif PAGE == "attendance":
    config = load_config()
    emp_df = load_employees()
    att_df = load_attendance()

    st.markdown('<div class="page-header"><h1>🕐 Attendance Management</h1><p>Track daily attendance, punch details, overtime, and apply attendance rules</p></div>', unsafe_allow_html=True)
    tab1,tab2,tab3,tab4 = st.tabs(["📤 Upload / Enter Attendance","📋 View & Edit","⚠️ Missing Punches","📊 Analytics"])

    with tab1:
        st.markdown("### Upload Punch Data")
        st.info("**Template Columns:** ecode, date (YYYY-MM-DD), in_time (HH:MM), out_time (HH:MM)")
        tmpl = pd.DataFrame({"ecode":["EMP001","EMP002"],"date":["2024-01-15","2024-01-15"],"in_time":["09:05","09:30"],"out_time":["18:35","18:00"]})
        st.download_button("📥 Download Template", tmpl.to_csv(index=False), "attendance_template.csv","text/csv")

        uploaded = st.file_uploader("Upload Attendance File (CSV/Excel)", type=["csv","xlsx"])
        if uploaded:
            raw = pd.read_csv(uploaded,dtype=str) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded,dtype=str)
            st.markdown(f"**Preview: {len(raw)} records**")
            st.dataframe(raw.head(10), use_container_width=True)

            if st.button("⚙️ Process & Calculate", use_container_width=True):
                with st.spinner("Processing..."):
                    processed = []
                    for _, row in raw.iterrows():
                        ec  = str(row.get("ecode","")).upper().strip()
                        dt  = str(row.get("date","")).strip()
                        in_t= str(row.get("in_time","")).strip()
                        out_t=str(row.get("out_time","")).strip()
                        er  = emp_df[emp_df["ecode"]==ec]
                        if er.empty: continue
                        emp     = er.iloc[0]
                        shift   = emp.get("shift", config["shifts"]["fixed"][0]["name"])
                        try:    day_name = datetime.strptime(dt,"%Y-%m-%d").strftime("%A")
                        except: day_name = ""
                        calc = calculate_working_hours(in_t, out_t, shift, config)
                        processed.append({"ecode":ec,"name":emp.get("name",""),"date":dt,"day":day_name,
                            "shift":shift,"in_time":in_t,"out_time":out_t,
                            "working_hours":calc["working_hours"],"overtime_hours":calc["overtime_hours"],
                            "early_going_minutes":calc["early_going_minutes"],
                            "late_entry_minutes":calc["late_entry_minutes"],"status":calc["status"],"remarks":""})

                    new_att = pd.DataFrame(processed)
                    if config["attendance"]["sandwich_rule"] and not new_att.empty:
                        results = []
                        for _, grp in new_att.groupby("ecode"):
                            results.append(apply_sandwich_rule(grp, config))
                        new_att = pd.concat(results, ignore_index=True)

                    existing = load_attendance()
                    if not existing.empty:
                        keys = new_att[["ecode","date"]].apply(tuple,axis=1)
                        ex_keys = existing[["ecode","date"]].apply(tuple,axis=1)
                        existing = existing[~ex_keys.isin(keys)]
                    final = pd.concat([existing, new_att], ignore_index=True)
                    save_attendance(final)
                    st.success(f"✅ {len(new_att)} records processed!")
                    st.dataframe(new_att, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("### ✏️ Manual Entry")
        with st.form("manual_att"):
            ec_opts = emp_df["ecode"].tolist() if not emp_df.empty else []
            c1,c2,c3 = st.columns(3)
            m_ec   = c1.selectbox("Employee",ec_opts) if ec_opts else c1.text_input("E-Code")
            m_date = c2.date_input("Date", value=date.today())
            m_status=c3.selectbox("Status",["Present","Absent","Half Day","Week Off","Holiday","On Leave"])
            c1,c2  = st.columns(2)
            m_in   = c1.text_input("IN Time","09:00")
            m_out  = c2.text_input("OUT Time","18:00")
            m_rem  = st.text_input("Remarks","")
            if st.form_submit_button("💾 Save", use_container_width=True):
                er = emp_df[emp_df["ecode"]==m_ec]
                if not er.empty:
                    emp   = er.iloc[0]
                    shift = emp.get("shift","")
                    calc  = calculate_working_hours(m_in, m_out, shift, config)
                    try:    dn = m_date.strftime("%A")
                    except: dn = ""
                    nr = {"ecode":m_ec,"name":emp.get("name",""),"date":str(m_date),"day":dn,"shift":shift,
                          "in_time":m_in,"out_time":m_out,
                          "working_hours":calc["working_hours"] if m_status=="Present" else 0,
                          "overtime_hours":calc["overtime_hours"] if m_status=="Present" else 0,
                          "early_going_minutes":calc["early_going_minutes"],
                          "late_entry_minutes":calc["late_entry_minutes"],
                          "status":m_status,"remarks":m_rem}
                    df = load_attendance()
                    df = df[~((df["ecode"]==m_ec)&(df["date"]==str(m_date)))]
                    df = pd.concat([df, pd.DataFrame([nr])], ignore_index=True)
                    save_attendance(df)
                    st.success("✅ Saved!")

    with tab2:
        st.markdown("### View Attendance Records")
        c1,c2,c3,c4 = st.columns(4)
        sel_month = c1.selectbox("Month", MONTHS, index=date.today().month-1)
        sel_year  = c2.number_input("Year", value=date.today().year, min_value=2020, max_value=2030)
        ec_opts2  = ["All"]+sorted(emp_df["ecode"].tolist()) if not emp_df.empty else ["All"]
        sel_emp   = c3.selectbox("Employee", ec_opts2)
        sel_status= c4.selectbox("Status Filter",["All","Present","Absent","Missing Punch","Half Day"])

        if not att_df.empty:
            att_df["date"] = pd.to_datetime(att_df["date"], errors="coerce")
            mn = MONTHS.index(sel_month)+1
            filt = att_df[(att_df["date"].dt.month==mn)&(att_df["date"].dt.year==int(sel_year))]
            if sel_emp!="All": filt = filt[filt["ecode"]==sel_emp]
            if sel_status!="All": filt = filt[filt["status"].str.contains(sel_status,na=False)]
            filt = filt.sort_values(["ecode","date"])
            filt["date"] = filt["date"].dt.strftime("%Y-%m-%d")
            st.markdown(f"**{len(filt)} records**")
            if not filt.empty:
                s1,s2,s3,s4 = st.columns(4)
                s1.metric("Present", len(filt[filt["status"]=="Present"]))
                s2.metric("Absent",  len(filt[filt["status"]=="Absent"]))
                s3.metric("Total OT hrs", round(pd.to_numeric(filt["overtime_hours"],errors="coerce").sum(),2))
                s4.metric("Late Entries", len(filt[pd.to_numeric(filt["late_entry_minutes"],errors="coerce")>0]))
            st.dataframe(filt[["ecode","name","date","day","shift","in_time","out_time","working_hours","overtime_hours","late_entry_minutes","early_going_minutes","status","remarks"]], use_container_width=True, hide_index=True)
            st.download_button("📥 Download", filt.to_csv(index=False), f"attendance_{sel_month}_{sel_year}.csv","text/csv")
        else:
            st.info("No records yet.")

    with tab3:
        st.markdown("### ⚠️ Missing Punch Details")
        c1,c2 = st.columns(2)
        fdate = c1.date_input("Filter Date", value=date.today())
        mtype = c2.selectbox("Type",["All Missing","Missing IN Punch","Missing OUT Punch"])

        if not att_df.empty:
            att_df["date"] = pd.to_datetime(att_df["date"], errors="coerce")
            miss = att_df[att_df["status"].str.contains("Missing",na=False)]
            if mtype=="Missing IN Punch":
                miss = att_df[att_df["in_time"].isna()|(att_df["in_time"]=="")]
            elif mtype=="Missing OUT Punch":
                miss = att_df[att_df["out_time"].isna()|(att_df["out_time"]=="")]
            miss = miss[miss["date"].dt.date==fdate]
            st.markdown(f"**{len(miss)} missing on {fdate}**")
            if not miss.empty:
                st.dataframe(miss[["ecode","name","date","shift","in_time","out_time","status"]], use_container_width=True, hide_index=True)
                st.markdown("#### ✏️ Fix Punch")
                with st.form("fix_punch"):
                    fx_ec  = st.selectbox("Employee", miss["ecode"].tolist())
                    fc1,fc2= st.columns(2)
                    fx_in  = fc1.text_input("IN Time","09:00")
                    fx_out = fc2.text_input("OUT Time","18:00")
                    fx_rem = st.text_input("Remarks","Manual entry by HR")
                    if st.form_submit_button("✅ Update", use_container_width=True):
                        df = load_attendance()
                        df["date"] = pd.to_datetime(df["date"],errors="coerce")
                        mask = (df["ecode"]==fx_ec)&(df["date"].dt.date==fdate)
                        er2  = emp_df[emp_df["ecode"]==fx_ec]
                        if not er2.empty:
                            calc = calculate_working_hours(fx_in, fx_out, er2.iloc[0].get("shift",""), config)
                            df.loc[mask,"in_time"]             = fx_in
                            df.loc[mask,"out_time"]            = fx_out
                            df.loc[mask,"working_hours"]       = calc["working_hours"]
                            df.loc[mask,"overtime_hours"]      = calc["overtime_hours"]
                            df.loc[mask,"late_entry_minutes"]  = calc["late_entry_minutes"]
                            df.loc[mask,"early_going_minutes"] = calc["early_going_minutes"]
                            df.loc[mask,"status"]  = "Present"
                            df.loc[mask,"remarks"] = fx_rem
                            df["date"] = df["date"].dt.strftime("%Y-%m-%d")
                            save_attendance(df)
                            st.success("✅ Updated!")
                            st.rerun()
            else:
                st.success("✅ No missing punches on this date!")
        else:
            st.info("No attendance data.")

    with tab4:
        st.markdown("### 📊 Attendance Analytics")
        if att_df.empty:
            st.info("No data to analyze.")
        else:
            att_df["date"]                = pd.to_datetime(att_df["date"],errors="coerce")
            att_df["late_entry_minutes"]  = pd.to_numeric(att_df["late_entry_minutes"],errors="coerce").fillna(0)
            att_df["early_going_minutes"] = pd.to_numeric(att_df["early_going_minutes"],errors="coerce").fillna(0)
            att_df["overtime_hours"]      = pd.to_numeric(att_df["overtime_hours"],errors="coerce").fillna(0)
            att_df["working_hours"]       = pd.to_numeric(att_df["working_hours"],errors="coerce").fillna(0)

            c1,c2 = st.columns(2)
            an_month = c1.selectbox("Month", MONTHS, index=date.today().month-1, key="an_m")
            an_year  = c2.number_input("Year", value=date.today().year, min_value=2020, max_value=2030, key="an_y")
            mn2 = MONTHS.index(an_month)+1
            mdata = att_df[(att_df["date"].dt.month==mn2)&(att_df["date"].dt.year==int(an_year))]

            if mdata.empty:
                st.warning("No data for selected period.")
            else:
                col1,col2 = st.columns(2)
                with col1:
                    late_df = mdata[mdata["late_entry_minutes"]>0].groupby("name")["late_entry_minutes"].sum().reset_index().sort_values("late_entry_minutes",ascending=False).head(10)
                    if not late_df.empty:
                        fig = px.bar(late_df,x="name",y="late_entry_minutes",title="🕐 Top 10 Late Entries (Min)",color_discrete_sequence=["#e53935"])
                        fig.update_layout(height=300,paper_bgcolor="white",plot_bgcolor="white")
                        st.plotly_chart(fig,use_container_width=True)
                with col2:
                    ot_df = mdata[mdata["overtime_hours"]>0].groupby("name")["overtime_hours"].sum().reset_index().sort_values("overtime_hours",ascending=False).head(10)
                    if not ot_df.empty:
                        fig2 = px.bar(ot_df,x="name",y="overtime_hours",title="⏰ Top 10 Overtime Hours",color_discrete_sequence=["#2e7d32"])
                        fig2.update_layout(height=300,paper_bgcolor="white",plot_bgcolor="white")
                        st.plotly_chart(fig2,use_container_width=True)

                early_df = mdata[mdata["early_going_minutes"]>0].groupby("name")["early_going_minutes"].sum().reset_index().sort_values("early_going_minutes",ascending=False).head(10)
                if not early_df.empty:
                    fig3 = px.bar(early_df,x="name",y="early_going_minutes",title="🏃 Early Going (Min)",color_discrete_sequence=["#f57c00"])
                    fig3.update_layout(height=300,paper_bgcolor="white",plot_bgcolor="white")
                    st.plotly_chart(fig3,use_container_width=True)

                summary = mdata.groupby(["ecode","name"]).agg(
                    present_days=("status", lambda x:(x=="Present").sum()),
                    absent_days =("status", lambda x:(x=="Absent").sum()),
                    total_hours =("working_hours","sum"),
                    total_ot    =("overtime_hours","sum"),
                    total_late  =("late_entry_minutes","sum"),
                    total_early =("early_going_minutes","sum")
                ).reset_index()
                st.markdown("#### 📋 Employee Summary")
                st.dataframe(summary, use_container_width=True, hide_index=True)
                st.download_button("📥 Download Summary", summary.to_csv(index=False), f"att_summary_{an_month}_{an_year}.csv","text/csv")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: PAYROLL
# ══════════════════════════════════════════════════════════════════════════════

elif PAGE == "payroll":
    config = load_config()
    emp_df = load_employees()
    att_df = load_attendance()

    st.markdown('<div class="page-header"><h1>💰 Payroll Management</h1><p>Calculate monthly salary, PF, ESIC, overtime and generate payslips</p></div>', unsafe_allow_html=True)
    tab1,tab2,tab3 = st.tabs(["🧮 Run Payroll","📄 Payslip Generator","📊 Payroll Reports"])

    with tab1:
        st.markdown("### Run Monthly Payroll")
        c1,c2 = st.columns(2)
        sel_month = c1.selectbox("Month", MONTHS, index=date.today().month-2 if date.today().month>1 else 0)
        sel_year  = c2.number_input("Year", value=date.today().year, min_value=2020, max_value=2030)
        month_num = MONTHS.index(sel_month)+1
        _, total_days = calendar.monthrange(int(sel_year), month_num)
        week_off  = config["attendance"]["week_off"]
        working_days = sum(1 for d in range(1, total_days+1) if date(int(sel_year), month_num, d).strftime("%A") != week_off)
        st.info(f"📅 **{sel_month} {sel_year}** | Total Days: {total_days} | Working Days: {working_days} (excl. {week_off}s)")

        if st.button("⚙️ Calculate Payroll for All Employees", use_container_width=True):
            if emp_df.empty:
                st.error("No employees found!")
            elif att_df.empty:
                st.error("No attendance data found!")
            else:
                with st.spinner("Calculating..."):
                    att_copy = att_df.copy()
                    att_copy["date"] = pd.to_datetime(att_copy["date"],errors="coerce")
                    month_att = att_copy[(att_copy["date"].dt.month==month_num)&(att_copy["date"].dt.year==int(sel_year))]
                    active = emp_df[emp_df["status"]=="Active"] if "status" in emp_df.columns else emp_df
                    results = []
                    for _, emp in active.iterrows():
                        ec = emp["ecode"]
                        ea = month_att[month_att["ecode"]==ec]
                        present = len(ea[ea["status"]=="Present"])
                        ot_hrs  = pd.to_numeric(ea["overtime_hours"],errors="coerce").sum()
                        results.append(calculate_payroll(emp, present, working_days, ot_hrs, config))
                    pr_df = pd.DataFrame(results)
                    st.session_state[f"payroll_{sel_month}_{sel_year}"] = pr_df
                    pr_path = os.path.join(DATA_DIR, f"payroll_{sel_month}_{sel_year}.csv")
                    pr_df.to_csv(pr_path, index=False)
                    st.success(f"✅ Payroll calculated for {len(pr_df)} employees!")
                    s1,s2,s3,s4 = st.columns(4)
                    s1.metric("Total Gross",       f"₹{pr_df['earned_gross'].sum():,.0f}")
                    s2.metric("Total PF Employer", f"₹{pr_df['pf_employer'].sum():,.0f}")
                    s3.metric("Total OT Pay",      f"₹{pr_df['overtime_pay'].sum():,.0f}")
                    s4.metric("Total Net Pay",     f"₹{pr_df['net_pay'].sum():,.0f}")
                    st.dataframe(pr_df, use_container_width=True, hide_index=True)
                    st.download_button("📥 Download Payroll", pr_df.to_csv(index=False), f"payroll_{sel_month}_{sel_year}.csv","text/csv")

    with tab2:
        st.markdown("### 📄 Generate Payslip")
        c1,c2,c3 = st.columns(3)
        ps_month = c1.selectbox("Month", MONTHS, index=date.today().month-2 if date.today().month>1 else 0, key="ps_m")
        ps_year  = c2.number_input("Year", value=date.today().year, key="ps_y", min_value=2020, max_value=2030)
        ec_opts  = emp_df["ecode"].tolist() if not emp_df.empty else []
        ps_ec    = c3.selectbox("Employee E-Code", ec_opts) if ec_opts else c3.text_input("E-Code")

        if st.button("🖨️ Generate Payslip", use_container_width=True):
            pk   = f"payroll_{ps_month}_{ps_year}"
            prp  = os.path.join(DATA_DIR, f"payroll_{ps_month}_{ps_year}.csv")
            pr_df= st.session_state.get(pk) or (pd.read_csv(prp) if os.path.exists(prp) else None)
            if pr_df is None:
                st.error("Please run payroll first!")
            else:
                emp_data = pr_df[pr_df["ecode"]==ps_ec]
                if emp_data.empty:
                    st.error("No payroll data for this employee!")
                else:
                    p  = emp_data.iloc[0]
                    ei = emp_df[emp_df["ecode"]==ps_ec]
                    e  = ei.iloc[0] if not ei.empty else {}
                    def eg(k): return e.get(k,"") if hasattr(e,"get") else ""
                    st.markdown(f"""
                    <div style="max-width:700px;margin:0 auto;font-family:'Segoe UI',sans-serif;border:1px solid #ddd;border-radius:12px;overflow:hidden;">
                        <div style="background:linear-gradient(135deg,#1a237e,#3949ab);color:white;padding:24px;">
                            <h2 style="margin:0;font-size:22px;">{config['company']['name']}</h2>
                            <p style="margin:4px 0;opacity:0.8;">SALARY SLIP — {ps_month.upper()} {ps_year}</p>
                        </div>
                        <div style="padding:20px;background:#f8f9fa;">
                            <table style="width:100%;font-size:14px;">
                                <tr><td><b>Employee:</b> {p.get('name','')}</td><td><b>E-Code:</b> {p.get('ecode','')}</td></tr>
                                <tr><td><b>Department:</b> {eg('department')}</td><td><b>Designation:</b> {eg('designation')}</td></tr>
                                <tr><td><b>Bank:</b> {eg('bank_name')}</td><td><b>Account:</b> {eg('account_no')}</td></tr>
                                <tr><td><b>UAN:</b> {eg('uan')}</td><td><b>Days Worked:</b> {p.get('present_days',0)}</td></tr>
                            </table>
                        </div>
                        <div style="display:flex;padding:0 20px 20px;">
                            <div style="flex:1;margin-right:12px;">
                                <h4 style="color:#1a237e;border-bottom:2px solid #3949ab;padding-bottom:6px;">💚 EARNINGS</h4>
                                <table style="width:100%;font-size:13px;">
                                    <tr><td>Basic</td><td align="right">₹{p.get('earned_basic',0):,.2f}</td></tr>
                                    <tr><td>HRA</td><td align="right">₹{p.get('earned_hra',0):,.2f}</td></tr>
                                    <tr><td>Conveyance</td><td align="right">₹{p.get('earned_conveyance',0):,.2f}</td></tr>
                                    <tr><td>Special Allowance</td><td align="right">₹{p.get('earned_special',0):,.2f}</td></tr>
                                    <tr><td>Medical</td><td align="right">₹{p.get('earned_medical',0):,.2f}</td></tr>
                                    <tr><td>Food</td><td align="right">₹{p.get('earned_food',0):,.2f}</td></tr>
                                    <tr><td>Overtime Pay</td><td align="right">₹{p.get('overtime_pay',0):,.2f}</td></tr>
                                    <tr style="font-weight:bold;border-top:1px solid #ddd;">
                                        <td>Gross Earned</td><td align="right">₹{p.get('earned_gross',0):,.2f}</td>
                                    </tr>
                                </table>
                            </div>
                            <div style="flex:1;margin-left:12px;">
                                <h4 style="color:#c62828;border-bottom:2px solid #e53935;padding-bottom:6px;">❤️ DEDUCTIONS</h4>
                                <table style="width:100%;font-size:13px;">
                                    <tr><td>PF Employee ({config['pf']['employee_percentage']}%)</td><td align="right">₹{p.get('pf_employee',0):,.2f}</td></tr>
                                    <tr><td>ESIC Employee</td><td align="right">₹{p.get('esic_employee',0):,.2f}</td></tr>
                                    <tr style="font-weight:bold;border-top:1px solid #ddd;">
                                        <td>Total Deductions</td><td align="right">₹{p.get('total_deductions',0):,.2f}</td>
                                    </tr>
                                </table>
                                <br/>
                                <h4 style="color:#1a237e;border-bottom:2px solid #3949ab;padding-bottom:6px;">🏢 EMPLOYER CONTRIBUTION</h4>
                                <table style="width:100%;font-size:13px;">
                                    <tr><td>PF Employer ({config['pf']['employer_percentage']}%)</td><td align="right">₹{p.get('pf_employer',0):,.2f}</td></tr>
                                    <tr><td>EPS</td><td align="right">₹{p.get('eps',0):,.2f}</td></tr>
                                    <tr><td>ESIC Employer</td><td align="right">₹{p.get('esic_employer',0):,.2f}</td></tr>
                                </table>
                            </div>
                        </div>
                        <div style="background:linear-gradient(135deg,#1a237e,#3949ab);color:white;padding:16px 20px;text-align:center;">
                            <h3 style="margin:0;font-size:20px;">💵 NET PAY: ₹{p.get('net_pay',0):,.2f}</h3>
                        </div>
                        <div style="padding:12px 20px;background:#f8f9fa;font-size:11px;color:#777;text-align:center;">
                            Computer generated payslip. Generated on {date.today()}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    with tab3:
        st.markdown("### 📊 Payroll Reports")
        pr_files = [f for f in os.listdir(DATA_DIR) if f.startswith("payroll_") and f.endswith(".csv")]
        if not pr_files:
            st.info("No payroll data. Run payroll first.")
        else:
            sel_file = st.selectbox("Select Period", pr_files)
            rdf = pd.read_csv(os.path.join(DATA_DIR, sel_file))
            r1,r2,r3,r4 = st.columns(4)
            r1.metric("Employees", len(rdf))
            r2.metric("Total Gross",    f"₹{pd.to_numeric(rdf['earned_gross'],errors='coerce').sum():,.0f}")
            r3.metric("Total PF Both",  f"₹{(pd.to_numeric(rdf['pf_employee'],errors='coerce')+pd.to_numeric(rdf['pf_employer'],errors='coerce')).sum():,.0f}")
            r4.metric("Total Net Pay",  f"₹{pd.to_numeric(rdf['net_pay'],errors='coerce').sum():,.0f}")
            col1,col2 = st.columns(2)
            with col1:
                fig = px.bar(rdf.sort_values("net_pay",ascending=False).head(15),x="name",y="net_pay",title="Top 15 Earners",color_discrete_sequence=["#1a237e"])
                fig.update_layout(height=350,paper_bgcolor="white",plot_bgcolor="white")
                st.plotly_chart(fig,use_container_width=True)
            with col2:
                fig2 = px.scatter(rdf,x="present_days",y="net_pay",hover_data=["name"],title="Days vs Net Pay",color_discrete_sequence=["#3949ab"])
                fig2.update_layout(height=350,paper_bgcolor="white",plot_bgcolor="white")
                st.plotly_chart(fig2,use_container_width=True)
            st.dataframe(rdf, use_container_width=True, hide_index=True)
            st.download_button("📥 Download", rdf.to_csv(index=False), sel_file,"text/csv")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: LEAVE MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

elif PAGE == "leaves":
    config   = load_config()
    emp_df   = load_employees()
    leaves_df= load_leaves()

    st.markdown('<div class="page-header"><h1>🌴 Leave Management</h1><p>Manage PL, CL, SL leaves and track balances for all employees</p></div>', unsafe_allow_html=True)
    tab1,tab2,tab3 = st.tabs(["📋 Leave Register","➕ Apply / Approve Leave","📊 Leave Balance"])

    with tab1:
        c1,c2,c3 = st.columns(3)
        lr_months = ["All"]+MONTHS
        lr_month  = c1.selectbox("Month", lr_months)
        lr_year   = c2.number_input("Year", value=date.today().year, min_value=2020, max_value=2030, key="lr_y")
        lr_type   = c3.selectbox("Leave Type",["All","PL","CL","SL"])
        lr_status = st.selectbox("Status",["All","Approved","Pending","Rejected"])

        filt = leaves_df.copy()
        if not filt.empty:
            filt["from_date"] = pd.to_datetime(filt["from_date"],errors="coerce")
            if lr_month!="All":
                filt = filt[filt["from_date"].dt.month == MONTHS.index(lr_month)+1]
            filt = filt[filt["from_date"].dt.year==int(lr_year)]
            if lr_type!="All":   filt = filt[filt["leave_type"]==lr_type]
            if lr_status!="All": filt = filt[filt["status"]==lr_status]
            st.markdown(f"**{len(filt)} records**")
            st.dataframe(filt, use_container_width=True, hide_index=True)
            if not filt.empty:
                st.download_button("📥 Download", filt.to_csv(index=False),"leave_register.csv","text/csv")
        else:
            st.info("No leave records.")

    with tab2:
        cl, cr = st.columns(2)
        with cl:
            st.markdown("#### ➕ Apply Leave")
            ec_opts = emp_df["ecode"].tolist() if not emp_df.empty else []
            with st.form("apply_leave"):
                al_ec   = st.selectbox("Employee", ec_opts) if ec_opts else st.text_input("E-Code")
                al_type = st.selectbox("Leave Type",["PL","CL","SL"])
                al_from = st.date_input("From Date")
                al_to   = st.date_input("To Date")
                al_rsn  = st.text_area("Reason",height=80)
                if st.form_submit_button("Submit", use_container_width=True):
                    if al_to < al_from:
                        st.error("To date cannot be before From date!")
                    else:
                        days = (al_to - al_from).days+1
                        en   = ""
                        if not emp_df.empty:
                            er = emp_df[emp_df["ecode"]==al_ec]
                            if not er.empty: en = er.iloc[0].get("name","")
                        nl = {"ecode":al_ec,"name":en,"leave_type":al_type,
                              "from_date":str(al_from),"to_date":str(al_to),
                              "days":days,"reason":al_rsn,"status":"Pending","applied_on":str(date.today())}
                        ldf = load_leaves()
                        ldf = pd.concat([ldf, pd.DataFrame([nl])], ignore_index=True)
                        save_leaves(ldf)
                        st.success(f"✅ Leave applied for {days} day(s)!")
                        st.rerun()

        with cr:
            st.markdown("#### ✅ Pending Approvals")
            ldf = load_leaves()
            pending = ldf[ldf["status"]=="Pending"] if not ldf.empty else pd.DataFrame()
            if not pending.empty:
                for idx, row in pending.iterrows():
                    with st.expander(f"🔔 {row.get('name','')} ({row.get('ecode','')}) — {row.get('leave_type','')} | {row.get('from_date','')} to {row.get('to_date','')}"):
                        st.write(f"**Days:** {row.get('days','')}")
                        st.write(f"**Reason:** {row.get('reason','')}")
                        b1,b2 = st.columns(2)
                        if b1.button("✅ Approve", key=f"app_{idx}", use_container_width=True):
                            ldf.loc[idx,"status"] = "Approved"; save_leaves(ldf); st.success("Approved!"); st.rerun()
                        if b2.button("❌ Reject",  key=f"rej_{idx}", use_container_width=True):
                            ldf.loc[idx,"status"] = "Rejected"; save_leaves(ldf); st.warning("Rejected!"); st.rerun()
            else:
                st.success("✅ No pending leaves!")

    with tab3:
        st.markdown("#### 📊 Leave Balance Report")
        bal_year = st.number_input("Year", value=date.today().year, min_value=2020, max_value=2030)
        if not emp_df.empty:
            active = emp_df[emp_df["status"]=="Active"] if "status" in emp_df.columns else emp_df
            bals = []
            for _, emp in active.iterrows():
                b = get_leave_balance(emp["ecode"], int(bal_year), config)
                bals.append({"E-Code":emp["ecode"],"Name":emp.get("name",""),"Dept":emp.get("department",""),
                    "PL Entitled":b["pl_entitled"],"PL Taken":b["pl_taken"],"PL Balance":b["pl_balance"],
                    "CL Entitled":b["cl_entitled"],"CL Taken":b["cl_taken"],"CL Balance":b["cl_balance"],
                    "SL Entitled":b["sl_entitled"],"SL Taken":b["sl_taken"],"SL Balance":b["sl_balance"]})
            bdf = pd.DataFrame(bals)
            st.dataframe(bdf, use_container_width=True, hide_index=True)
            st.download_button("📥 Download", bdf.to_csv(index=False), f"leave_balance_{bal_year}.csv","text/csv")
        else:
            st.info("No employee data found.")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: SETTINGS
# ══════════════════════════════════════════════════════════════════════════════

elif PAGE == "settings":
    config = load_config()
    st.markdown('<div class="page-header"><h1>⚙️ Settings & Rules</h1><p>Customize all rules, shifts, salary components, PF, ESIC, leave policies — fully flexible</p></div>', unsafe_allow_html=True)

    tab1,tab2,tab3,tab4,tab5,tab6 = st.tabs(["🏢 Company","⏰ Shifts & Attendance","💰 Salary Components","🏛️ PF & ESIC","🌴 Leave Policy","📋 Raw Config"])

    with tab1:
        with st.form("co_form"):
            cn = st.text_input("Company Name", config["company"]["name"])
            ca = st.text_area("Address",       config["company"].get("address",""))
            if st.form_submit_button("💾 Save", use_container_width=True):
                config["company"]["name"] = cn; config["company"]["address"] = ca
                save_config(config); st.success("✅ Saved!")

    with tab2:
        with st.form("att_form"):
            grace   = st.number_input("Grace Period (Minutes)",    value=int(config["shifts"]["grace_period_minutes"]),    min_value=0, max_value=30)
            ot_thr  = st.number_input("OT Threshold (Min after shift end)", value=int(config["shifts"]["overtime_threshold_minutes"]), min_value=0, max_value=120)
            week_off= st.selectbox("Week Off Day",["Sunday","Saturday","Monday"],index=["Sunday","Saturday","Monday"].index(config["attendance"]["week_off"]))
            sandwich= st.checkbox("Enable Sandwich Rule", value=config["attendance"]["sandwich_rule"])
            min_days= st.number_input("Min Working Days/Week", value=int(config["attendance"]["min_days_per_week"]), min_value=1, max_value=6)
            if st.form_submit_button("💾 Save Attendance Rules", use_container_width=True):
                config["shifts"]["grace_period_minutes"]     = grace
                config["shifts"]["overtime_threshold_minutes"]= ot_thr
                config["attendance"]["week_off"]             = week_off
                config["attendance"]["sandwich_rule"]        = sandwich
                config["attendance"]["min_days_per_week"]    = min_days
                save_config(config); st.success("✅ Saved!")

        st.markdown("---")
        st.markdown("### Fixed Shifts")
        shifts     = config["shifts"]["fixed"]
        upd_shifts = []
        for i, s in enumerate(shifts):
            c1,c2,c3,c4 = st.columns([3,2,2,1])
            sn = c1.text_input("Name",          s["name"],         key=f"sn{i}")
            ss = c2.text_input("Start (HH:MM)", s["start"],        key=f"ss{i}")
            se = c3.text_input("End (HH:MM)",   s["end"],          key=f"se{i}")
            sh = c4.number_input("Hrs",         float(s["total_hours"]), key=f"sh{i}", min_value=0.0)
            upd_shifts.append({"name":sn,"start":ss,"end":se,"total_hours":sh})

        st.markdown("#### ➕ Add New Shift")
        c1,c2,c3,c4 = st.columns([3,2,2,1])
        nsn = c1.text_input("Name","",      key="nsn")
        nss = c2.text_input("Start","09:00",key="nss")
        nse = c3.text_input("End","18:00",  key="nse")
        nsh = c4.number_input("Hrs",9.0,   key="nsh")
        b1,b2 = st.columns(2)
        if b1.button("💾 Save Shifts", use_container_width=True):
            config["shifts"]["fixed"] = upd_shifts
            if nsn.strip():
                config["shifts"]["fixed"].append({"name":nsn,"start":nss,"end":nse,"total_hours":nsh})
            save_config(config); st.success("✅ Shifts saved!"); st.rerun()
        if b2.button("🗑️ Remove Last Shift", use_container_width=True):
            if config["shifts"]["fixed"]:
                config["shifts"]["fixed"].pop()
                save_config(config); st.warning("Last shift removed!"); st.rerun()

    with tab3:
        st.markdown("### Salary Components")
        comps = config["salary_components"]["components"]
        upd_comps = []
        for i, comp in enumerate(comps):
            with st.expander(f"{'✅' if comp.get('enabled') else '❌'} {comp['name']}", expanded=comp.get("enabled",False)):
                c1,c2,c3 = st.columns(3)
                cname    = c1.text_input("Name",    comp["name"],          key=f"cn{i}")
                cenabled = c2.checkbox("Enabled",   comp.get("enabled",True),  key=f"ce{i}")
                ctaxable = c3.checkbox("Taxable",   comp.get("taxable",True),  key=f"ct{i}")
                ctype    = st.selectbox("Type",["fixed","percentage","calculated"],
                                        index=["fixed","percentage","calculated"].index(comp.get("type","fixed")), key=f"ctype{i}")
                uc = {"name":cname,"type":ctype,"taxable":ctaxable,"enabled":cenabled}
                if ctype=="percentage":
                    cc1,cc2 = st.columns(2)
                    uc["value"]          = cc1.number_input("%", float(comp.get("value",40)), key=f"cpct{i}")
                    uc["percentage_of"]  = cc2.text_input("Of", comp.get("percentage_of","Basic"), key=f"cpof{i}")
                upd_comps.append(uc)

        st.markdown("#### ➕ Add Component")
        with st.form("add_comp"):
            nc1,nc2,nc3 = st.columns(3)
            ncname = nc1.text_input("Name")
            nctype = nc2.selectbox("Type",["fixed","percentage"])
            nctax  = nc3.checkbox("Taxable",True)
            if st.form_submit_button("Add"):
                if ncname:
                    upd_comps.append({"name":ncname,"type":nctype,"taxable":nctax,"enabled":True})

        if st.button("💾 Save Components", use_container_width=True):
            config["salary_components"]["components"] = upd_comps
            save_config(config); st.success("✅ Saved!")

        st.markdown("---")
        st.markdown("### ⏰ Overtime")
        with st.form("ot_form"):
            ot_en   = st.checkbox("OT Enabled",        config["overtime"]["enabled"])
            ot_rate = st.number_input("OT Multiplier", float(config["overtime"]["rate_multiplier"]), min_value=1.0, max_value=3.0, step=0.5)
            ot_base = st.selectbox("OT Base",["Basic","Gross"], index=["Basic","Gross"].index(config["overtime"]["calculation_base"]))
            if st.form_submit_button("💾 Save OT"):
                config["overtime"]["enabled"]          = ot_en
                config["overtime"]["rate_multiplier"]  = ot_rate
                config["overtime"]["calculation_base"] = ot_base
                save_config(config); st.success("✅ Saved!")

    with tab4:
        st.markdown("### 🏛️ PF Configuration")
        with st.form("pf_form"):
            pf_en  = st.checkbox("PF Enabled", config["pf"]["enabled"])
            c1,c2  = st.columns(2)
            pf_emp = c1.number_input("Employee PF %", float(config["pf"]["employee_percentage"]), min_value=0.0, max_value=100.0, step=0.5)
            pf_er  = c2.number_input("Employer PF %", float(config["pf"]["employer_percentage"]), min_value=0.0, max_value=100.0, step=0.5)
            pf_base_opts = ["Basic","Basic + DA","Gross"]
            pf_base = st.selectbox("PF Base", pf_base_opts, index=pf_base_opts.index(config["pf"]["pf_base"]) if config["pf"]["pf_base"] in pf_base_opts else 0)
            pf_cap = st.checkbox("Cap at ₹15,000 Basic", value=config["pf"]["cap_at_15000"])
            st.info("💡 Uncheck = PF on actual Basic (above ₹15,000 too)")
            eps_pct= st.number_input("EPS %", float(config["pf"]["eps_percentage"]), min_value=0.0, max_value=20.0, step=0.5)
            if st.form_submit_button("💾 Save PF", use_container_width=True):
                config["pf"]["enabled"]             = pf_en
                config["pf"]["employee_percentage"] = pf_emp
                config["pf"]["employer_percentage"] = pf_er
                config["pf"]["pf_base"]             = pf_base
                config["pf"]["cap_at_15000"]        = pf_cap
                config["pf"]["eps_percentage"]      = eps_pct
                save_config(config); st.success("✅ PF Saved!")

        st.markdown("---")
        st.markdown("### 🏥 ESIC Configuration")
        with st.form("esic_form"):
            esic_en  = st.checkbox("ESIC Enabled", config["esic"]["enabled"])
            c1,c2    = st.columns(2)
            esic_emp = c1.number_input("Employee %", float(config["esic"]["employee_percentage"]), min_value=0.0, max_value=10.0, step=0.25)
            esic_er  = c2.number_input("Employer %", float(config["esic"]["employer_percentage"]), min_value=0.0, max_value=10.0, step=0.25)
            esic_ceil= st.number_input("Wage Ceiling (₹)", int(config["esic"]["wage_ceiling"]), min_value=0, step=1000)
            if st.form_submit_button("💾 Save ESIC", use_container_width=True):
                config["esic"]["enabled"]             = esic_en
                config["esic"]["employee_percentage"] = esic_emp
                config["esic"]["employer_percentage"] = esic_er
                config["esic"]["wage_ceiling"]        = esic_ceil
                save_config(config); st.success("✅ ESIC Saved!")

        st.markdown("---")
        st.markdown("### TDS & Professional Tax")
        st.info("Both are currently **disabled** as per your requirement.")
        with st.form("tds_pt"):
            tds_on = st.checkbox("Enable TDS",               config["tds"]["enabled"])
            pt_on  = st.checkbox("Enable Professional Tax",  config["professional_tax"]["enabled"])
            if st.form_submit_button("Save"):
                config["tds"]["enabled"]             = tds_on
                config["professional_tax"]["enabled"]= pt_on
                save_config(config); st.success("✅ Saved!")

    with tab5:
        with st.form("leave_form"):
            st.markdown("#### Privilege Leave (PL)")
            c1,c2,c3 = st.columns(3)
            pl_a  = c1.number_input("Annual Days", int(config["leave"]["pl"]["annual"]), min_value=0)
            pl_cf = c2.checkbox("Carry Forward",   config["leave"]["pl"]["carry_forward"])
            pl_mc = c3.number_input("Max CF Days", int(config["leave"]["pl"]["max_carry_forward"]), min_value=0)
            st.markdown("#### Casual Leave (CL)")
            c1,c2 = st.columns(2)
            cl_a  = c1.number_input("Annual Days", int(config["leave"]["cl"]["annual"]), min_value=0, key="cl_a")
            cl_cf = c2.checkbox("Carry Forward",   config["leave"]["cl"]["carry_forward"], key="cl_cf")
            st.markdown("#### Sick Leave (SL)")
            c1,c2 = st.columns(2)
            sl_a  = c1.number_input("Annual Days", int(config["leave"]["sl"]["annual"]), min_value=0, key="sl_a")
            sl_cf = c2.checkbox("Carry Forward",   config["leave"]["sl"]["carry_forward"], key="sl_cf")
            if st.form_submit_button("💾 Save Leave Policy", use_container_width=True):
                config["leave"]["pl"]["annual"]        = pl_a
                config["leave"]["pl"]["carry_forward"] = pl_cf
                config["leave"]["pl"]["max_carry_forward"] = pl_mc
                config["leave"]["cl"]["annual"]        = cl_a
                config["leave"]["cl"]["carry_forward"] = cl_cf
                config["leave"]["sl"]["annual"]        = sl_a
                config["leave"]["sl"]["carry_forward"] = sl_cf
                save_config(config); st.success("✅ Leave policy saved!")

    with tab6:
        st.warning("⚠️ Advanced users only. Edit JSON carefully!")
        edited = st.text_area("Config JSON", json.dumps(config, indent=2), height=500)
        if st.button("💾 Save Raw Config", use_container_width=True):
            try:
                save_config(json.loads(edited))
                st.success("✅ Saved!"); st.rerun()
            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON: {e}")
