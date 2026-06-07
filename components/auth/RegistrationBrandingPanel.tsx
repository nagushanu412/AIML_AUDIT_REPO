import { ShieldCheck } from "lucide-react";
import {
  REGISTRATION_BENEFITS,
  REGISTRATION_PRODUCT_NAME,
  REGISTRATION_SUBTITLE,
  REGISTRATION_TITLE,
  TRIAL_BADGES,
} from "@/lib/auth/registrationConstants";

export function RegistrationBrandingPanel() {
  return (
    <aside
      className="relative hidden lg:flex lg:w-[52%] xl:w-[55%] flex-col justify-between overflow-hidden bg-enterprise-gradient p-10 xl:p-14"
      aria-label="Product information"
    >
      <div
        className="pointer-events-none absolute inset-0 bg-mesh-gradient opacity-90"
        aria-hidden="true"
      />

      <div
        className="pointer-events-none absolute inset-0 opacity-[0.07]"
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,.8) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,.8) 1px, transparent 1px)`,
          backgroundSize: "48px 48px",
        }}
        aria-hidden="true"
      />

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
            {REGISTRATION_PRODUCT_NAME}
          </span>
        </div>
      </div>

      <div className="relative z-10 max-w-xl animate-slide-up">
        <h1 className="font-display text-3xl font-bold leading-tight tracking-tight text-white xl:text-4xl">
          {REGISTRATION_TITLE}
        </h1>
        <p className="mt-4 text-base leading-relaxed text-brand-100/90 xl:text-lg">
          {REGISTRATION_SUBTITLE}
        </p>

        <ul className="mt-10 space-y-3.5" role="list">
          {REGISTRATION_BENEFITS.map((benefit, index) => {
            const Icon = benefit.icon;
            return (
              <li
                key={benefit.id}
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
                  {benefit.label}
                </span>
              </li>
            );
          })}
        </ul>

        <div className="mt-8 flex flex-wrap gap-2">
          {TRIAL_BADGES.map((badge) => (
            <span
              key={badge.id}
              className="rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-brand-100 ring-1 ring-white/15"
            >
              {badge.label}
            </span>
          ))}
        </div>
      </div>

      <div className="relative z-10 flex items-center justify-between text-xs text-brand-200/70 animate-fade-in">
        <p>Built for CA firms, auditors &amp; audit managers</p>
        <p className="rounded-full bg-white/10 px-3 py-1 ring-1 ring-white/15">
          SOC 2 Ready · ISO 27001 Aligned
        </p>
      </div>
    </aside>
  );
}
