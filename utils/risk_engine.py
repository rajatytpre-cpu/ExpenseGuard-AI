def calculate_risk_score(
    policy_issues,
    receipt_present,
    receipt_amount=None,
    submitted_amount=0,
    merchant_match=True,
    duplicate=False,
):
    """
    Calculate a transparent, rule-based expense risk score.

    Score:
    0-29   = Low
    30-59  = Medium
    60+    = High
    """

    score = 0
    factors = []

    # Policy violations
    for issue in policy_issues:

        if issue["type"] == "POLICY_LIMIT":
            score += 30
            factors.append(
                {
                    "factor": "Policy Limit Exceeded",
                    "points": 30,
                    "severity": "High",
                }
            )

        elif issue["type"] == "MISSING_RECEIPT":
            score += 20
            factors.append(
                {
                    "factor": "Missing Receipt",
                    "points": 20,
                    "severity": "Medium",
                }
            )

    # Receipt amount mismatch
    if receipt_amount is not None:

        try:
            difference = abs(
                float(submitted_amount)
                - float(receipt_amount)
            )

            if difference > 1:

                score += 30

                factors.append(
                    {
                        "factor": "Receipt Amount Mismatch",
                        "points": 30,
                        "severity": "High",
                    }
                )

        except (ValueError, TypeError):
            pass

    # Merchant mismatch
    if not merchant_match:

        score += 20

        factors.append(
            {
                "factor": "Merchant Mismatch",
                "points": 20,
                "severity": "Medium",
            }
        )

    # Duplicate expense
    if duplicate:

        score += 25

        factors.append(
            {
                "factor": "Potential Duplicate",
                "points": 25,
                "severity": "High",
            }
        )

    # Cap score
    score = min(score, 100)

    # Risk level
    if score >= 60:
        level = "High"
    elif score >= 30:
        level = "Medium"
    else:
        level = "Low"

    return {
        "score": score,
        "level": level,
        "factors": factors,
    }
