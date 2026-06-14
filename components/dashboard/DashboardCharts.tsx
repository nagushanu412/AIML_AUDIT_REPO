"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const RISK_COLORS = ["#ef4444", "#f59e0b", "#10b981"];

interface DashboardChartsProps {
  riskDistribution: Record<string, number>;
  violationsByRule: Record<string, number>;
}

export function DashboardCharts({
  riskDistribution,
  violationsByRule,
}: DashboardChartsProps) {
  const riskData = [
    { name: "High", value: riskDistribution.high ?? 0, fill: RISK_COLORS[0] },
    { name: "Medium", value: riskDistribution.medium ?? 0, fill: RISK_COLORS[1] },
    { name: "Low", value: riskDistribution.low ?? 0, fill: RISK_COLORS[2] },
  ];

  const ruleData = Object.entries(violationsByRule)
    .map(([rule, count]) => ({ rule, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 7);

  const hasRisk = riskData.some((d) => d.value > 0);
  const hasRules = ruleData.length > 0;

  if (!hasRisk && !hasRules) {
    return (
      <p className="rounded-xl border border-dashed border-slate-200 bg-white px-4 py-8 text-center text-sm text-slate-500">
        Run journal entry analysis to populate risk and violation charts.
      </p>
    );
  }

  return (
    <section className="grid gap-4 lg:grid-cols-2" aria-label="Analytics charts">
      {hasRisk && (
        <article className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <h3 className="mb-4 text-sm font-semibold text-slate-900">Risk distribution</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={riskData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label={({ name, value }) => `${name}: ${value}`}
              >
                {riskData.map((entry, i) => (
                  <Cell key={entry.name} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </article>
      )}

      {hasRules && (
        <article className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <h3 className="mb-4 text-sm font-semibold text-slate-900">Violations by rule</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={ruleData} margin={{ left: 0, right: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="rule" tick={{ fontSize: 10 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#4f46e5" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </article>
      )}
    </section>
  );
}
