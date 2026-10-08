package com.smartjobs.matching;

import com.smartjobs.job.JobOffer;
import com.smartjobs.job.JobOfferController;
import com.smartjobs.profile.Profile;
import com.smartjobs.profile.ProfileController;
import java.util.List;
import java.util.Locale;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/matching")
@CrossOrigin(origins = "http://localhost:5173")
public class MatchingController {

    private final ProfileController profiles;
    private final JobOfferController jobs;

    public MatchingController(ProfileController profiles, JobOfferController jobs) {
        this.profiles = profiles;
        this.jobs = jobs;
    }

    @GetMapping("/profiles/{profileId}/jobs/{jobId}")
    public MatchResponse match(@PathVariable Long profileId, @PathVariable Long jobId) {
        Profile profile = profiles.get(profileId);
        JobOffer job = jobs.get(jobId);
        List<String> profileSkills = profile.getSkills().stream().map(this::normalize).toList();
        List<String> matching = job.getSkills().stream()
                .filter(skill -> profileSkills.contains(normalize(skill)))
                .distinct()
                .toList();
        List<String> missing = job.getSkills().stream()
                .filter(skill -> !profileSkills.contains(normalize(skill)))
                .distinct()
                .toList();
        int score = job.getSkills().isEmpty() ? 0 : (int) Math.round(100.0 * matching.size() / job.getSkills().size());
        String recommendation = score >= 70
                ? "This offer is a strong match for your profile."
                : "Review the missing skills before deciding whether to apply.";
        return new MatchResponse(score, matching, missing, recommendation);
    }

    private String normalize(String value) {
        return value == null ? "" : value.trim().toLowerCase(Locale.ROOT);
    }
}
