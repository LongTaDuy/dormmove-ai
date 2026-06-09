export function LoadingState({ message = "Loading…" }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-muted">
      <div className="h-9 w-9 animate-spin rounded-full border-2 border-border border-t-brand" />
      <p className="text-sm font-medium">{message}</p>
    </div>
  );
}
