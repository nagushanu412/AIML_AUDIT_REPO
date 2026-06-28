"use client";

import { useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, Inbox, Search } from "lucide-react";
import { SectionCard } from "@/components/journal-entry-testing/SectionCard";
import type { ProcurementFinding, RiskLevel } from "@/lib/procurement-testing/types";
import { formatIndianAmount } from "@/lib/journal-entry-testing/utils";
import { cn } from "@/lib/utils/cn";

const PAGE_SIZE = 8;

const RISK_STYLES: Record<RiskLevel, string> = {
  high: "bg-red-50 text-red-700 ring-red-200",
  medium: "bg-amber-50 text-amber-700 ring-amber-200",
  low: "bg-emerald-50 text-emerald-700 ring-emerald-200",
};

export function ProcurementFindingsTable({ findings }: { findings: ProcurementFinding[] }) {
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState<RiskLevel | "all">("all");
  const [page, setPage] = useState(1);

  const filtered = useMemo(() => {
    let rows = findings.filter((f) => f.riskScore > 0);
    if (search.trim()) {
      const q = search.toLowerCase();
      rows = rows.filter(
        (f) =>
          f.invoiceNo.toLowerCase().includes(q) ||
          f.vendorName.toLowerCase().includes(q) ||
          f.aiExplanation.toLowerCase().includes(q)
      );
    }
    if (riskFilter !== "all") rows = rows.filter((f) => f.riskLevel === riskFilter);
    return rows.sort((a, b) => b.riskScore - a.riskScore);
  }, [findings, search, riskFilter]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <SectionCard title="Invoice Exception Register" description="Line-level procurement exceptions ranked by AI risk score.">
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative max-w-xs flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            placeholder="Search invoice, Vendor…"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="w-full rounded-lg border border-slate-200 py-2 pl-9 pr-3 text-sm"
          />
        </div>
        <select
          value={riskFilter}
          onChange={(e) => { setRiskFilter(e.target.value as RiskLevel | "all"); setPage(1); }}
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm"
        >
          <option value="all">All risk levels</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {paginated.length === 0 ? (
        <div className="flex flex-col items-center py-12 text-slate-500">
          <Inbox className="h-10 w-10 text-slate-300" />
          <p className="mt-2 text-sm">No exceptions match your filters.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3">Invoice</th>
                <th className="px-4 py-3">Vendor</th>
                <th className="px-4 py-3 text-right">Amount</th>
                <th className="px-4 py-3">Risk</th>
                <th className="px-4 py-3">AI Explanation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {paginated.map((f) => (
                <tr key={f.id} className="hover:bg-slate-50/80">
                  <td className="whitespace-nowrap px-4 py-3 text-slate-600">{f.invoiceDate}</td>
                  <td className="px-4 py-3 font-medium text-slate-900">{f.invoiceNo}</td>
                  <td className="px-4 py-3 text-slate-700">{f.vendorName}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-right font-medium">
                    ₹ {formatIndianAmount(f.totalAmount)}
                  </td>
                  <td className="px-4 py-3">
                    <span className={cn("rounded-full px-2 py-0.5 text-xs font-semibold ring-1", RISK_STYLES[f.riskLevel])}>
                      {f.riskLevel} · {f.riskScore}
                    </span>
                  </td>
                  <td className="max-w-xs px-4 py-3 text-xs text-slate-500">{f.aiExplanation}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
        <div className="mt-4 flex items-center justify-between text-sm text-slate-500">
          <span>Page {page} of {totalPages}</span>
          <div className="flex gap-2">
            <button type="button" disabled={page <= 1} onClick={() => setPage((p) => p - 1)} className="rounded border px-2 py-1 disabled:opacity-40">
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button type="button" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)} className="rounded border px-2 py-1 disabled:opacity-40">
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </SectionCard>
  );
}
