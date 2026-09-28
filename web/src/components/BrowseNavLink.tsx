"use client";

import type { MouseEvent, ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

/** Asks the home AskPanel to leave its answer view and show browse sections again. */
export const SHOW_BROWSE_EVENT = "founder-atlas:show-browse";

interface BrowseNavLinkProps {
  /** Section id on the home page, e.g. `keywords`. */
  readonly sectionId: string;
  readonly children: ReactNode;
}

/** Header link to a home section; works even while an answer hides that section. */
export function BrowseNavLink({ sectionId, children }: BrowseNavLinkProps) {
  const pathname = usePathname();

  function handleClick(event: MouseEvent<HTMLAnchorElement>): void {
    if (pathname !== "/") return;
    event.preventDefault();
    window.dispatchEvent(new Event(SHOW_BROWSE_EVENT));
    // The section only exists after AskPanel re-renders its children.
    requestAnimationFrame(() => {
      document.getElementById(sectionId)?.scrollIntoView({ behavior: "smooth" });
      window.history.replaceState(null, "", `#${sectionId}`);
    });
  }

  return (
    <Link
      href={`/#${sectionId}`}
      onClick={handleClick}
      className="rounded-lg px-2 py-1.5 text-[14px] text-ink-muted transition-colors hover:text-ink"
    >
      {children}
    </Link>
  );
}
