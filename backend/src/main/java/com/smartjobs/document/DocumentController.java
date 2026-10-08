package com.smartjobs.document;

import com.smartjobs.job.JobOffer;
import com.smartjobs.job.JobOfferController;
import com.smartjobs.profile.Profile;
import com.smartjobs.profile.ProfileController;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/documents")
@CrossOrigin(origins = "http://localhost:5173")
public class DocumentController {
    private final DocumentRepository documents;
    private final ProfileController profiles;
    private final JobOfferController jobs;

    public DocumentController(DocumentRepository documents, ProfileController profiles, JobOfferController jobs) {
        this.documents = documents;
        this.profiles = profiles;
        this.jobs = jobs;
    }

    @PostMapping("/generate")
    @ResponseStatus(HttpStatus.CREATED)
    public ApplicationDocument generate(@RequestParam Long profileId, @RequestParam Long jobId,
                                        @RequestParam DocumentType type) {
        Profile profile = profiles.get(profileId);
        JobOffer job = jobs.get(jobId);
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
        if (type == DocumentType.CV) {
            return "CV\n\n" + profile.getFullName() + "\n" + profile.getProfessionalTitle()
                    + "\n\nSkills: " + String.join(", ", profile.getSkills())
                    + "\n\nTarget role: " + job.getTitle() + " at " + job.getCompany();
        }
        return "Cover letter\n\nDear " + job.getCompany() + " recruitment team,\n\n"
                + "I am " + profile.getFullName() + ", applying for the " + job.getTitle()
                + " position. My relevant skills include " + String.join(", ", profile.getSkills()) + ".\n\n"
                + "Sincerely,\n" + profile.getFullName();
    }
}
