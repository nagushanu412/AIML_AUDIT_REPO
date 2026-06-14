"use client";

import { FormEvent, useEffect, useState } from "react";
import { Pencil } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { fetchRules, updateRule } from "@/lib/api";
import type { ApiRule } from "@/lib/api/types";

const WEEKDAY_OPTIONS = [
  { value: 0, label: "Monday" },
  { value: 1, label: "Tuesday" },
  { value: 2, label: "Wednesday" },
  { value: 3, label: "Thursday" },
  { value: 4, label: "Friday" },
  { value: 5, label: "Saturday" },
  { value: 6, label: "Sunday" },
];

function parseList(value: string): string[] {
  return value
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

function parseNumberList(value: string): number[] {
  return parseList(value).map((s) => Number(s));
}

interface RuleFormState {
  ruleName: string;
  description: string;
  defaultScore: string;
  isActive: boolean;
  threshold: string;
  daysBefore: string;
  suffixes: string;
  weekdays: number[];
  suspenseKeywords: string;
  manualKeywords: string;
  stdMultiplier: string;
  minCount: string;
}

function configToForm(rule: ApiRule): RuleFormState {
  const cfg = rule.config_schema ?? {};
  const keywords = Array.isArray(cfg.keywords) ? (cfg.keywords as string[]).join(", ") : "";
  return {
    ruleName: rule.rule_name,
    description: rule.description ?? "",
    defaultScore: String(rule.default_score),
    isActive: rule.is_active,
    threshold: cfg.threshold != null ? String(cfg.threshold) : "",
    daysBefore: String(cfg.days_before ?? 7),
    suffixes: Array.isArray(cfg.suffixes) ? cfg.suffixes.join(", ") : "500, 1000, 5000",
    weekdays: Array.isArray(cfg.weekdays) ? (cfg.weekdays as number[]) : [5, 6],
    suspenseKeywords:
      rule.rule_code === "SUSPENSE_ACCOUNT"
        ? keywords || "suspense, clearing, adjustment"
        : "suspense, clearing, adjustment",
    manualKeywords:
      rule.rule_code === "MANUAL_JOURNAL"
        ? keywords || "manual, adjustment, correction"
        : "manual, adjustment, correction",
    stdMultiplier: String(cfg.std_multiplier ?? 2),
    minCount: String(cfg.min_count ?? 5),
  };
}

function buildConfigPayload(ruleCode: string, form: RuleFormState): Record<string, unknown> {
  switch (ruleCode) {
    case "LARGE_VALUE":
      return {
        threshold: form.threshold.trim() ? Number(form.threshold) : null,
      };
    case "YEAR_END":
      return { days_before: Number(form.daysBefore) };
    case "ROUND_AMOUNT":
      return { suffixes: parseNumberList(form.suffixes) };
    case "WEEKEND":
      return { weekdays: form.weekdays };
    case "SUSPENSE_ACCOUNT":
      return { keywords: parseList(form.suspenseKeywords) };
    case "MANUAL_JOURNAL":
      return { keywords: parseList(form.manualKeywords) };
    case "UNUSUAL_POSTING":
      return {
        std_multiplier: Number(form.stdMultiplier),
        min_count: Number(form.minCount),
      };
    default:
      return {};
  }
}

function RuleConfigFields({
  ruleCode,
  form,
  setForm,
}: {
  ruleCode: string;
  form: RuleFormState;
  setForm: React.Dispatch<React.SetStateAction<RuleFormState | null>>;
}) {
  const update = (patch: Partial<RuleFormState>) =>
    setForm((prev) => (prev ? { ...prev, ...patch } : prev));

  if (ruleCode === "LARGE_VALUE") {
    return (
      <Input
        label="Threshold (₹)"
        type="number"
        min={1}
        value={form.threshold}
        onChange={(e) => update({ threshold: e.target.value })}
        placeholder="Leave empty to use engagement default"
      />
    );
  }

  if (ruleCode === "YEAR_END") {
    return (
      <Input
        label="Days before financial year end"
        type="number"
        min={1}
        max={30}
        value={form.daysBefore}
        onChange={(e) => update({ daysBefore: e.target.value })}
        required
      />
    );
  }

  if (ruleCode === "ROUND_AMOUNT") {
    return (
      <Input
        label="Round amount suffixes (comma-separated)"
        value={form.suffixes}
        onChange={(e) => update({ suffixes: e.target.value })}
        placeholder="500, 1000, 5000"
        required
      />
    );
  }

  if (ruleCode === "WEEKEND") {
    return (
      <div>
        <p className="text-sm font-medium text-slate-700">Flag posting days</p>
        <div className="mt-2 flex flex-wrap gap-3">
          {WEEKDAY_OPTIONS.map((day) => (
            <label key={day.value} className="flex items-center gap-2 text-sm text-slate-600">
              <input
                type="checkbox"
                checked={form.weekdays.includes(day.value)}
                onChange={(e) => {
                  const next = e.target.checked
                    ? [...form.weekdays, day.value].sort()
                    : form.weekdays.filter((d) => d !== day.value);
                  update({ weekdays: next });
                }}
              />
              {day.label}
            </label>
          ))}
        </div>
      </div>
    );
  }

  if (ruleCode === "SUSPENSE_ACCOUNT") {
    return (
      <Input
        label="Account name keywords (comma-separated)"
        value={form.suspenseKeywords}
        onChange={(e) => update({ suspenseKeywords: e.target.value })}
        required
      />
    );
  }

  if (ruleCode === "MANUAL_JOURNAL") {
    return (
      <Input
        label="Description keywords (comma-separated)"
        value={form.manualKeywords}
        onChange={(e) => update({ manualKeywords: e.target.value })}
        required
      />
    );
  }

  if (ruleCode === "UNUSUAL_POSTING") {
    return (
      <div className="grid gap-3 sm:grid-cols-2">
        <Input
          label="Std deviation multiplier"
          type="number"
          min={0.1}
          step={0.1}
          value={form.stdMultiplier}
          onChange={(e) => update({ stdMultiplier: e.target.value })}
          required
        />
        <Input
          label="Minimum entry count"
          type="number"
          min={1}
          value={form.minCount}
          onChange={(e) => update({ minCount: e.target.value })}
          required
        />
      </div>
    );
  }

  return null;
}

export function RulesList() {
  const [rules, setRules] = useState<ApiRule[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [editingRule, setEditingRule] = useState<ApiRule | null>(null);
  const [form, setForm] = useState<RuleFormState | null>(null);
  const [saving, setSaving] = useState(false);

  const load = () => {
    fetchRules()
      .then(setRules)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load rules"));
  };

  useEffect(() => {
    load();
  }, []);

  const startEdit = (rule: ApiRule) => {
    setEditingRule(rule);
    setForm(configToForm(rule));
    setError(null);
  };

  const cancelEdit = () => {
    setEditingRule(null);
    setForm(null);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!editingRule || !form) return;

    if (editingRule.rule_code === "WEEKEND" && form.weekdays.length === 0) {
      setError("Select at least one weekday for the WEEKEND rule.");
      return;
    }

    setSaving(true);
    setError(null);
    try {
      await updateRule(editingRule.id, {
        rule_name: form.ruleName.trim(),
        description: form.description.trim() || null,
        default_score: Number(form.defaultScore),
        is_active: form.isActive,
        config_schema: buildConfigPayload(editingRule.rule_code, form),
      });
      cancelEdit();
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <p className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
        Changes apply on the next <strong>Run AI Analysis</strong> in Journal Entry Testing.
        Large value threshold can also be set per engagement.
      </p>

      {error && (
        <p className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {editingRule && form && (
        <form
          onSubmit={handleSubmit}
          className="space-y-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
        >
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900">
              Edit Rule: {editingRule.rule_code}
            </h3>
            <Button type="button" variant="outline" size="sm" onClick={cancelEdit}>
              Cancel
            </Button>
          </div>

          <Input
            label="Rule code"
            value={editingRule.rule_code}
            readOnly
            disabled
          />
          <Input
            label="Rule name"
            value={form.ruleName}
            onChange={(e) => setForm({ ...form, ruleName: e.target.value })}
            required
          />
          <div>
            <label className="block text-sm font-medium text-slate-700">Description</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={2}
              className="mt-1 block w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </div>
          <Input
            label="Risk score (1–100)"
            type="number"
            min={1}
            max={100}
            value={form.defaultScore}
            onChange={(e) => setForm({ ...form, defaultScore: e.target.value })}
            required
          />
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={form.isActive}
              onChange={(e) => setForm({ ...form, isActive: e.target.checked })}
            />
            Rule active (included in analysis)
          </label>

          <div className="border-t border-slate-100 pt-4">
            <p className="mb-3 text-sm font-medium text-slate-800">Rule configuration</p>
            <RuleConfigFields
              ruleCode={editingRule.rule_code}
              form={form}
              setForm={setForm}
            />
          </div>

          <Button type="submit" variant="primary" size="sm" isLoading={saving}>
            Update Rule
          </Button>
        </form>
      )}

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Code</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Rule</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Score</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Active</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Description</th>
              <th className="px-4 py-3 text-right font-medium text-slate-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rules.map((rule) => (
              <tr
                key={rule.id}
                className={`hover:bg-slate-50/80 ${!rule.is_active ? "opacity-60" : ""}`}
              >
                <td className="px-4 py-3 font-mono text-xs text-slate-700">{rule.rule_code}</td>
                <td className="px-4 py-3 font-medium text-slate-900">{rule.rule_name}</td>
                <td className="px-4 py-3 text-slate-600">{rule.default_score}</td>
                <td className="px-4 py-3 text-slate-600">{rule.is_active ? "Yes" : "No"}</td>
                <td className="px-4 py-3 text-slate-600">{rule.description ?? "—"}</td>
                <td className="px-4 py-3 text-right">
                  <button
                    type="button"
                    onClick={() => startEdit(rule)}
                    className="rounded p-1.5 text-slate-500 hover:bg-slate-100"
                    aria-label="Edit rule"
                  >
                    <Pencil className="h-4 w-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
