import { Card } from "@/components/ui/card";

export function ChartGallery() {
  return (
    <Card className="p-5">
      <h2 className="text-base font-semibold text-slate-950">Charts</h2>
      <p className="mt-2 text-sm text-slate-600">
        Generated plot artifacts will appear here when analysis results include
        visual outputs.
      </p>
    </Card>
  );
}
