export function ConnectionError({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="card border-warning-border bg-warning-light p-8 text-center">
      <h3 className="text-lg font-semibold text-warning">Cannot connect</h3>
      <p className="mt-2 text-sm text-espresso/80">{message}</p>
      <p className="mt-2 text-xs text-muted">
        Make sure the backend is running at{" "}
        <code className="rounded bg-ivory px-1">localhost:8000</code>.
      </p>
      <button
        type="button"
        onClick={onRetry}
        className="btn-primary mt-6"
        aria-label="Retry backend connection"
      >
        Retry connection
      </button>
    </div>
  );
}
