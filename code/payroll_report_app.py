"""
payroll_report_app.py — the quarter at a glance, for someone who never opens a terminal.

Every Friday since September the office manager at Salt City Coffee has downloaded
a payroll export from the Assignment 04 app; before that she typed the same file
by hand. The owner now wants to know where the hours went this quarter, the
accountant wants pay by month and department, and the manager wants to see who
has been missing shifts. This page answers all three from the pile of exports.

Same shape as Assignment 04: the page *assembles* the pipeline — one call to
`build_history` does the cleaning — and then shows the reports, filtered by the
department and dates the user picks.

Run it:  Run and Debug -> "Streamlit Run: Current File"
Test it: pytest tests/test_pipeline.py -k app
"""
# --- The page ---------------------------------------------------------------------
#
# No scaffolding. Every function this page needs already exists in the payroll
# package, and every widget it needs you used in Assignments 03 and 04 — plus two
# new ones, st.date_input and st.bar_chart. README Step 8 has the exact widgets,
# keys and labels; the tests in tests/test_pipeline.py -k app check them.
#
# The shape, in words:
#
#   title and a sentence of instructions
#   roster   <- load_employees()                           (fixed; not uploaded)
#   uploads  <- st.file_uploader, key="exports", accept_multiple_files=True
#               (an empty list until files are chosen)
#   if there are uploads:
#       history <- build_history([load_export(u) for u in uploads], roster)
#       st.warning naming any employeeid with no department (not on the roster);
#           the reports below use only the rows that matched
#       st.selectbox, key="department": "All" plus each department
#       st.date_input, key="dates": a (start, end) range, defaulting to the first
#           and last pay_date — compare against pay_date.dt.date to filter
#       the selection as a subheader
#       four st.metric cards in st.columns(4): Weeks, Employees, Total hours,
#           Total gross pay — counts are .nunique(), totals are .sum()
#       st.bar_chart of pay_by_month(selected), with month as the x axis
#       st.dataframe of summarize_employees(selected)
#       st.dataframe of hours_grid(selected), then of missed_weeks(that grid)
#       st.download_button, key="download": pay_by_month(...).to_csv(index=False)
#
# What the page does NOT do: cleaning, grouping, pivoting. If you find yourself
# writing a groupby or a pivot_table here, that logic belongs in the package.

import streamlit as st
from payroll import (load_employees, load_export, build_history,
                     pay_by_month, summarize_employees, hours_grid, missed_weeks)

st.title("Salt City Coffee — Quarterly Payroll Report")
roster = load_employees()
uploads = st.file_uploader(
    "Upload payroll exports (one or more)",
    accept_multiple_files=True,
    key="exports"
)
if uploads:
    history = build_history([load_export(u) for u in uploads], roster)
    missing_dept = history["department"].isna()
    if missing_dept.any():
        raw_missing_ids = history.loc[missing_dept, "employeeid"].unique()
        st.warning(f"Warning: IDs have no department: {', '.join(raw_missing_ids)}")

    filtered_history = history.dropna(subset=["department"])

    depts = ["All"] + sorted(filtered_history["department"].unique())
    selected_dept = st.selectbox("Department", depts)

    min_date = filtered_history["pay_date"].dt.date.min()
    max_date = filtered_history["pay_date"].dt.date.max()
    selected_dates = st.date_input("Dates", [min_date, max_date])

    if selected_dept != "All":
        filtered_history = filtered_history[
            filtered_history["department"] == selected_dept
        ]
    filtered_history = filtered_history[
        (filtered_history["pay_date"].dt.date >= selected_dates[0]) &
        (filtered_history["pay_date"].dt.date <= selected_dates[1])
    ]

    st.subheader(
        f"Payroll Report for {selected_dept}, "
        f"{selected_dates[0]} to {selected_dates[1]}"
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Weeks", filtered_history["week_ending"].nunique())
    col2.metric("Employees", filtered_history["employee_id"].nunique())
    col3.metric("Total hours", f"{filtered_history['hours_worked'].sum():,.2f}")
    col4.metric("Total gross pay", f"${filtered_history['gross_pay'].sum():,.2f}")

    st.bar_chart(pay_by_month(filtered_history).set_index("month"))

    st.dataframe(summarize_employees(filtered_history))

    grid = hours_grid(filtered_history)
    st.dataframe(grid)
    st.dataframe(missed_weeks(grid))

    csv = pay_by_month(filtered_history).to_csv(index=False)
    st.download_button("Download CSV", data=csv, file_name="pay_by_month.csv")
