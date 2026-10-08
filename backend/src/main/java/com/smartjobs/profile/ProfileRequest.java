package com.smartjobs.profile;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import java.util.List;

public record ProfileRequest(
        @NotBlank String fullName,
        @NotBlank @Email String email,
        String phone,
        String professionalTitle,
        String education,
        String preferredLocation,
        String desiredEmploymentType,
        Integer yearsOfExperience,
        List<String> skills
) {
}
