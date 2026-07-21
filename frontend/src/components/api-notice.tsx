import type { ApiResult } from "@/lib/api";

type ApiNoticeProps = {
  results: ApiResult<unknown>[];
};

export function ApiNotice({ results }: ApiNoticeProps) {
  const errors = results.filter((result) => !result.ok).map((result) => (result.ok ? "" : result.error));
  if (!errors.length) {
    return null;
  }
  return (
    <div className="api-notice" role="status">
      <strong>FastAPI chưa sẵn sàng</strong>
      <span>{errors[0]}</span>
    </div>
  );
}
