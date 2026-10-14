import { Button } from "@/components/ui/button";

export function CancelAnalysisButton({
  disabled,
  isCancelling,
  onCancel,
}: {
  disabled?: boolean;
  isCancelling?: boolean;
  onCancel: () => void;
}) {
  return (
    <Button
      disabled={disabled || isCancelling}
      onClick={onCancel}
      variant="secondary"
    >
      {isCancelling ? "Cancelling..." : "Cancel"}
    </Button>
  );
}
