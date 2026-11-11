export function AppLogo({ className = "h-7 w-7" }: { className?: string }) {
  return (
    <>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        alt=""
        className={`${className} shrink-0 dark:hidden`}
        src="/favicon.ico"
      />
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        alt=""
        className={`${className} hidden shrink-0 dark:block`}
        src="/favicon.ico"
      />
    </>
  );
}