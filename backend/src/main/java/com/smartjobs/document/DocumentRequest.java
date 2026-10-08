package com.smartjobs.document;

import jakarta.validation.constraints.NotBlank;

public record DocumentRequest(@NotBlank String content) {}
