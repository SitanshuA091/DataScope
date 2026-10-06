import { Card } from "@/components/ui/card";
import type { DatasetListItem } from "@/types/dataset";

export function SchemaTable({ item }: { item: DatasetListItem | null }) {
  const schema =
    item?.current_version?.schema_json ??
    item?.current_version?.columns_schema ??
    [];

  return (
    <Card className="overflow-hidden">
      <div className="border-b border-slate-200 px-5 py-4">
        <h2 className="text-base font-semibold text-slate-950">Schema</h2>
      </div>
      {schema.length === 0 ? (
        <p className="px-5 py-6 text-sm text-slate-600">
          No schema has been captured yet.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-5 py-3 font-semibold">Column</th>
                <th className="px-5 py-3 font-semibold">Type</th>
                <th className="px-5 py-3 font-semibold">Missing</th>
                <th className="px-5 py-3 font-semibold">Nullable</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {schema.map((column, index) => (
                <tr key={`${String(column.name ?? index)}`}>
                  <td className="px-5 py-3 font-medium text-slate-900">
                    {String(column.name ?? "Unnamed")}
                  </td>
                  <td className="px-5 py-3 text-slate-600">
                    {String(column.dtype ?? column.type ?? "unknown")}
                  </td>
                  <td className="px-5 py-3 text-slate-600">
                    {String(column.missing_count ?? 0)}
                  </td>
                  <td className="px-5 py-3 text-slate-600">
                    {column.nullable === false ? "No" : "Yes"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
