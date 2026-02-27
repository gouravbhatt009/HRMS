{
  "company": {
    "name": "My Company",
    "address": "",
    "logo": ""
  },
  "shifts": {
    "fixed": [
      {"name": "Morning 9-6", "start": "09:00", "end": "18:00", "total_hours": 9.0},
      {"name": "Morning 9-6:30", "start": "09:00", "end": "18:30", "total_hours": 9.5},
      {"name": "Late 10-6:30", "start": "10:00", "end": "18:30", "total_hours": 8.5},
      {"name": "Long 9-9", "start": "09:00", "end": "21:00", "total_hours": 12.0}
    ],
    "open_shift": true,
    "grace_period_minutes": 5,
    "overtime_threshold_minutes": 30
  },
  "attendance": {
    "week_off": "Sunday",
    "working_days": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"],
    "sandwich_rule": true,
    "min_days_per_week": 3
  },
  "salary_components": {
    "components": [
      {"name": "Basic", "type": "fixed", "taxable": true, "enabled": true},
      {"name": "HRA", "type": "percentage", "percentage_of": "Basic", "value": 40, "taxable": true, "enabled": true},
      {"name": "Conveyance Allowance", "type": "fixed", "taxable": false, "enabled": true},
      {"name": "Special Allowance", "type": "calculated", "taxable": true, "enabled": true},
      {"name": "Medical Allowance", "type": "fixed", "taxable": false, "enabled": false},
      {"name": "Food Allowance", "type": "fixed", "taxable": false, "enabled": false}
    ]
  },
  "pf": {
    "enabled": true,
    "employee_percentage": 12,
    "employer_percentage": 12,
    "pf_base": "Basic",
    "cap_at_15000": false,
    "eps_percentage": 8.33,
    "edli_enabled": true
  },
  "esic": {
    "enabled": false,
    "employee_percentage": 0.75,
    "employer_percentage": 3.25,
    "wage_ceiling": 21000
  },
  "tds": {
    "enabled": false
  },
  "professional_tax": {
    "enabled": false
  },
  "leave": {
    "pl": {
      "annual": 12,
      "carry_forward": true,
      "max_carry_forward": 30,
      "encashable": true
    },
    "cl": {
      "annual": 6,
      "carry_forward": false,
      "max_carry_forward": 0,
      "encashable": false
    },
    "sl": {
      "annual": 6,
      "carry_forward": false,
      "encashable": false
    }
  },
  "overtime": {
    "enabled": true,
    "rate_multiplier": 1.5,
    "calculation_base": "Basic"
  }
}
