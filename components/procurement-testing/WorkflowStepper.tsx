import { Check } from "lucide-react";
import { WORKFLOW_STEPS } from "@/lib/procurement-testing/constants";
import type { WorkflowStepId } from "@/lib/procurement-testing/types";
import { cn } from "@/lib/utils/cn";

interface WorkflowStepperProps {
  activeStep: WorkflowStepId;
  completedSteps: Set<WorkflowStepId>;
}

const STEP_ORDER: WorkflowStepId[] = [
  "select",
  "upload",
  "validate",
  "analyze",
  "review",
  "export",
];

export function WorkflowStepper({ activeStep, completedSteps }: WorkflowStepperProps) {
  const activeIndex = STEP_ORDER.indexOf(activeStep);

  return (
    <nav
      aria-label="Procurement testing workflow"
      className="rounded-xl border border-slate-200/80 bg-white p-4 shadow-sm dark:border-slate-700/80 dark:bg-slate-900"
    >
      <ol className="flex flex-wrap items-center gap-2 sm:gap-0 sm:justify-between">
        {WORKFLOW_STEPS.map((step, index) => {
          const stepId = STEP_ORDER[index];
          const isComplete = completedSteps.has(stepId);
          const isActive = stepId === activeStep;
          const isPast = index < activeIndex;

          return (
            <li
              key={step.id}
              className={cn(
                "flex items-center gap-2 text-xs sm:text-sm",
                index < WORKFLOW_STEPS.length - 1 && "sm:flex-1"
              )}
            >
              <span
                className={cn(
                  "flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold ring-2",
                  isComplete || isPast
                    ? "bg-teal-600 text-white ring-teal-600"
                    : isActive
                      ? "bg-white text-teal-700 ring-teal-600 dark:bg-slate-900"
                      : "bg-slate-100 text-slate-400 ring-slate-200 dark:bg-slate-800 dark:ring-slate-600"
                )}
              >
                {isComplete || isPast ? (
                  <Check className="h-3.5 w-3.5" aria-hidden="true" />
                ) : (
                  index + 1
                )}
              </span>
              <span
                className={cn(
                  "hidden font-medium sm:inline",
                  isActive ? "text-teal-700 dark:text-teal-300" : "text-slate-500"
                )}
              >
                {step.label}
              </span>
              {index < WORKFLOW_STEPS.length - 1 && (
                <span
                  className="mx-2 hidden h-px flex-1 bg-slate-200 sm:block dark:bg-slate-700"
                  aria-hidden="true"
                />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
