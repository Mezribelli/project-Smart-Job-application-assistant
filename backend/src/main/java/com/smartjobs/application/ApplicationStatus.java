package com.smartjobs.application;

/**
 * Pipeline stages of a tracked application. The names match the vocabulary used by the dashboard
 * UI, its status styles and the project README (Draft, Applied, Interviewing, Offered, Rejected).
 */
public enum ApplicationStatus {
    DRAFT, READY_TO_APPLY, APPLIED, INTERVIEWING, OFFERED, REJECTED
}
