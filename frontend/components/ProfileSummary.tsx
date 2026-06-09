import type { StudentMoveInProfile } from "@/types";
import { formatCurrency, formatDate } from "@/lib/format";

export function ProfileSummary({
  profile,
  missingFields,
}: {
  profile: StudentMoveInProfile;
  missingFields: string[];
}) {
  const rows: [string, string | null][] = [
    ["School", profile.school_name],
    ["Dorm", profile.dorm_name],
    ["Room type", profile.room_type !== "unknown" ? profile.room_type : null],
    ["Move-in", profile.move_in_date ? formatDate(profile.move_in_date) : null],
    [
      "Budget",
      profile.budget_total != null
        ? formatCurrency(profile.budget_total)
        : null,
    ],
    [
      "Transport",
      profile.transportation_mode !== "unknown"
        ? profile.transportation_mode
        : null,
    ],
    ["Preference", profile.budget_preference],
  ];

  return (
    <div className="card p-5">
      <h3 className="section-title">Your profile</h3>
      <dl className="mt-4 space-y-3 text-sm">
        {rows.map(([label, value]) => (
          <div key={label} className="flex justify-between gap-4 border-b border-border/60 pb-2 last:border-0 last:pb-0">
            <dt className="text-muted">{label}</dt>
            <dd className="text-right font-medium text-espresso">
              {value ?? <span className="text-muted/50">—</span>}
            </dd>
          </div>
        ))}
      </dl>

      {profile.already_owned_items.length > 0 && (
        <div className="mt-4 rounded-lg bg-sage/10 px-3 py-2">
          <p className="text-xs font-medium text-sage">Already own</p>
          <p className="mt-1 text-sm text-espresso/80">
            {profile.already_owned_items.join(", ")}
          </p>
        </div>
      )}

      {profile.roommate_items.length > 0 && (
        <div className="mt-2 rounded-lg bg-cream px-3 py-2">
          <p className="text-xs font-medium text-muted">Roommate brings</p>
          <p className="mt-1 text-sm text-espresso/80">
            {profile.roommate_items.join(", ")}
          </p>
        </div>
      )}

      {missingFields.length > 0 && (
        <div className="mt-4 rounded-lg border border-warning-border bg-warning-light p-3">
          <p className="text-xs font-semibold text-warning">Still needed</p>
          <ul className="mt-1 space-y-0.5 text-sm text-espresso/80">
            {missingFields.map((f) => (
              <li key={f}>{f.replace(/_/g, " ")}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
