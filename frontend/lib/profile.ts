import type { StudentMoveInProfile } from "@/types";

/** Client-side mirror of backend missing_required_fields(). */
export function missingRequiredFields(
  profile: StudentMoveInProfile,
): string[] {
  const missing: string[] = [];
  if (!profile.school_name && !profile.dorm_name) {
    missing.push("school_or_dorm_name");
  }
  if (profile.room_type === "unknown") {
    missing.push("room_type");
  }
  if (!profile.move_in_date) {
    missing.push("move_in_date");
  }
  if (profile.budget_total == null) {
    missing.push("budget_total");
  }
  return missing;
}
