"use client";

import { Building2, Calendar, FileText } from "lucide-react";
import { SectionCard } from "@/components/journal-entry-testing/SectionCard";
import type { ClientOption, EngagementOption } from "@/lib/journal-entry-testing/types";
import { cn } from "@/lib/utils/cn";

interface ClientEngagementSectionProps {
  clients: ClientOption[];
  engagements: EngagementOption[];
  selectedClientId: string;
  selectedEngagementId: string;
  onClientChange: (clientId: string) => void;
  onEngagementChange: (engagementId: string) => void;
}

export function ClientEngagementSection({
  clients,
  engagements,
  selectedClientId,
  selectedEngagementId,
  onClientChange,
  onEngagementChange,
}: ClientEngagementSectionProps) {
  const selectedClient = clients.find((c) => c.id === selectedClientId);
  const selectedEngagement = engagements.find((e) => e.id === selectedEngagementId);

  return (
    <SectionCard
      title="Client & Engagement"
      description="Select the client and audit engagement for this journal entry test."
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <label
            htmlFor="select-client"
            className="block text-sm font-medium text-slate-700 dark:text-slate-300"
          >
            Select Client
          </label>
          <select
            id="select-client"
            value={selectedClientId}
            onChange={(e) => onClientChange(e.target.value)}
            className={cn(
              "block w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900",
              "focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30",
              "dark:border-slate-600 dark:bg-slate-800 dark:text-white"
            )}
          >
            <option value="">— Select client —</option>
            {clients.map((client) => (
              <option key={client.id} value={client.id}>
                {client.name}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-1.5">
          <label
            htmlFor="select-engagement"
            className="block text-sm font-medium text-slate-700 dark:text-slate-300"
          >
            Select Audit Engagement
          </label>
          <select
            id="select-engagement"
            value={selectedEngagementId}
            onChange={(e) => onEngagementChange(e.target.value)}
            disabled={!selectedClientId}
            className={cn(
              "block w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900",
              "focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30",
              "disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-400",
              "dark:border-slate-600 dark:bg-slate-800 dark:text-white dark:disabled:bg-slate-800/50"
            )}
          >
            <option value="">— Select engagement —</option>
            {engagements.map((eng) => (
              <option key={eng.id} value={eng.id}>
                {eng.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {selectedClient && selectedEngagement ? (
        <div className="mt-5 grid gap-3 rounded-lg border border-brand-100 bg-brand-50/50 p-4 sm:grid-cols-3 dark:border-brand-900/50 dark:bg-brand-950/30">
          <InfoItem
            icon={Building2}
            label="Client Name"
            value={selectedClient.name}
          />
          <InfoItem
            icon={Calendar}
            label="Audit Period"
            value={selectedEngagement.auditPeriod}
          />
          <InfoItem
            icon={FileText}
            label="Financial Year"
            value={selectedEngagement.financialYear}
          />
        </div>
      ) : (
        <p className="mt-4 rounded-lg border border-dashed border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-800/50 dark:text-slate-400">
          Select a client and engagement to view engagement details.
        </p>
      )}
    </SectionCard>
  );
}

function InfoItem({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Building2;
  label: string;
  value: string;
}) {
  return (
    <div className="flex gap-3">
      <Icon
        className="mt-0.5 h-4 w-4 shrink-0 text-brand-600 dark:text-brand-400"
        aria-hidden="true"
      />
      <div className="min-w-0">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
          {label}
        </p>
        <p className="mt-0.5 text-sm font-medium text-slate-900 dark:text-white">
          {value}
        </p>
      </div>
    </div>
  );
}
