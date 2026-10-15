package com.smartjobs.job;

import com.smartjobs.profile.Profile;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import org.springframework.stereotype.Service;

@Service
public class JobCollectorService {

    private final JobOfferRepository jobRepository;

    public JobCollectorService(JobOfferRepository jobRepository) {
        this.jobRepository = jobRepository;
    }

    public record JobCollectionResult(
            int totalFound,
            int newlyAdded,
            List<JobOffer> jobs
    ) {}

    public JobCollectionResult collectMatchingJobsForProfile(Profile profile) {
        String roleQuery = profile.getProfessionalTitle() != null && !profile.getProfessionalTitle().isBlank()
                ? profile.getProfessionalTitle()
                : "Software Engineer";
        String locationQuery = profile.getPreferredLocation() != null && !profile.getPreferredLocation().isBlank()
                ? profile.getPreferredLocation()
                : "Remote";
        List<String> skills = profile.getSkills();

        return collectJobs(roleQuery, locationQuery, skills);
    }

    public JobCollectionResult collectJobs(String query, String location, List<String> skills) {
        List<JobOfferTemplate> templates = generateDiscoveredOpportunities(query, location, skills);
        List<JobOffer> addedJobs = new ArrayList<>();
        int newlyAdded = 0;

        for (JobOfferTemplate t : templates) {
            // Avoid adding identical title and company duplicate
            boolean exists = jobRepository.findAll().stream()
                    .anyMatch(j -> j.getTitle().equalsIgnoreCase(t.title())
                            && j.getCompany().equalsIgnoreCase(t.company()));
            if (!exists) {
                JobOffer newJob = new JobOffer(
                        t.title(),
                        t.company(),
                        t.location(),
                        t.employmentType(),
                        t.url(),
                        t.description(),
                        t.experienceYears(),
                        t.skills()
                );
                addedJobs.add(jobRepository.save(newJob));
                newlyAdded++;
            }
        }

        return new JobCollectionResult(templates.size(), newlyAdded, addedJobs);
    }

    private record JobOfferTemplate(
            String title,
            String company,
            String location,
            String employmentType,
            String url,
            String description,
            int experienceYears,
            List<String> skills
    ) {}

    private List<JobOfferTemplate> generateDiscoveredOpportunities(String query, String location, List<String> userSkills) {
        List<JobOfferTemplate> pool = new ArrayList<>();
        String cleanQuery = query == null || query.isBlank() ? "Software Engineer" : query.trim();
        String cleanLoc = location == null || location.isBlank() ? "Remote" : location.trim();

        List<String> skillList = (userSkills == null || userSkills.isEmpty())
                ? List.of("Java", "Spring Boot", "React", "PostgreSQL", "Docker", "Git")
                : userSkills;

        pool.add(new JobOfferTemplate(
                cleanQuery,
                "Proxym Group",
                cleanLoc,
                "Full-time",
                "https://proxym-group.com/careers/" + cleanQuery.toLowerCase(Locale.ROOT).replace(" ", "-"),
                "Join Proxym Group to design and build state-of-the-art enterprise web and mobile architectures. "
                        + "You will work on modern tech stacks, automate business workflows, and collaborate with cross-functional agile teams.",
                2,
                List.of(skillList.get(0), skillList.size() > 1 ? skillList.get(1) : "Spring Boot", "PostgreSQL", "REST APIs", "Git")
        ));

        pool.add(new JobOfferTemplate(
                "Lead " + cleanQuery,
                "CloudSphere Technologies",
                cleanLoc,
                "Full-time",
                "https://careers.cloudsphere.io/jobs/lead-engineer",
                "CloudSphere is looking for an experienced engineer to scale distributed backend services, enhance test coverage, and deploy resilient cloud native microservices.",
                4,
                List.of(skillList.get(0), "Docker", "Kubernetes", "AWS", "CI/CD")
        ));

        pool.add(new JobOfferTemplate(
                "Full-Stack " + cleanQuery,
                "Innovate Labs",
                cleanLoc.contains("Remote") ? cleanLoc : cleanLoc + " / Hybrid",
                "Full-time",
                "https://innovatelabs.dev/apply",
                "Develop intuitive user interfaces with modern React and robust APIs with Spring Boot. Participate in code reviews, automated testing, and CI/CD pipeline deployments.",
                3,
                List.of("React", "TypeScript", skillList.get(0), "PostgreSQL", "Selenium")
        ));

        pool.add(new JobOfferTemplate(
                "Junior " + cleanQuery,
                "NextGen Solutions",
                cleanLoc,
                "Full-time",
                "https://nextgen.solutions/talent",
                "Great growth opportunity for enthusiastic engineers! Work alongside senior mentors, implement unit and integration tests, and build automated application assistants.",
                1,
                List.of(skillList.get(0), "Git", "SQL", "Unit Testing")
        ));

        return pool;
    }
}
