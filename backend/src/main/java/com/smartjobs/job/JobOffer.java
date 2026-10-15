package com.smartjobs.job;

import jakarta.persistence.CollectionTable;
import jakarta.persistence.Column;
import jakarta.persistence.ElementCollection;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.Table;
import jakarta.validation.constraints.NotBlank;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

@Entity
@Table(name = "job_offers")
public class JobOffer {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @NotBlank
    private String title;
    @NotBlank
    private String company;
    private String location;
    private String employmentType;
    private String url;
    @Column(columnDefinition = "TEXT")
    private String description;
    private Integer minimumExperienceYears;
    private Instant createdAt = Instant.now();

    @Enumerated(EnumType.STRING)
    private JobStatus status = JobStatus.SAVED;

    @ElementCollection(fetch = FetchType.EAGER)
    @CollectionTable(name = "job_offer_skills", joinColumns = @JoinColumn(name = "job_offer_id"))
    private List<String> skills = new ArrayList<>();

    protected JobOffer() {
    }

    public JobOffer(String title, String company, String location, String employmentType, String url,
                    String description, Integer minimumExperienceYears, List<String> skills) {
        this.title = title;
        this.company = company;
        this.location = location;
        this.employmentType = employmentType;
        this.url = url;
        this.description = description;
        this.minimumExperienceYears = minimumExperienceYears;
        this.skills = skills == null ? new ArrayList<>() : new ArrayList<>(skills.stream().filter(Objects::nonNull).toList());
    }

    public Long getId() { return id; }
    public String getTitle() { return title; }
    public String getCompany() { return company; }
    public String getLocation() { return location; }
    public String getEmploymentType() { return employmentType; }
    public String getUrl() { return url; }
    public String getDescription() { return description; }
    public Integer getMinimumExperienceYears() { return minimumExperienceYears; }
    public Instant getCreatedAt() { return createdAt; }
    public JobStatus getStatus() { return status; }
    public List<String> getSkills() { return skills == null ? List.of() : List.copyOf(skills.stream().filter(Objects::nonNull).toList()); }

    public void update(String title, String company, String location, String employmentType, String url,
                       String description, Integer minimumExperienceYears, List<String> skills) {
        this.title = title;
        this.company = company;
        this.location = location;
        this.employmentType = employmentType;
        this.url = url;
        this.description = description;
        this.minimumExperienceYears = minimumExperienceYears;
        this.skills = skills == null ? new ArrayList<>() : new ArrayList<>(skills.stream().filter(Objects::nonNull).toList());
    }

    public void changeStatus(JobStatus status) {
        this.status = status;
    }
}
