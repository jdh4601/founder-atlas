import { CategoryLegend } from "@/components/CategoryLegend";
import { ForceGraphClient } from "@/components/ForceGraphClient";
import { getContentDir } from "@/lib/contentDir";
import { getSiteData } from "@/lib/site";

export default function MapPage() {
  const { taxonomy, graph } = getSiteData(getContentDir());

  return (
    <div>
      <div className="border-b border-line">
        <CategoryLegend categories={taxonomy.categories} />
      </div>
      <ForceGraphClient graph={graph} />
    </div>
  );
}
