package com.smartjobs.document;

import com.smartjobs.job.JobNotFoundException;
import com.smartjobs.job.JobOffer;
import com.smartjobs.job.JobOfferRepository;
import com.smartjobs.profile.Profile;
import com.smartjobs.profile.ProfileNotFoundException;
import com.smartjobs.profile.ProfileRepository;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/documents")
public class DocumentController {
    private final DocumentRepository documents;
    private final ProfileRepository profiles;
    private final JobOfferRepository jobs;

    public DocumentController(DocumentRepository documents, ProfileRepository profiles, JobOfferRepository jobs) {
        this.documents = documents;
        this.profiles = profiles;
        this.jobs = jobs;
    }

    @PostMapping("/generate")
    @ResponseStatus(HttpStatus.CREATED)
    public ApplicationDocument generate(@RequestParam Long profileId, @RequestParam Long jobId,
                                        @RequestParam DocumentType type) {
        Profile profile = profiles.findById(profileId).orElseThrow(() -> new ProfileNotFoundException(profileId));
        JobOffer job = jobs.findById(jobId).orElseThrow(() -> new JobNotFoundException(jobId));
        return documents.save(new ApplicationDocument(profile, job, type, createDraft(profile, job, type)));
    }

    @GetMapping
    public List<ApplicationDocument> list(@RequestParam Long profileId) {
        return documents.findByProfileId(profileId);
    }

    @PutMapping("/{id}")
    public ApplicationDocument edit(@PathVariable Long id, @Valid @RequestBody DocumentRequest request) {
        ApplicationDocument document = get(id);
        document.edit(request.content());
        return documents.save(document);
    }

    @PostMapping("/{id}/approve")
    public ApplicationDocument approve(@PathVariable Long id) {
        ApplicationDocument document = get(id);
        document.approve();
        return documents.save(document);
    }

    private ApplicationDocument get(Long id) {
        return documents.findById(id).orElseThrow(() -> new DocumentNotFoundException(id));
    }

    private String createDraft(Profile profile, JobOffer job, DocumentType type) {
        String titleLine = (profile.getProfessionalTitle() != null && !profile.getProfessionalTitle().isBlank())
                ? profile.getProfessionalTitle() + "\n"
                : "";
        String skillsText = profile.getSkills().isEmpty() ? "Not specified" : String.join(", ", profile.getSkills());

        if (type == DocumentType.CV) {
            return "CV\n\n" + profile.getFullName() + "\n" + titleLine
                    + "\nSkills: " + skillsText
                    + "\n\nTarget role: " + job.getTitle() + " at " + job.getCompany();
        }
        return "Cover letter\n\nDear " + job.getCompany() + " recruitment team,\n\n"
                + "I am " + profile.getFullName() + ", applying for the " + job.getTitle()
                + " position. My relevant skills include " + skillsText + ".\n\n"
                + "Sincerely,\n" + profile.getFullName();
    }
}
