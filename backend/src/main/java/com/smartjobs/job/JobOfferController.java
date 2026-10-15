package com.smartjobs.job;

import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/jobs")
@CrossOrigin(origins = {"${app.cors.allowed-origins:http://localhost:5173}", "${app.cors.sandbox-origin:}"})
public class JobOfferController {

    private final JobOfferRepository jobs;

    public JobOfferController(JobOfferRepository jobs) {
        this.jobs = jobs;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public JobOffer create(@Valid @RequestBody JobOfferRequest request) {
        return jobs.save(toJob(request));
    }

    @GetMapping
    public List<JobOffer> search(@RequestParam(required = false) String keyword,
                                 @RequestParam(required = false) String location,
                                 @RequestParam(required = false) String skill,
                                 @RequestParam(required = false) JobStatus status) {
        List<JobOffer> result = keyword == null || keyword.isBlank()
                ? jobs.findAll()
                : jobs.findByTitleContainingIgnoreCaseOrCompanyContainingIgnoreCaseOrDescriptionContainingIgnoreCase(
                        keyword, keyword, keyword);
        return result.stream()
                .filter(job -> location == null || location.isBlank()
                        || containsIgnoreCase(job.getLocation(), location))
                .filter(job -> skill == null || skill.isBlank()
                        || job.getSkills().stream().anyMatch(item -> containsIgnoreCase(item, skill)))
                .filter(job -> status == null || job.getStatus() == status)
                .toList();
    }

    @GetMapping("/{id}")
    public JobOffer get(@PathVariable Long id) {
        return jobs.findById(id).orElseThrow(() -> new JobNotFoundException(id));
    }

    @PutMapping("/{id}")
    public JobOffer update(@PathVariable Long id, @Valid @RequestBody JobOfferRequest request) {
        JobOffer job = get(id);
        job.update(request.title(), request.company(), request.location(), request.employmentType(),
                request.url(), request.description(), request.minimumExperienceYears(), request.skills());
        return jobs.save(job);
    }

    @PatchMapping("/{id}/status")
    public JobOffer changeStatus(@PathVariable Long id, @RequestParam JobStatus value) {
        JobOffer job = get(id);
        job.changeStatus(value);
        return jobs.save(job);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable Long id) {
        if (!jobs.existsById(id)) {
            throw new JobNotFoundException(id);
        }
        jobs.deleteById(id);
    }

    private JobOffer toJob(JobOfferRequest request) {
        return new JobOffer(request.title(), request.company(), request.location(), request.employmentType(),
                request.url(), request.description(), request.minimumExperienceYears(), request.skills());
    }

    private boolean containsIgnoreCase(String value, String query) {
        return value != null && value.toLowerCase().contains(query.toLowerCase());
    }
}
