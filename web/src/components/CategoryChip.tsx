interface CategoryChipProps {
  readonly title: string;
  readonly color: string;
}

/** A small dot + category name, used to tag a keyword page by category. */
export function CategoryChip({ title, color }: CategoryChipProps) {
  return (
    <span className="inline-flex items-center gap-1.5 text-[13px] text-ink-muted">
      <span
        aria-hidden
        className="h-2 w-2 rounded-full"
        style={{ backgroundColor: color }}
      />
      {title}
    </span>
  );
}
