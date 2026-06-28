from __future__ import annotations

REVENUE_REQUIRED_COLUMNS = [
    "Invoice_No",
    "Invoice_Date",
    "Customer_Name",
    "Taxable_Amount",
    "GST_Amount",
    "Total_Amount",
]

REVENUE_OPTIONAL_COLUMNS = [
    "Customer_GSTIN",
    "Payment_Status",
    "Reference_No",
]

REVENUE_RULE_DEFINITIONS: dict[str, dict] = {
    "REV_DUPLICATE_INVOICE": {
        "name": "Duplicate Invoice",
        "module": "#20 Invoice Checking",
    },
    "REV_CUTOFF": {
        "name": "Year-End Cut-Off",
        "module": "#20 Invoice Checking",
    },
    "REV_GST_MISMATCH": {
        "name": "GST Mismatch",
        "module": "#4 GST Mismatch Checking",
    },
    "REV_ROUND_AMOUNT": {
        "name": "Round Invoice Amount",
        "module": "#20 Invoice Checking",
    },
    "REV_HIGH_VALUE": {
        "name": "High-Value Invoice",
        "module": "#13 Customer Balance Confirmation",
    },
    "REV_MISSING_GSTIN": {
        "name": "Missing Customer GSTIN",
        "module": "#20 Invoice Checking",
    },
    "REV_UNPAID_LARGE": {
        "name": "Large Unpaid Invoice",
        "module": "#13 Customer Balance Confirmation",
    },
}

REVENUE_RULE_PREFIX = "REV_"
