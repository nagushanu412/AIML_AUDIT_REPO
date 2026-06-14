"use client";

import { useEffect, useState } from "react";
import { Download } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { downloadReportFile, fetchClients, fetchProjects, fetchReports } from "@/lib/api";
import type { ApiReport } from "@/lib/api/types";

export function ReportsList() {
  const [reports, setReports] = useState<ApiReport[]>([]);
  const [projectNames, setProjectNames] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchReports(), fetchClients(), fetchProjects()])
      .then(([reportRows, , projects]) => {
        setReports(reportRows);
        setProjectNames(Object.fromEntries(projects.map((p) => [p.id, p.name])));
      })
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load reports")
      );
  }, []);

  const handleDownload = async (report: ApiReport) => {
    setDownloading(report.id);
    setError(null);
    try {
      await downloadReportFile(report.id, report.file_name);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download failed");
    } finally {
      setDownloading(null);
    }
  };

  if (error) {
    return (
      <p className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {error}
      </p>
    );
  }

  if (!reports.length) {
    return (
      <p className="rounded-lg border border-dashed border-slate-200 px-4 py-8 text-center text-sm text-slate-500">
        No reports yet. Run Journal Entry Testing analysis and use Export to generate reports.
      </p>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-slate-600">Report</th>
            <th className="px-4 py-3 text-left font-medium text-slate-600">Project</th>
            <th className="px-4 py-3 text-left font-medium text-slate-600">Type</th>
            <th className="px-4 py-3 text-left font-medium text-slate-600">Generated</th>
            <th className="px-4 py-3 text-right font-medium text-slate-600">Download</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {reports.map((report) => (
            <tr key={report.id} className="hover:bg-slate-50/80">
              <td className="px-4 py-3 font-medium text-slate-900">{report.file_name}</td>
              <td className="px-4 py-3 text-slate-600">
                {projectNames[report.project_id] ?? report.project_id.slice(0, 8)}
              </td>
              <td className="px-4 py-3 text-slate-600">{report.report_type}</td>
              <td className="px-4 py-3 text-slate-500">
                {new Date(report.created_at).toLocaleString("en-IN", {
                  dateStyle: "medium",
                  timeStyle: "short",
                })}
              </td>
              <td className="px-4 py-3 text-right">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  isLoading={downloading === report.id}
                  onClick={() => handleDownload(report)}
                >
                  <Download className="h-4 w-4" />
                  Download
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
