package com.smartjobs.automation;

import com.smartjobs.profile.Profile;
import com.smartjobs.profile.ProfileNotFoundException;
import com.smartjobs.profile.ProfileRepository;
import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/automation")
public class AutomationController {
    private final ProfileRepository profiles;
    private final SeleniumAutomationService seleniumService;

    public AutomationController(ProfileRepository profiles, SeleniumAutomationService seleniumService) {
        this.profiles = profiles;
        this.seleniumService = seleniumService;
    }

    @PostMapping("/preview")
    public AutomationPreview preview(@RequestParam Long profileId, @RequestParam String url) {
        Profile profile = profiles.findById(profileId).orElseThrow(() -> new ProfileNotFoundException(profileId));
        boolean hasPhone = profile.getPhone() != null && !profile.getPhone().isBlank();
        return new AutomationPreview(url, List.of(
                new AutomationField("full_name", profile.getFullName(), true),
                new AutomationField("email", profile.getEmail(), true),
                new AutomationField("phone", profile.getPhone(), hasPhone),
                new AutomationField("resume_upload", "Profile document required", false)
        ), false);
    }

    @PostMapping("/submit")
    public AutomationPreview submit(@RequestBody AutomationPreview preview) {
        if (!preview.submissionConfirmed()) {
            throw new IllegalStateException("Submission requires explicit user confirmation");
        }
        return preview;
    }

    @PostMapping("/selenium-apply")
    public SeleniumAutomationService.AutomationExecutionResult seleniumApply(
            @RequestParam Long profileId,
            @RequestParam String url,
            @RequestParam(required = false, defaultValue = "") String coverLetter,
            @RequestParam(required = false, defaultValue = "false") boolean confirm
    ) {
        Profile profile = profiles.findById(profileId).orElseThrow(() -> new ProfileNotFoundException(profileId));
        return seleniumService.fillAndSubmitApplication(url, profile, coverLetter, confirm);
    }
}
