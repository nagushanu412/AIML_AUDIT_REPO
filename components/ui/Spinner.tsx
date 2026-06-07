import { cn } from "@/lib/utils/cn";

interface SpinnerProps {
  className?: string;
  size?: "sm" | "md" | "lg";
  label?: string;
}

const sizeClasses = {
  sm: "h-4 w-4 border-2",
  md: "h-5 w-5 border-2",
  lg: "h-8 w-8 border-[3px]",
};

export function Spinner({
  className,
  size = "md",
  label = "Loading",
}: SpinnerProps) {
  return (
    <span className={cn("inline-flex items-center gap-2", className)} role="status">
      <span
        className={cn(
          "animate-spin rounded-full border-white/30 border-t-white",
          sizeClasses[size]
        )}
        aria-hidden="true"
      />
      <span className="sr-only">{label}</span>
    </span>
  );
}
