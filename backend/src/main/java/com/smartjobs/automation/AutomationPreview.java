package com.smartjobs.automation;

import java.util.List;

public record AutomationPreview(String url, List<AutomationField> fields, boolean submissionConfirmed) {}
