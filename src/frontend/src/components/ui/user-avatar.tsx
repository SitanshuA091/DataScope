"use client";

import { useState } from "react";

function getInitials(name?: string | null, email?: string | null) {
  const source = (name ?? "").trim() || (email ?? "").trim();
  if (!source) return "?";
  const parts = source.split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }
  return source.slice(0, 2).toUpperCase();
}

export function UserAvatar({
  name,
  email,
  avatarUrl,
  className = "h-10 w-10",
}: {
  name?: string | null;
  email?: string | null;
  avatarUrl?: string | null;
  className?: string;
}) {
  const [failed, setFailed] = useState(false);

  if (avatarUrl && !failed) {
    return (
      <img
        alt={name ?? "User avatar"}
        className={`${className} rounded-full border border-slate-200 object-cover`}
        onError={() => setFailed(true)}
        referrerPolicy="no-referrer"
        src={avatarUrl}
      />
    );
  }

  return (
    <div
      className={`${className} flex items-center justify-center rounded-full bg-blue-600 text-sm font-semibold text-white`}
    >
      {getInitials(name, email)}
    </div>
  );
}