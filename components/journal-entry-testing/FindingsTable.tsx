"use client";

import { useMemo, useState } from "react";
import {
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  Search,
  Inbox,
} from "lucide-react";
import { SectionCard } from "@/components/journal-entry-testing/SectionCard";
import type {
  JournalFinding,
  RiskLevel,
  SortDirection,
  SortField,
} from "@/lib/journal-entry-testing/types";
import { formatIndianAmount } from "@/lib/journal-entry-testing/utils";
import { cn } from "@/lib/utils/cn";

const PAGE_SIZE = 5;

interface FindingsTableProps {
  findings: JournalFinding[];
}

const RISK_LEVEL_STYLES: Record<RiskLevel, string> = {
  high: "bg-red-50 text-red-700 ring-red-200 dark:bg-red-950/50 dark:text-red-300 dark:ring-red-900",
  medium:
    "bg-amber-50 text-amber-700 ring-amber-200 dark:bg-amber-950/50 dark:text-amber-300 dark:ring-amber-900",
  low: "bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-950/50 dark:text-emerald-300 dark:ring-emerald-900",
};

export function FindingsTable({ findings }: FindingsTableProps) {
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState<RiskLevel | "all">("all");
  const [sortField, setSortField] = useState<SortField>("riskScore");
  const [sortDir, setSortDir] = useState<SortDirection>("desc");
  const [page, setPage] = useState(1);

  const filtered = useMemo(() => {
    let rows = [...findings];

    if (search.trim()) {
      const q = search.toLowerCase();
      rows = rows.filter(
        (f) =>
          f.voucherNumber.toLowerCase().includes(q) ||
          f.accountName.toLowerCase().includes(q) ||
          f.aiExplanation.toLowerCase().includes(q) ||
          f.date.toLowerCase().includes(q)
      );
    }

    if (riskFilter !== "all") {
      rows = rows.filter((f) => f.riskLevel === riskFilter);
    }

    rows.sort((a, b) => {
      const aVal = a[sortField];
      const bVal = b[sortField];
      if (typeof aVal === "number" && typeof bVal === "number") {
        return sortDir === "asc" ? aVal - bVal : bVal - aVal;
      }
      const cmp = String(aVal).localeCompare(String(bVal));
      return sortDir === "asc" ? cmp : -cmp;
    });

    return rows;
  }, [findings, search, riskFilter, sortField, sortDir]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages);
  const paginated = filtered.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE
  );

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("desc");
    }
    setPage(1);
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return null;
    return sortDir === "asc" ? (
      <ChevronUp className="h-3.5 w-3.5" aria-hidden="true" />
    ) : (
      <ChevronDown className="h-3.5 w-3.5" aria-hidden="true" />
    );
  };

  return (
    <SectionCard
      title="High-Risk Journal Entries"
      description="Entry-level risk scores from rule violations — drill down by voucher and account."
    >
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
            aria-hidden="true"
          />
          <input
            type="search"
            placeholder="Search voucher, account, explanation…"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className={cn(
              "w-full rounded-lg border border-slate-200 bg-white py-2 pl-9 pr-3 text-sm",
              "focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30",
              "dark:border-slate-600 dark:bg-slate-800 dark:text-white"
            )}
          />
        </div>
        <select
          value={riskFilter}
          onChange={(e) => {
            setRiskFilter(e.target.value as RiskLevel | "all");
            setPage(1);
          }}
          className={cn(
            "rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm",
            "focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30",
            "dark:border-slate-600 dark:bg-slate-800 dark:text-white sm:w-40"
          )}
          aria-label="Filter by risk level"
        >
          <option value="all">All risk levels</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {paginated.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-slate-200 py-12 dark:border-slate-700">
          <Inbox className="h-10 w-10 text-slate-300 dark:text-slate-600" aria-hidden="true" />
          <p className="mt-3 text-sm font-medium text-slate-600 dark:text-slate-400">
            No findings match your search
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700">
          <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
            <thead className="bg-slate-50 dark:bg-slate-800/80">
              <tr>
                <Th field="date" onSort={toggleSort}>
                  Date <SortIcon field="date" />
                </Th>
                <Th field="voucherNumber" onSort={toggleSort}>
                  Voucher <SortIcon field="voucherNumber" />
                </Th>
                <Th field="accountName" onSort={toggleSort}>
                  Account <SortIcon field="accountName" />
                </Th>
                <Th field="debitAmount" onSort={toggleSort} className="text-right">
                  Debit <SortIcon field="debitAmount" />
                </Th>
                <Th field="creditAmount" onSort={toggleSort} className="text-right">
                  Credit <SortIcon field="creditAmount" />
                </Th>
                <Th field="riskScore" onSort={toggleSort} className="text-right">
                  Score <SortIcon field="riskScore" />
                </Th>
                <Th field="riskLevel" onSort={toggleSort}>
                  Level <SortIcon field="riskLevel" />
                </Th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                  AI Explanation
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white dark:divide-slate-800 dark:bg-slate-900">
              {paginated.map((row) => (
                <tr
                  key={row.id}
                  className="transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/50"
                >
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-900 dark:text-white">
                    {row.date}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-brand-600 dark:text-brand-400">
                    {row.voucherNumber}
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-700 dark:text-slate-300">
                    {row.accountName}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-right text-sm tabular-nums text-slate-700 dark:text-slate-300">
                    {row.debitAmount > 0
                      ? `₹ ${formatIndianAmount(row.debitAmount)}`
                      : "—"}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-right text-sm tabular-nums text-slate-700 dark:text-slate-300">
                    {row.creditAmount > 0
                      ? `₹ ${formatIndianAmount(row.creditAmount)}`
                      : "—"}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-right text-sm font-semibold tabular-nums text-slate-900 dark:text-white">
                    {row.riskScore}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3">
                    <span
                      className={cn(
                        "inline-flex rounded-full px-2 py-0.5 text-xs font-semibold capitalize ring-1",
                        RISK_LEVEL_STYLES[row.riskLevel]
                      )}
                    >
                      {row.riskLevel}
                    </span>
                  </td>
                  <td className="max-w-xs px-4 py-3 text-sm text-slate-600 dark:text-slate-400">
                    {row.aiExplanation}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {filtered.length > 0 && (
        <div className="mt-4 flex flex-col items-center justify-between gap-3 sm:flex-row">
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Showing {(currentPage - 1) * PAGE_SIZE + 1}–
            {Math.min(currentPage * PAGE_SIZE, filtered.length)} of{" "}
            {filtered.length} findings
          </p>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={currentPage <= 1}
              className="rounded-lg border border-slate-200 p-2 disabled:opacity-40 dark:border-slate-600"
              aria-label="Previous page"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Page {currentPage} of {totalPages}
            </span>
            <button
              type="button"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage >= totalPages}
              className="rounded-lg border border-slate-200 p-2 disabled:opacity-40 dark:border-slate-600"
              aria-label="Next page"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </SectionCard>
  );
}

function Th({
  children,
  field,
  onSort,
  className,
}: {
  children: React.ReactNode;
  field: SortField;
  onSort: (f: SortField) => void;
  className?: string;
}) {
  return (
    <th className={cn("px-4 py-3", className)}>
      <button
        type="button"
        onClick={() => onSort(field)}
        className="inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wide text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white"
      >
        {children}
      </button>
    </th>
  );
}
