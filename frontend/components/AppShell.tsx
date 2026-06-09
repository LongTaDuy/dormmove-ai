import { Header } from "./Header";

export function AppShell({
  children,
  sessionId,
}: {
  children: React.ReactNode;
  sessionId?: string | null;
}) {
  return (
    <div className="flex min-h-screen flex-col bg-cream">
      <Header sessionId={sessionId} />
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6 sm:py-8">
        {children}
      </main>
    </div>
  );
}
