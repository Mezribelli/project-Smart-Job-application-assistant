package com.smartjobs.matching;

import com.smartjobs.job.JobNotFoundException;
import com.smartjobs.job.JobOffer;
import com.smartjobs.job.JobOfferRepository;
import com.smartjobs.profile.Profile;
import com.smartjobs.profile.ProfileNotFoundException;
import com.smartjobs.profile.ProfileRepository;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/matching")
@CrossOrigin(origins = "http://localhost:5173")
public class MatchingController {

    private final ProfileRepository profiles;
    private final JobOfferRepository jobs;

    public MatchingController(ProfileRepository profiles, JobOfferRepository jobs) {
        this.profiles = profiles;
        this.jobs = jobs;
    }

    @GetMapping("/profiles/{profileId}/jobs/{jobId}")
    public MatchResponse match(@PathVariable Long profileId, @PathVariable Long jobId) {
        Profile profile = profiles.findById(profileId).orElseThrow(() -> new ProfileNotFoundException(profileId));
        JobOffer job = jobs.findById(jobId).orElseThrow(() -> new JobNotFoundException(jobId));

        Set<String> profileSkillSet = profile.getSkills().stream()
                .map(this::normalize)
                .filter(s -> !s.isBlank())
                .collect(Collectors.toSet());

        Map<String, String> distinctJobSkills = new LinkedHashMap<>();
        for (String skill : job.getSkills()) {
            String norm = normalize(skill);
            if (!norm.isBlank()) {
                distinctJobSkills.putIfAbsent(norm, skill.trim());
            }
        }

        List<String> matching = new ArrayList<>();
        List<String> missing = new ArrayList<>();

        for (Map.Entry<String, String> entry : distinctJobSkills.entrySet()) {
            if (profileSkillSet.contains(entry.getKey())) {
                matching.add(entry.getValue());
            } else {
                missing.add(entry.getValue());
            }
        }

        int totalSkills = distinctJobSkills.size();
        int score = totalSkills == 0 ? 100 : (int) Math.round(100.0 * matching.size() / totalSkills);
        String recommendation;
        if (totalSkills == 0) {
            recommendation = "No specific skills listed for this offer. Your profile is eligible to apply.";
        } else if (score >= 70) {
            recommendation = "This offer is a strong match for your profile.";
        } else {
            recommendation = "Review the missing skills before deciding whether to apply.";
        }

        return new MatchResponse(score, matching, missing, recommendation);
    }

    private String normalize(String value) {
        return value == null ? "" : value.trim().toLowerCase(Locale.ROOT);
    }
}
