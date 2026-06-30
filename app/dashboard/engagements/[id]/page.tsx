import Link from "next/link";
import { EngagementHubClient } from "@/components/dashboard/EngagementHubClient";

export default function EngagementHubPage({
  params,
}: {
  params: { id: string };
}) {
  return (
    <div className="space-y-4">
      <Link
        href="/dashboard/engagements"
        className="text-sm text-brand-600 hover:underline"
      >
        ← Back to engagements
      </Link>
      <EngagementHubClient engagementId={params.id} />
    </div>
  );
}
