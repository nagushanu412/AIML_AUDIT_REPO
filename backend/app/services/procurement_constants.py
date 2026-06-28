from __future__ import annotations

PROCUREMENT_REQUIRED_COLUMNS = [
    "Invoice_No",
    "Invoice_Date",
    "Vendor_Name",
    "Taxable_Amount",
    "GST_Amount",
    "Total_Amount",
]

PROCUREMENT_OPTIONAL_COLUMNS = [
    "Vendor_GSTIN",
    "PO_Number",
    "Payment_Status",
    "Reference_No",
]

PROCUREMENT_RULE_DEFINITIONS: dict[str, dict] = {
    "PROC_DUPLICATE_PAYMENT": {"name": "Duplicate Vendor Payment", "module": "#7"},
    "PROC_MISSING_PO": {"name": "Missing Purchase Order", "module": "#5"},
    "PROC_GST_MISMATCH": {"name": "GST Input Mismatch", "module": "#12"},
    "PROC_HIGH_VALUE": {"name": "High-Value Vendor Invoice", "module": "#6"},
    "PROC_ROUND_AMOUNT": {"name": "Round Invoice Amount", "module": "#6"},
    "PROC_MISSING_GSTIN": {"name": "Missing Vendor GSTIN", "module": "#6"},
    "PROC_CUTOFF": {"name": "Year-End Cut-Off", "module": "#5"},
}

PROCUREMENT_RULE_PREFIX = "PROC_"
