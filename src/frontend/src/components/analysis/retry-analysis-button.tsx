import { Button } from "@/components/ui/button";

export function RetryAnalysisButton({
  disabled,
  isRetrying,
  onRetry,
}: {
  disabled?: boolean;
  isRetrying?: boolean;
  onRetry: () => void;
}) {
  return (
    <Button disabled={disabled || isRetrying} onClick={onRetry} variant="secondary">
      {isRetrying ? "Retrying..." : "Retry"}
    </Button>
  );
}
