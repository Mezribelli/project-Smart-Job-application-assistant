package com.smartjobs.job;

import jakarta.validation.constraints.NotBlank;
import java.util.List;

public record JobOfferRequest(
        @NotBlank String title,
        @NotBlank String company,
        String location,
        String employmentType,
        String url,
        String description,
        Integer minimumExperienceYears,
        List<String> skills
) {
}
