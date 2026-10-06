import { Button } from "@/components/ui/button";

export function RetryAnalysisButton({ onRetry }: { onRetry?: () => void }) {
  return (
    <Button disabled={!onRetry} onClick={onRetry} variant="secondary">
      Retry
    </Button>
  );
}
