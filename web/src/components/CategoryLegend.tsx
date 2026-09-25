interface CategoryLegendItem {
  readonly slug: string;
  readonly title: string;
  readonly color: string;
}

interface CategoryLegendProps {
  readonly categories: readonly CategoryLegendItem[];
}

/** Horizontal legend of category dot + title, scrollable on mobile. */
export function CategoryLegend({ categories }: CategoryLegendProps) {
  return (
    <div className="flex gap-x-5 gap-y-2 overflow-x-auto whitespace-nowrap px-5 py-3 text-[13px] text-ink-muted">
      {categories.map((category) => (
        <span key={category.slug} className="inline-flex items-center gap-1.5">
          <span
            aria-hidden
            className="h-2.5 w-2.5 shrink-0 rounded-full"
            style={{ backgroundColor: category.color }}
          />
          {category.title}
        </span>
      ))}
    </div>
  );
}
