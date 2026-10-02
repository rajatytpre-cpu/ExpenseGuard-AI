import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found. "
        "Please add it to your .env file."
    )

client = genai.Client(api_key=API_KEY)

MODEL = "gemini-3.5-flash-lite"


def generate_expense_explanation(
    employee,
    merchant,
    category,
    amount,
    policy_limit,
    issues
):
    """
    Generate a concise business explanation
    for an expense review.
    """

    issue_text = "\n".join(
        [
            f"- {issue['message']}"
            for issue in issues
        ]
    )

    prompt = f"""
You are ExpenseGuard AI, an enterprise
expense management assistant.

Analyze the following expense:

Employee: {employee}
Merchant: {merchant}
Category: {category}
Amount: ₹{amount:,.0f}
Policy Limit: ₹{policy_limit:,.0f}

Policy findings:
{issue_text if issue_text else "No policy violations found."}

Provide a concise management-friendly explanation.

Rules:
1. Do not change or override the policy decision.
2. Do not invent facts.
3. Explain why the expense is compliant or requires review.
4. Mention the financial impact if applicable.
5. Recommend the next action.
6. Keep the response under 100 words.
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    return response.text


def categorize_expense(
    merchant,
    purpose
):
    """
    Ask Gemini to suggest an expense category.
    """

    prompt = f"""
You are an expense classification assistant.

Merchant:
{merchant}

Business purpose:
{purpose}

Choose exactly ONE category:

Client Meals
Hotel
Travel
Software
Office Supplies
Client Entertainment
Other

Return ONLY the category name.
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    return response.text.strip()


def generate_management_summary(
    total_spend,
    category_breakdown,
    policy_issues,
    pending_expenses
):
    """
    Generate an executive summary from
    aggregated expense statistics.
    """

    prompt = f"""
You are an enterprise finance analyst.

Create a short management summary using
ONLY the following information.

Total spend:
₹{total_spend:,.0f}

Category breakdown:
{category_breakdown}

Policy issues:
{policy_issues}

Pending expenses:
{pending_expenses}

Provide:
1. One key observation
2. One risk/concern
3. One recommended management action

Keep the answer under 120 words.
Do not invent numbers or facts.
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    return response.text
def extract_receipt_details(receipt_file):
    """
    Extract structured expense information from a receipt using Gemini.
    """

    prompt = """
You are an enterprise expense receipt extraction assistant.

Analyze the uploaded receipt and extract ONLY information that is
clearly visible or reasonably readable.

Return ONLY valid JSON:

{
  "merchant": "",
  "date": "",
  "amount": 0,
  "currency": "",
  "category": "",
  "description": ""
}

Rules:
- Do not invent missing information.
- If a field cannot be identified, use an empty string.
- Amount must be the final payable/total amount.
- Category must be one of:
  Client Meals, Hotel, Travel, Software, Office Supplies,
  Client Entertainment, Air Travel, Other
- Keep description short.
- Return ONLY JSON.
"""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=[
                prompt,
                receipt_file
            ]
        )

        text = response.text.strip()

        if text.startswith("```"):
            text = text.replace("```json", "")
            text = text.replace("```", "")
            text = text.strip()

        import json

        return json.loads(text)

    except Exception as e:
        return {
            "error": str(e)
        }