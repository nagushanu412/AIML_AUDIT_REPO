REQUIRED_COLUMNS = [
    "Journal_ID",
    "Posting_Date",
    "Account_Code",
    "Account_Name",
    "Amount",
    "Debit_Credit",
    "User_ID",
    "Description",
]

VALID_DEBIT_CREDIT = {"DEBIT", "CREDIT", "D", "C"}

RULE_DEFINITIONS: dict[str, dict] = {
    "LARGE_VALUE": {
        "code": "LARGE_VALUE",
        "name": "Large Value Entries",
        "description": "Flag entries greater than the configurable project threshold.",
    },
    "YEAR_END": {
        "code": "YEAR_END",
        "name": "Year End Entries",
        "description": "Flag entries posted during the last 7 days of the financial year.",
    },
    "ROUND_AMOUNT": {
        "code": "ROUND_AMOUNT",
        "name": "Round Amount Entries",
        "description": "Flag amounts ending in 000, 500, 1000, or 5000.",
    },
    "WEEKEND": {
        "code": "WEEKEND",
        "name": "Weekend Entries",
        "description": "Flag entries posted on Saturday or Sunday.",
    },
    "SUSPENSE_ACCOUNT": {
        "code": "SUSPENSE_ACCOUNT",
        "name": "Suspense Account Entries",
        "description": "Flag entries where account name contains Suspense, Clearing, or Adjustment.",
    },
    "MANUAL_JOURNAL": {
        "code": "MANUAL_JOURNAL",
        "name": "Manual Journal Entries",
        "description": "Flag entries with description containing Manual, Adjustment, or Correction.",
    },
    "UNUSUAL_POSTING": {
        "code": "UNUSUAL_POSTING",
        "name": "Unusual Posting Patterns",
        "description": "Flag users posting an unusually high number of journals vs the average.",
    },
}

ROUND_AMOUNT_SUFFIXES = (500, 1000, 5000)

SUSPENSE_KEYWORDS = ("suspense", "clearing", "adjustment")

MANUAL_KEYWORDS = ("manual", "adjustment", "correction")
