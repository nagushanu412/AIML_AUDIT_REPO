import { ModuleDetailClient } from "@/components/dashboard/ModuleDetailClient";

export const dynamic = "force-dynamic";

interface ModuleDetailPageProps {
  params: { slug: string };
}

export default function ModuleDetailPage({ params }: ModuleDetailPageProps) {
  return <ModuleDetailClient slug={params.slug} />;
}
