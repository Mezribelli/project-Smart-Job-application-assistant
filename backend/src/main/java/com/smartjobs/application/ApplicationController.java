package com.smartjobs.application;

import com.smartjobs.job.JobOffer;
import com.smartjobs.job.JobOfferController;
import com.smartjobs.profile.Profile;
import com.smartjobs.profile.ProfileController;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/applications")
@CrossOrigin(origins = "http://localhost:5173")
public class ApplicationController {
    private final ApplicationRepository applications;
    private final ProfileController profiles;
    private final JobOfferController jobs;

    public ApplicationController(ApplicationRepository applications, ProfileController profiles, JobOfferController jobs) {
        this.applications = applications; this.profiles = profiles; this.jobs = jobs;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public JobApplication create(@RequestParam Long profileId, @RequestParam Long jobId,
                                 @RequestParam(required = false, defaultValue = "") String notes) {
        Profile profile = profiles.get(profileId);
        JobOffer job = jobs.get(jobId);
        return applications.save(new JobApplication(profile, job, notes));
    }

    @GetMapping
    public List<JobApplication> list(@RequestParam Long profileId) {
        return applications.findByProfileId(profileId);
    }

    @GetMapping("/dashboard")
    public DashboardResponse dashboard(@RequestParam Long profileId) {
        List<JobApplication> items = list(profileId);
        Map<ApplicationStatus, Long> counts = new EnumMap<>(ApplicationStatus.class);
        for (ApplicationStatus status : ApplicationStatus.values()) {
            counts.put(status, items.stream().filter(item -> item.getStatus() == status).count());
        }
        return new DashboardResponse(items.size(), counts);
    }

    @PatchMapping("/{id}")
    public JobApplication update(@PathVariable Long id, @RequestBody ApplicationRequest request) {
        JobApplication application = applications.findById(id)
                .orElseThrow(() -> new ApplicationNotFoundException(id));
        application.update(request.status(), request.notes());
        return applications.save(application);
    }
}
