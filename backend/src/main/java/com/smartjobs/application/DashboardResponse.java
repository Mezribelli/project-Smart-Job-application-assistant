package com.smartjobs.application;

import java.util.Map;

public record DashboardResponse(long total, Map<ApplicationStatus, Long> byStatus) {}
