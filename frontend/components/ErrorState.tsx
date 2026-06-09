export function ErrorState({
  title = "Something went wrong",
  message,
  onRetry,
}: {
  title?: string;
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="card border-danger-border bg-danger-light p-6 text-center">
      <h3 className="font-semibold text-danger">{title}</h3>
      <p className="mt-2 text-sm text-espresso/80">{message}</p>
      {onRetry && (
        <button type="button" onClick={onRetry} className="btn-secondary mt-4">
          Try again
        </button>
      )}
    </div>
  );
}
