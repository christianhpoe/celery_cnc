import type { TaskState } from "./types";

export const STATE_COLORS: Record<TaskState, string> = {
  PENDING: "var(--dag-state-pending)",
  RECEIVED: "var(--dag-state-received)",
  STARTED: "var(--dag-state-started)",
  RETRY: "var(--dag-state-retry)",
  SUCCESS: "var(--dag-state-success)",
  FAILURE: "var(--dag-state-failure)",
  REVOKED: "var(--dag-state-revoked)",
};

export const STATE_LABELS: Record<TaskState, string> = {
  PENDING: "Pending",
  RECEIVED: "Received",
  STARTED: "Started",
  RETRY: "Retry",
  SUCCESS: "Success",
  FAILURE: "Failure",
  REVOKED: "Revoked",
};

export const DEFAULT_STATE_ORDER: TaskState[] = [
  "STARTED",
  "RETRY",
  "FAILURE",
  "PENDING",
  "RECEIVED",
  "SUCCESS",
  "REVOKED",
];
