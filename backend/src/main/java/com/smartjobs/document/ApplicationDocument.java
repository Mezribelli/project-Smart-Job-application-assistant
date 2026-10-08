package com.smartjobs.document;

import com.smartjobs.job.JobOffer;
import com.smartjobs.profile.Profile;
import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import java.time.Instant;

@Entity
@Table(name = "application_documents")
public class ApplicationDocument {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @ManyToOne(optional = false)
    private Profile profile;
    @ManyToOne(optional = false)
    private JobOffer job;
    @Enumerated(EnumType.STRING)
    private DocumentType type;
    @Enumerated(EnumType.STRING)
    private DocumentStatus status = DocumentStatus.DRAFT;
    @NotBlank
    @Column(columnDefinition = "TEXT")
    private String content;
    private Instant createdAt = Instant.now();

    protected ApplicationDocument() {}

    public ApplicationDocument(Profile profile, JobOffer job, DocumentType type, String content) {
        this.profile = profile;
        this.job = job;
        this.type = type;
        this.content = content;
    }

    public Long getId() { return id; }
    public Profile getProfile() { return profile; }
    public JobOffer getJob() { return job; }
    public DocumentType getType() { return type; }
    public DocumentStatus getStatus() { return status; }
    public String getContent() { return content; }
    public Instant getCreatedAt() { return createdAt; }
    public void edit(String content) { this.content = content; this.status = DocumentStatus.DRAFT; }
    public void approve() { this.status = DocumentStatus.APPROVED; }
}
