export type DatasetVersion = {
  id: string;
  dataset_id: string;
  version_number: number;
  original_filename: string;
  storage_key: string;
  checksum: string;
  file_size: number;
  row_count: number;
  column_count: number;
  schema_json?: Array<Record<string, unknown>>;
  columns_schema?: Array<Record<string, unknown>>;
  validation_status: string;
  validation_error: string | null;
  created_at: string;
};

export type Dataset = {
  id: string;
  workspace_id: string;
  name: string;
  current_version_id: string | null;
  created_at: string;
  updated_at: string;
};

export type DatasetListItem = {
  dataset: Dataset;
  current_version: DatasetVersion | null;
};

export type DatasetOverview = {
  dataset_id: string;
  workspace_id: string;
  dataset_name: string;
  current_version_id: string;
  version_number: number;
  original_filename: string;
  row_count: number;
  column_count: number;
  columns: string[];
  schema_json?: Array<Record<string, unknown>>;
  columns_schema?: Array<Record<string, unknown>>;
  validation_status: string;
  validation_error: string | null;
  created_at: string;
};

export type DatasetUploadResponse = {
  dataset: Dataset;
  version: DatasetVersion;
};
