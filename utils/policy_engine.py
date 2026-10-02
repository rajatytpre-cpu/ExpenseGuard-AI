# utils/policy_engine.py

POLICIES = {
    "Client Meals": {
        "limit": 3000,
        "receipt_required": True
    },
    "Hotel": {
        "limit": 10000,
        "receipt_required": True
    },
    "Travel": {
        "limit": 2500,
        "receipt_required": True
    },
    "Software": {
        "limit": 10000,
        "receipt_required": True
    },
    "Office Supplies": {
        "limit": 5000,
        "receipt_required": True
    },
    "Client Entertainment": {
        "limit": 5000,
        "receipt_required": True
    },
    "Other": {
        "limit": 2000,
        "receipt_required": True
    }
}


def check_expense(
    category,
    amount,
    receipt_present
):
    """
    Evaluate an expense against company policy.
    """

    policy = POLICIES.get(
        category,
        POLICIES["Other"]
    )

    issues = []

    # -----------------------------
    # AMOUNT CHECK
    # -----------------------------

    if amount > policy["limit"]:

        excess = amount - policy["limit"]

        issues.append({
            "type": "POLICY_LIMIT",
            "message": (
                f"Amount exceeds the permitted "
                f"limit by ₹{excess:,.0f}."
            ),
            "severity": "High"
        })

    # -----------------------------
    # RECEIPT CHECK
    # -----------------------------

    if (
        policy["receipt_required"]
        and not receipt_present
    ):

        issues.append({
            "type": "MISSING_RECEIPT",
            "message": "Receipt is required for this expense.",
            "severity": "Medium"
        })

    # -----------------------------
    # FINAL STATUS
    # -----------------------------

    if len(issues) == 0:

        status = "Approved"

    elif any(
        issue["severity"] == "High"
        for issue in issues
    ):

        status = "Review"

    else:

        status = "Review"

    return {
        "status": status,
        "policy_limit": policy["limit"],
        "issues": issues
    }