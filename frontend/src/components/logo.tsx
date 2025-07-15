export function Logo({ className }: { className?: string }) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <img
        src="/logo.svg"
        alt="ScholarAI Logo"
        width={32}
        height={32}
        className="text-primary"
      />
      <span className="text-xl font-headline font-bold">ScholarAI</span>
    </div>
  );
}
