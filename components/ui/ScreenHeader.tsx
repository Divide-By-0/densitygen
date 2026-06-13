import type { ReactNode } from "react";

export function ScreenHeader({
  eyebrow,
  title,
  accent,
  subtitle,
  actions,
}: {
  eyebrow: string;
  title: ReactNode;
  accent?: string;
  subtitle?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-4">
      <div className="eyebrow">{eyebrow}</div>
      <div className="mt-1 flex flex-wrap items-end justify-between gap-x-5 gap-y-3.5">
        <div className="min-w-[290px] flex-1 basis-[360px]">
          <h1 className="display text-[32px]">
            {title} {accent && <span className="accent">{accent}</span>}
          </h1>
          {subtitle && <p className="mt-1 text-[13px] text-muted">{subtitle}</p>}
        </div>
        {actions && <div className="flex gap-2">{actions}</div>}
      </div>
    </div>
  );
}
