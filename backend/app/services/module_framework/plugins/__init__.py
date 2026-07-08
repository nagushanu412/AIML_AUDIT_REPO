"""Built-in module plugin registrations."""

from app.services.module_framework.plugins.journal_entry import build_journal_entry_plugin
from app.services.module_framework.plugins.procurement import build_procurement_plugin
from app.services.module_framework.plugins.revenue import build_revenue_plugin

PLUGIN_BUILDERS = {
    "JOURNAL_ENTRY_TESTING": build_journal_entry_plugin,
    "REVENUE_TESTING": build_revenue_plugin,
    "PROCUREMENT_TESTING": build_procurement_plugin,
}
