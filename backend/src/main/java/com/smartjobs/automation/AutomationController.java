package com.smartjobs.automation;

import com.smartjobs.profile.Profile;
import com.smartjobs.profile.ProfileController;
import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/automation")
@CrossOrigin(origins = {"${app.cors.allowed-origins:http://localhost:5173}", "${app.cors.sandbox-origin:}"})
public class AutomationController {
    private final ProfileController profiles;

    public AutomationController(ProfileController profiles) { this.profiles = profiles; }

    @PostMapping("/preview")
    public AutomationPreview preview(@RequestParam Long profileId, @RequestParam String url) {
        Profile profile = profiles.get(profileId);
        return new AutomationPreview(url, List.of(
                new AutomationField("full_name", profile.getFullName(), true),
                new AutomationField("email", profile.getEmail(), true),
                new AutomationField("phone", profile.getPhone(), profile.getPhone() != null),
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
}
