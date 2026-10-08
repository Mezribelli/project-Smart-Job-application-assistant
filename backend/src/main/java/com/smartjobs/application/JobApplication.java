package com.smartjobs.application;

import com.smartjobs.job.JobOffer;
import com.smartjobs.profile.Profile;
import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "job_applications")
public class JobApplication {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @ManyToOne(optional = false)
    private Profile profile;
    @ManyToOne(optional = false)
    private JobOffer job;
    @Enumerated(EnumType.STRING)
    private ApplicationStatus status = ApplicationStatus.DRAFT;
    private String notes;
    private Instant createdAt = Instant.now();
    private Instant updatedAt = Instant.now();

    protected JobApplication() {}
    public JobApplication(Profile profile, JobOffer job, String notes) {
        this.profile = profile; this.job = job; this.notes = notes;
    }
    public Long getId() { return id; }
    public Profile getProfile() { return profile; }
    public JobOffer getJob() { return job; }
    public ApplicationStatus getStatus() { return status; }
    public String getNotes() { return notes; }
    public Instant getCreatedAt() { return createdAt; }
    public Instant getUpdatedAt() { return updatedAt; }
    public void update(ApplicationStatus status, String notes) {
        this.status = status; this.notes = notes; this.updatedAt = Instant.now();
    }
}
