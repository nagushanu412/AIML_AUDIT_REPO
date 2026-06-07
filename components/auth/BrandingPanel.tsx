import { ShieldCheck } from "lucide-react";
import {
  FEATURE_HIGHLIGHTS,
  PRODUCT_NAME,
  TAGLINE,
} from "@/lib/auth/constants";

export function BrandingPanel() {
  return (
    <aside
      className="relative hidden lg:flex lg:w-[52%] xl:w-[55%] flex-col justify-between overflow-hidden bg-enterprise-gradient p-10 xl:p-14"
      aria-label="Product information"
    >
      {/* Mesh overlay */}
      <div
        className="pointer-events-none absolute inset-0 bg-mesh-gradient opacity-90"
        aria-hidden="true"
      />

      {/* Decorative grid */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.07]"
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,.8) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,.8) 1px, transparent 1px)`,
          backgroundSize: "48px 48px",
        }}
        aria-hidden="true"
      />

      {/* Floating orbs */}
      <div
        className="pointer-events-none absolute -left-20 top-1/4 h-72 w-72 rounded-full bg-brand-400/20 blur-3xl animate-pulse-soft"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute -right-16 bottom-1/4 h-64 w-64 rounded-full bg-brand-300/15 blur-3xl animate-pulse-soft"
        style={{ animationDelay: "1.5s" }}
        aria-hidden="true"
      />

      <div className="relative z-10 animate-fade-in">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/10 ring-1 ring-white/20 backdrop-blur-sm">
            <ShieldCheck className="h-6 w-6 text-white" strokeWidth={1.75} />
          </div>
          <span className="font-display text-lg font-semibold tracking-tight text-white">
            {PRODUCT_NAME}
          </span>
        </div>
      </div>

      <div className="relative z-10 max-w-lg animate-slide-up">
        <h1 className="font-display text-4xl font-bold leading-tight tracking-tight text-white xl:text-5xl">
          {PRODUCT_NAME}
        </h1>
        <p className="mt-4 text-lg leading-relaxed text-brand-100/90">{TAGLINE}</p>

        <ul className="mt-10 space-y-4" role="list">
          {FEATURE_HIGHLIGHTS.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <li
                key={feature.id}
                className="flex items-center gap-4 rounded-xl bg-white/5 px-4 py-3 ring-1 ring-white/10 backdrop-blur-sm transition-colors hover:bg-white/10"
                style={{ animationDelay: `${index * 80}ms` }}
              >
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-500/30 ring-1 ring-white/20">
                  <Icon
                    className="h-5 w-5 text-brand-100"
                    strokeWidth={1.75}
                    aria-hidden="true"
                  />
                </span>
                <span className="text-sm font-medium text-white/95">
                  {feature.label}
                </span>
              </li>
            );
          })}
        </ul>
      </div>

      <div className="relative z-10 flex items-center justify-between text-xs text-brand-200/70 animate-fade-in">
        <p>Trusted by audit firms &amp; CA practices</p>
        <p className="rounded-full bg-white/10 px-3 py-1 ring-1 ring-white/15">
          SOC 2 Ready · ISO 27001 Aligned
        </p>
      </div>
    </aside>
  );
}
