import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from utils.risk_engine import calculate_risk_score

from utils.policy_engine import check_expense, POLICIES

from utils.gemini_service import (
    generate_expense_explanation,
    categorize_expense,
    generate_management_summary,
    extract_receipt_details,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="ExpenseGuard AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background-color: #0b0f14;
    }

    [data-testid="stSidebar"] {
        background-color: #11161d;
    }

    .main-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 0px;
    }

    .subtitle {
        color: #9ca3af;
        font-size: 16px;
        margin-bottom: 25px;
    }

    .kpi-card {
        background: #151a22;
        border: 1px solid #252c36;
        border-radius: 14px;
        padding: 20px;
        min-height: 120px;
    }

    .kpi-label {
        color: #9ca3af;
        font-size: 14px;
    }

    .kpi-value {
        font-size: 30px;
        font-weight: 750;
        margin-top: 8px;
    }

    .status-box {
        padding: 18px;
        border-radius: 12px;
        margin: 10px 0;
    }

    .success-box {
        background-color: #123524;
        border: 1px solid #1d6b43;
    }

    .warning-box {
        background-color: #3b2b12;
        border: 1px solid #8b641d;
    }

    .danger-box {
        background-color: #3d171b;
        border: 1px solid #7d2d35;
    }

    .info-box {
        background-color: #14283d;
        border: 1px solid #28547d;
    }

    div[data-testid="stMetric"] {
        background-color: #151a22;
        border: 1px solid #252c36;
        padding: 15px;
        border-radius: 12px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "receipt_details" not in st.session_state:
    st.session_state.receipt_details = None

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "submitted_expenses" not in st.session_state:
    st.session_state.submitted_expenses = []

if "ai_category" not in st.session_state:
    st.session_state.ai_category = None


# ============================================================
# SAMPLE / DATASET
# ============================================================

def load_expense_data():

    try:
        df = pd.read_csv("data/expenses.csv")

        # Make column names consistent
        df.columns = [str(c).strip() for c in df.columns]

        return df

    except Exception:

        # Fallback dataset
        data = [
            ["EXP-001", "Rajat Gera", "Marketing", "Client Meals", 4850, "Review"],
            ["EXP-002", "Aman Sharma", "Finance", "Hotel", 12000, "Review"],
            ["EXP-003", "Priya Mehta", "HR", "Travel", 18500, "Review"],
            ["EXP-004", "Karan Singh", "IT", "Software", 3200, "Approved"],
            ["EXP-005", "Neha Kapoor", "Operations", "Office Supplies", 7500, "Review"],
            ["EXP-006", "Arjun Malhotra", "Finance", "Client Meals", 2800, "Approved"],
            ["EXP-007", "Rajat Gera", "Marketing", "Travel", 4200, "Review"],
            ["EXP-008", "Aman Sharma", "Finance", "Software", 6500, "Approved"],
            ["EXP-009", "Priya Mehta", "HR", "Hotel", 4500, "Approved"],
            ["EXP-010", "Karan Singh", "IT", "Office Supplies", 1800, "Approved"],
            ["EXP-011", "Neha Kapoor", "Operations", "Client Meals", 4200, "Review"],
            ["EXP-012", "Arjun Malhotra", "Marketing", "Client Entertainment", 5200, "Review"],
        ]

        return pd.DataFrame(
            data,
            columns=[
                "Expense_ID",
                "Employee",
                "Department",
                "Category",
                "Amount",
                "Status",
            ],
        )


df = load_expense_data()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown(
    """
    <div style="padding:10px 0 20px 0;">
        <h2 style="margin-bottom:0;">🛡️ ExpenseGuard AI</h2>
        <p style="color:#9ca3af;margin-top:4px;">
            Intelligent Expense Management
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("### Navigation")

page = st.sidebar.radio(
    "",
    [
        "Dashboard",
        "Submit Expense",
        "Approval Center",
        "Policy Center",
    ],
)


st.sidebar.markdown("---")

st.sidebar.markdown("### System Status")

st.sidebar.success("● Gemini AI Online")
st.sidebar.success("● Policy Engine Operational")
st.sidebar.success("● Data Engine Operational")

st.sidebar.markdown("---")

st.sidebar.caption("ExpenseGuard AI")
st.sidebar.caption("Enterprise Expense Intelligence")


# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":

    st.markdown(
        '<div class="main-title">ExpenseGuard AI</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        'AI-assisted expense compliance, risk detection and approval intelligence.'
        '</div>',
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # FILTERS
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        departments = ["All"] + sorted(
            df["Department"].dropna().unique().tolist()
        )

        selected_department = st.selectbox(
            "Department",
            departments,
        )

    with col2:

        categories = ["All"] + sorted(
            df["Category"].dropna().unique().tolist()
        )

        selected_category = st.selectbox(
            "Category",
            categories,
        )

    filtered_df = df.copy()

    if selected_department != "All":
        filtered_df = filtered_df[
            filtered_df["Department"] == selected_department
        ]

    if selected_category != "All":
        filtered_df = filtered_df[
            filtered_df["Category"] == selected_category
        ]

    # --------------------------------------------------------
    # KPI CALCULATIONS
    # --------------------------------------------------------

    total_spend = filtered_df["Amount"].sum()

    review_df = filtered_df[
        filtered_df["Status"].astype(str).str.lower().isin(
            ["review", "pending", "pending review"]
        )
    ]

    pending_amount = review_df["Amount"].sum()

    policy_issues = len(review_df)

    total_records = len(filtered_df)

    approval_rate = (
        (
            len(
                filtered_df[
                    filtered_df["Status"].astype(str).str.lower()
                    == "approved"
                ]
            )
            / total_records
        )
        * 100
        if total_records > 0
        else 0
    )

    # --------------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------------

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.metric(
            "Total Spend",
            f"₹{total_spend:,.0f}",
        )

    with k2:
        st.metric(
            "Pending Review",
            f"₹{pending_amount:,.0f}",
        )

    with k3:
        st.metric(
            "Policy Issues",
            policy_issues,
        )

    with k4:
        st.metric(
            "Approval Rate",
            f"{approval_rate:.1f}%",
        )

    st.markdown("---")

    # --------------------------------------------------------
    # CHARTS
    # --------------------------------------------------------

    chart1, chart2 = st.columns(2)

    with chart1:

        st.markdown("### Spend by Category")

        category_spend = (
            filtered_df.groupby("Category")["Amount"]
            .sum()
            .reset_index()
            .sort_values("Amount", ascending=False)
        )

        fig = px.bar(
            category_spend,
            x="Category",
            y="Amount",
            text_auto=".2s",
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0b0f14",
            plot_bgcolor="#0b0f14",
            margin=dict(l=10, r=10, t=10, b=10),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    with chart2:

        st.markdown("### Expense Status")

        status_counts = (
            filtered_df["Status"]
            .value_counts()
            .reset_index()
        )

        status_counts.columns = ["Status", "Count"]

        fig = px.pie(
            status_counts,
            names="Status",
            values="Count",
            hole=0.55,
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0b0f14",
            margin=dict(l=10, r=10, t=10, b=10),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    # --------------------------------------------------------
    # DEPARTMENT SPENDING
    # --------------------------------------------------------

    st.markdown("### Department Spending")

    department_spend = (
        filtered_df.groupby("Department")["Amount"]
        .sum()
        .reset_index()
        .sort_values("Amount", ascending=False)
    )

    fig = px.bar(
        department_spend,
        x="Department",
        y="Amount",
        text_auto=".2s",
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0b0f14",
        plot_bgcolor="#0b0f14",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    # --------------------------------------------------------
    # EXCEPTIONS
    # --------------------------------------------------------

    st.markdown("### ⚠️ Top Expense Exceptions")

    exceptions = filtered_df[
        filtered_df["Status"].astype(str).str.lower() != "approved"
    ].copy()

    if len(exceptions) > 0:

        exceptions["Issue"] = exceptions.apply(
            lambda row: (
                "Above policy limit"
                if row["Amount"]
                > POLICIES.get(
                    row["Category"],
                    POLICIES["Other"],
                )["limit"]
                else "Policy review required"
            ),
            axis=1,
        )

        display_columns = [
            c
            for c in [
                "Expense_ID",
                "Employee",
                "Department",
                "Category",
                "Amount",
                "Issue",
            ]
            if c in exceptions.columns
        ]

        st.dataframe(
            exceptions[display_columns]
            .sort_values("Amount", ascending=False)
            .head(10),
            hide_index=True,
            use_container_width=True,
        )

    else:

        st.success("No expense exceptions found.")


# ============================================================
# SUBMIT EXPENSE
# ============================================================

elif page == "Submit Expense":

    st.markdown(
        '<div class="main-title">Submit Expense</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        'Submit an expense and let ExpenseGuard AI validate it before approval.'
        '</div>',
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # BASIC INFORMATION
    # --------------------------------------------------------

    st.markdown("### Expense Details")

    col1, col2 = st.columns(2)

    with col1:

        employee = st.text_input(
            "Employee Name",
            placeholder="e.g. Rajat Gera",
        )

        merchant = st.text_input(
            "Merchant",
            placeholder="e.g. Taj Hotel",
        )

        amount = st.number_input(
            "Expense Amount (₹)",
            min_value=0.0,
            step=100.0,
        )

        expense_date = st.date_input(
            "Expense Date",
            value=date.today(),
        )

    with col2:

        department = st.selectbox(
            "Department",
            [
                "Marketing",
                "Finance",
                "HR",
                "IT",
                "Operations",
            ],
        )

        category_options = list(POLICIES.keys())

        if "Air Travel" not in category_options:
            category_options.append("Air Travel")

        expense_category = st.selectbox(
            "Expense Category",
            category_options,
        )

        business_purpose = st.text_area(
            "Business Purpose",
            placeholder="Explain the business reason for this expense...",
        )

        payment_method = st.selectbox(
            "Payment Method",
            [
                "Corporate Card",
                "Personal Card",
                "Cash",
                "UPI",
                "Bank Transfer",
            ],
        )

    # --------------------------------------------------------
    # AI CATEGORY CLASSIFICATION
    # --------------------------------------------------------

    st.markdown("---")
    st.markdown("### 🤖 AI Classification")

    if merchant or business_purpose:

        if st.button(
            "✨ Suggest Category with Gemini",
            use_container_width=True,
        ):

            with st.spinner("Gemini is classifying the expense..."):

                try:

                    suggested = categorize_expense(
                        merchant,
                        business_purpose,
                    )

                    st.session_state.ai_category = suggested

                except Exception as e:

                    st.session_state.ai_category = None

                    st.warning(
                        f"AI classification unavailable: {e}"
                    )

    if st.session_state.ai_category:

        st.info(
            f"Gemini suggested category: "
            f"**{st.session_state.ai_category}**"
        )

        use_ai_category = st.checkbox(
            "Use AI suggested category",
            value=False,
        )

        if use_ai_category:

            expense_category = st.session_state.ai_category

    # --------------------------------------------------------
    # RECEIPT UPLOAD
    # --------------------------------------------------------

    st.markdown("---")
    st.markdown("### 🧾 Receipt")

    receipt = st.file_uploader(
        "Upload Receipt",
        type=["png", "jpg", "jpeg", "pdf"],
        help="Upload a receipt for AI extraction and verification.",
    )

    # ========================================================
    # RECEIPT INTELLIGENCE
    # IMPORTANT: INSIDE SUBMIT EXPENSE ONLY
    # ========================================================

    if receipt:

        st.markdown("### 🔍 Receipt Intelligence")

        st.caption(
            "Gemini AI extracts receipt information and helps compare "
            "it with the submitted expense."
        )

        if st.button(
            "✨ Extract Receipt Details",
            use_container_width=True,
        ):

            with st.spinner(
                "Gemini is analyzing the receipt..."
            ):

                try:

                    # Convert uploaded file into a Gemini Part.
                    from google.genai import types

                    receipt_part = types.Part.from_bytes(
                        data=receipt.getvalue(),
                        mime_type=receipt.type,
                    )

                    extracted = extract_receipt_details(
                        receipt_part
                    )

                    if "error" in extracted:

                        st.error(
                            "Receipt extraction failed. "
                            "The policy engine can still evaluate the expense."
                        )

                        st.session_state.receipt_details = None

                    else:

                        st.session_state.receipt_details = extracted

                        st.success(
                            "Receipt analyzed successfully."
                        )

                except Exception as e:

                    st.session_state.receipt_details = None

                    st.error(
                        f"Receipt analysis error: {e}"
                    )

        # ----------------------------------------------------
        # SHOW EXTRACTED INFORMATION
        # ----------------------------------------------------

        if st.session_state.receipt_details:

            extracted = st.session_state.receipt_details

            st.markdown("#### Extracted Receipt Information")

            c1, c2, c3 = st.columns(3)

            with c1:

                st.metric(
                    "Merchant",
                    extracted.get(
                        "merchant",
                        "Not detected",
                    )
                    or "Not detected",
                )

            with c2:

                receipt_amount = extracted.get(
                    "amount",
                    0,
                )

                try:
                    receipt_amount_display = (
                        f"₹{float(receipt_amount):,.0f}"
                        if receipt_amount
                        else "Not detected"
                    )
                except Exception:
                    receipt_amount_display = str(
                        receipt_amount
                    )

                st.metric(
                    "Receipt Amount",
                    receipt_amount_display,
                )

            with c3:

                st.metric(
                    "Receipt Date",
                    extracted.get(
                        "date",
                        "Not detected",
                    )
                    or "Not detected",
                )

            receipt_display = pd.DataFrame(
                [
                    [
                        "Merchant",
                        extracted.get("merchant", ""),
                    ],
                    [
                        "Date",
                        extracted.get("date", ""),
                    ],
                    [
                        "Amount",
                        extracted.get("amount", ""),
                    ],
                    [
                        "Currency",
                        extracted.get("currency", ""),
                    ],
                    [
                        "Category",
                        extracted.get("category", ""),
                    ],
                    [
                        "Description",
                        extracted.get("description", ""),
                    ],
                ],
                columns=[
                    "Field",
                    "Extracted Value",
                ],
            )

            st.dataframe(
                receipt_display,
                hide_index=True,
                use_container_width=True,
            )

    # --------------------------------------------------------
    # ANALYZE EXPENSE
    # --------------------------------------------------------

    st.markdown("---")

    st.markdown("### 🛡️ Expense Compliance Analysis")

    if st.button(
        "🔎 Analyze Expense",
        type="primary",
        use_container_width=True,
    ):

        if not employee:

            st.error("Please enter employee name.")

        elif not merchant:

            st.error("Please enter merchant name.")

        elif amount <= 0:

            st.error("Please enter a valid expense amount.")

        else:

            receipt_present = receipt is not None

            result = check_expense(
                expense_category,
                amount,
                receipt_present,
            )

            st.session_state.analysis_result = result

            # ------------------------------------------------
            # STATUS
            # ------------------------------------------------

            if result["status"] == "Approved":

                st.markdown(
                    """
                    <div class="status-box success-box">
                        <h3>🟢 Expense Compliant</h3>
                        <p>
                        This expense currently satisfies the configured
                        policy rules.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            else:

                st.markdown(
                    """
                    <div class="status-box warning-box">
                        <h3>🟡 Review Required</h3>
                        <p>
                        One or more policy conditions require review.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # ------------------------------------------------
            # METRICS
            # ------------------------------------------------

            c1, c2, c3, c4 = st.columns(4)

            with c1:

                st.metric(
                    "Status",
                    result["status"],
                )

            with c2:

                st.metric(
                    "Expense Amount",
                    f"₹{amount:,.0f}",
                )

            with c3:

                st.metric(
                    "Policy Limit",
                    f"₹{result['policy_limit']:,.0f}",
                )

            with c4:

                variance = amount - result["policy_limit"]

                st.metric(
                    "Variance",
                    f"₹{variance:,.0f}",
                )

            # ------------------------------------------------
            # POLICY CHECKS
            # ------------------------------------------------

            st.markdown("#### Policy Checks")

            if len(result["issues"]) == 0:

                st.success(
                    "✓ No policy violations detected."
                )

            else:

                for issue in result["issues"]:

                    if issue["severity"] == "High":

                        st.error(
                            f"🔴 {issue['message']}"
                        )

                    else:

                        st.warning(
                            f"🟡 {issue['message']}"
                        )

            # ------------------------------------------------
            # RECEIPT COMPARISON
            # ------------------------------------------------

            if st.session_state.receipt_details:

                extracted = st.session_state.receipt_details

                st.markdown(
                    "#### Receipt Verification"
                )

                receipt_amount = extracted.get(
                    "amount"
                )

                if receipt_amount:

                    try:

                        receipt_amount = float(
                            receipt_amount
                        )

                        difference = amount - receipt_amount

                        if abs(difference) < 1:

                            st.success(
                                "🟢 Amount Match — submitted "
                                "amount matches the receipt."
                            )

                        else:

                            st.error(
                                f"🔴 Amount Mismatch — submitted "
                                f"₹{amount:,.0f}, receipt shows "
                                f"₹{receipt_amount:,.0f}. "
                                f"Difference: ₹{abs(difference):,.0f}"
                            )

                    except Exception:

                        st.warning(
                            "Receipt amount could not be compared."
                        )

                receipt_merchant = str(
                    extracted.get(
                        "merchant",
                        "",
                    )
                ).strip().lower()

                submitted_merchant = (
                    merchant.strip().lower()
                )

                if (
                    receipt_merchant
                    and submitted_merchant
                ):

                    if (
                        submitted_merchant
                        in receipt_merchant
                        or receipt_merchant
                        in submitted_merchant
                    ):

                        st.success(
                            "🟢 Merchant Match"
                        )

                    else:

                        st.warning(
                            "🟡 Merchant mismatch — "
                            "please verify the receipt."
                        )
                # ------------------------------------------------
                # RISK ASSESSMENT
                # ------------------------------------------------

                st.markdown("---")
                st.markdown("### 🛡️ Expense Risk Assessment")

                receipt_amount_for_risk = None
                merchant_match_for_risk = True

                if st.session_state.receipt_details:

                    extracted = st.session_state.receipt_details

                    receipt_amount_for_risk = extracted.get("amount")

                    receipt_merchant = str(
                        extracted.get("merchant", "")
                    ).strip().lower()

                    submitted_merchant = merchant.strip().lower()

                    if receipt_merchant and submitted_merchant:

                        merchant_match_for_risk = (
                            submitted_merchant in receipt_merchant
                            or receipt_merchant in submitted_merchant
                        )

                # Calculate risk
                risk_result = calculate_risk_score(
                    policy_issues=result["issues"],
                    receipt_present=receipt_present,
                    receipt_amount=receipt_amount_for_risk,
                    submitted_amount=amount,
                    merchant_match=merchant_match_for_risk,
                    duplicate=False,
                )

                risk_score = risk_result["score"]
                risk_level = risk_result["level"]

                # Display risk
                r1, r2 = st.columns(2)

                with r1:

                    st.metric(
                        "Expense Risk Score",
                        f"{risk_score}/100",
                    )

                with r2:

                    if risk_level == "High":

                        st.error(
                            f"🔴 {risk_level} Risk"
                        )

                    elif risk_level == "Medium":

                        st.warning(
                            f"🟡 {risk_level} Risk"
                        )

                    else:

                        st.success(
                            f"🟢 {risk_level} Risk"
                        )

                # Risk explanation
                if risk_result["factors"]:

                    st.markdown("#### Risk Factors")

                    for factor in risk_result["factors"]:

                        if factor["severity"] == "High":

                            st.error(
                                f"🔴 **{factor['factor']}** "
                                f"+{factor['points']} points"
                            )

                        else:

                            st.warning(
                                f"🟡 **{factor['factor']}** "
                                f"+{factor['points']} points"
                            )

                else:

                    st.success(
                        "🟢 No significant risk factors detected."
                    )
            # ------------------------------------------------
            # AI EXPLANATION
            # ------------------------------------------------

            st.markdown("---")

            if st.button(
                "🧠 Generate AI Explanation",
                use_container_width=True,
            ):

                with st.spinner(
                    "Gemini is preparing the explanation..."
                ):

                    try:

                        explanation = generate_expense_explanation(
                            employee=employee,
                            merchant=merchant,
                            category=expense_category,
                            amount=amount,
                            policy_limit=result["policy_limit"],
                            issues=result["issues"],
                        )

                        st.info(explanation)

                    except Exception as e:

                        st.warning(
                            "AI explanation unavailable. "
                            "The policy decision remains valid."
                        )

                        st.caption(str(e))

            # ------------------------------------------------
            # COMPLETE DETAILS
            # ------------------------------------------------

            with st.expander(
                "View Complete Expense Details"
            ):

                details = {
                    "Employee": employee,
                    "Merchant": merchant,
                    "Amount": amount,
                    "Date": str(expense_date),
                    "Department": department,
                    "Category": expense_category,
                    "Business Purpose": business_purpose,
                    "Payment Method": payment_method,
                    "Receipt Uploaded": receipt is not None,
                    "Policy Status": result["status"],
                }

                st.json(details)

# ============================================================
# AI MANAGEMENT INSIGHTS
# ============================================================

if page == "Dashboard":

    st.markdown("---")

    st.markdown("### 🧠 AI Management Insights")

    st.caption(
        "Gemini analyzes the aggregated expense data and generates "
        "a concise management-level summary."
    )

    if st.button(
        "✨ Generate Management Insights",
        use_container_width=True,
    ):

        with st.spinner(
            "Gemini is analyzing expense patterns..."
        ):

            try:

                # --------------------------------------------
                # Prepare aggregated data
                # --------------------------------------------

                total_spend_value = filtered_df["Amount"].sum()

                category_breakdown = (
                    filtered_df.groupby("Category")["Amount"]
                    .sum()
                    .sort_values(ascending=False)
                    .to_dict()
                )

                policy_issue_count = len(
                    filtered_df[
                        filtered_df["Status"]
                        .astype(str)
                        .str.lower()
                        .isin(
                            [
                                "review",
                                "pending",
                                "pending review",
                            ]
                        )
                    ]
                )

                pending_expenses = policy_issue_count

                # --------------------------------------------
                # Gemini
                # --------------------------------------------

                management_summary = (
                    generate_management_summary(
                        total_spend=total_spend_value,
                        category_breakdown=category_breakdown,
                        policy_issues=policy_issue_count,
                        pending_expenses=pending_expenses,
                    )
                )

                st.success(
                    "Management insights generated successfully."
                )

                st.markdown(
                    """
                    <div class="status-box info-box">
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown(
                    management_summary
                )

                st.markdown(
                    "</div>",
                    unsafe_allow_html=True,
                )

            except Exception as e:

                st.warning(
                    "AI management insights are currently unavailable."
                )

                st.caption(str(e))
# ============================================================
# APPROVAL CENTER
# ============================================================

elif page == "Approval Center":

    st.markdown(
        '<div class="main-title">Approval Center</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        'Review expenses requiring management attention.'
        '</div>',
        unsafe_allow_html=True,
    )

    pending = df[
        df["Status"].astype(str).str.lower()
        .isin(["review", "pending", "pending review"])
    ].copy()

    if len(pending) == 0:

        st.success(
            "No expenses are currently waiting for approval."
        )

    else:

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "Pending Expenses",
                len(pending),
            )

        with c2:

            st.metric(
                "Pending Amount",
                f"₹{pending['Amount'].sum():,.0f}",
            )

        with c3:

            st.metric(
                "Highest Pending Expense",
                f"₹{pending['Amount'].max():,.0f}",
            )

        st.markdown("---")

        st.markdown("### Pending Expenses")

        st.dataframe(
            pending.sort_values(
                "Amount",
                ascending=False,
            ),
            hide_index=True,
            use_container_width=True,
        )

        st.markdown("### Review Expense")

        selected_expense = st.selectbox(
            "Select Expense",
            pending["Expense_ID"].tolist(),
        )

        selected_row = pending[
            pending["Expense_ID"]
            == selected_expense
        ].iloc[0]

        c1, c2 = st.columns(2)

        with c1:

            st.markdown(
                f"**Employee:** {selected_row['Employee']}"
            )

            st.markdown(
                f"**Department:** {selected_row['Department']}"
            )

            st.markdown(
                f"**Category:** {selected_row['Category']}"
            )

        with c2:

            st.markdown(
                f"**Amount:** ₹{selected_row['Amount']:,.0f}"
            )

            st.markdown(
                f"**Status:** {selected_row['Status']}"
            )

        approve_col, reject_col = st.columns(2)

        with approve_col:

            if st.button(
                "✅ Approve Expense",
                use_container_width=True,
            ):

                st.success(
                    f"{selected_expense} approved for processing."
                )

        with reject_col:

            if st.button(
                "❌ Reject Expense",
                use_container_width=True,
            ):

                st.error(
                    f"{selected_expense} rejected."
                )


# ============================================================
# POLICY CENTER
# ============================================================

elif page == "Policy Center":

    st.markdown(
        '<div class="main-title">Policy Center</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        'Configure and review expense policy thresholds.'
        '</div>',
        unsafe_allow_html=True,
    )

    policy_rows = []

    for category, policy in POLICIES.items():

        policy_rows.append(
            {
                "Category": category,
                "Limit (₹)": policy["limit"],
                "Receipt Required": (
                    "Yes"
                    if policy["receipt_required"]
                    else "No"
                ),
            }
        )

    # Add Air Travel if not yet present
    if "Air Travel" not in [
        row["Category"]
        for row in policy_rows
    ]:

        policy_rows.append(
            {
                "Category": "Air Travel",
                "Limit (₹)": 15000,
                "Receipt Required": "Yes",
            }
        )

    policy_df = pd.DataFrame(policy_rows)

    st.dataframe(
        policy_df,
        hide_index=True,
        use_container_width=True,
    )

    st.markdown("---")

    st.markdown("### How ExpenseGuard Makes Decisions")

    st.markdown(
        """
        **1. Policy Engine — Source of Truth**

        Deterministic Python rules check limits, receipt requirements
        and compliance conditions.

        **2. Gemini AI — Intelligence Layer**

        Gemini assists with category classification, receipt
        understanding and natural-language explanations.

        **3. Human-in-the-Loop**

        AI suggestions do not automatically override company policy.
        Employees and approvers remain responsible for final decisions.

        **4. Graceful Degradation**

        If Gemini becomes unavailable, the deterministic policy engine
        can still evaluate the expense.
        """
    )

    st.info(
        "This separation reduces the risk of an AI model making an "
        "unsupported compliance decision."
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "ExpenseGuard AI • Intelligent Expense Management • "
    "AI-assisted, policy-driven, human-approved"
)