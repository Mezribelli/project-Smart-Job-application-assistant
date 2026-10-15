package com.smartjobs;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.smartjobs.application.ApplicationRequest;
import com.smartjobs.application.ApplicationStatus;
import com.smartjobs.automation.AutomationPreview;
import com.smartjobs.document.DocumentRequest;
import com.smartjobs.job.JobOfferRequest;
import com.smartjobs.job.JobStatus;
import com.smartjobs.profile.ProfileRequest;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@Transactional
class FullIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void profileLifecycleAndValidation() throws Exception {
        ProfileRequest invalidRequest = new ProfileRequest(
                "", "not-an-email", null, null, null, null, null, null, List.of()
        );

        mockMvc.perform(post("/api/profiles")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(invalidRequest)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error", notNullValue()));

        ProfileRequest validRequest = new ProfileRequest(
                "Jane Doe", "jane@example.com", "+1234567890", "Senior Engineer",
                "MSc Computer Science", "Remote", "FULL_TIME", 8, List.of("Java", "Spring Boot", "Docker")
        );

        String createResponse = mockMvc.perform(post("/api/profiles")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(validRequest)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id", notNullValue()))
                .andExpect(jsonPath("$.fullName", is("Jane Doe")))
                .andReturn().getResponse().getContentAsString();

        long profileId = objectMapper.readTree(createResponse).get("id").asLong();

        mockMvc.perform(get("/api/profiles/" + profileId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.email", is("jane@example.com")));

        ProfileRequest updateRequest = new ProfileRequest(
                "Jane Doe Updated", "jane@example.com", "+1234567890", "Staff Engineer",
                "MSc Computer Science", "Remote", "FULL_TIME", 9, List.of("Java", "Spring Boot", "Kubernetes")
        );

        mockMvc.perform(put("/api/profiles/" + profileId)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(updateRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.fullName", is("Jane Doe Updated")))
                .andExpect(jsonPath("$.professionalTitle", is("Staff Engineer")));
    }

    @Test
    void jobOfferLifecycleAndSearch() throws Exception {
        JobOfferRequest jobRequest = new JobOfferRequest(
                "Backend Developer", "Acme Corp", "Remote", "Full-time",
                "https://example.com/apply", "Exciting opportunity for a backend engineer.", 3,
                List.of("Java", "PostgreSQL", "Docker")
        );

        String createResponse = mockMvc.perform(post("/api/jobs")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(jobRequest)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id", notNullValue()))
                .andExpect(jsonPath("$.status", is("SAVED")))
                .andReturn().getResponse().getContentAsString();

        long jobId = objectMapper.readTree(createResponse).get("id").asLong();

        // Search by keyword
        mockMvc.perform(get("/api/jobs?keyword=Acme"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(greaterThanOrEqualTo(1))))
                .andExpect(jsonPath("$[0].company", is("Acme Corp")));

        // Search by skill
        mockMvc.perform(get("/api/jobs?skill=Java"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(greaterThanOrEqualTo(1))));

        // Change status
        mockMvc.perform(patch("/api/jobs/" + jobId + "/status?value=APPLIED"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status", is("APPLIED")));

        // Delete job
        mockMvc.perform(delete("/api/jobs/" + jobId))
                .andExpect(status().isNoContent());

        // Verify deleted
        mockMvc.perform(get("/api/jobs/" + jobId))
                .andExpect(status().isNotFound());
    }

    @Test
    void matchingLogicCalculation() throws Exception {
        ProfileRequest profileReq = new ProfileRequest(
                "Alice", "alice@example.com", null, "Java Developer",
                null, null, null, null, List.of("Java", "spring boot", "SQL")
        );
        String profRes = mockMvc.perform(post("/api/profiles")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(profileReq)))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();
        long profileId = objectMapper.readTree(profRes).get("id").asLong();

        JobOfferRequest jobReq = new JobOfferRequest(
                "Java Dev", "TechCorp", "Remote", "Full-time", null, "Desc", 2,
                List.of("JAVA", "Spring Boot", "AWS", "Docker")
        );
        String jobRes = mockMvc.perform(post("/api/jobs")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(jobReq)))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();
        long jobId = objectMapper.readTree(jobRes).get("id").asLong();

        // Distinct job skills: JAVA, Spring Boot, AWS, Docker (4)
        // Matching: JAVA, Spring Boot (2) -> Score: 50%
        mockMvc.perform(get("/api/matching/profiles/" + profileId + "/jobs/" + jobId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.score", is(50)))
                .andExpect(jsonPath("$.matchingSkills", hasItems("JAVA", "Spring Boot")))
                .andExpect(jsonPath("$.missingSkills", hasItems("AWS", "Docker")));
    }

    @Test
    void documentGenerationEditingAndApproval() throws Exception {
        ProfileRequest profileReq = new ProfileRequest(
                "Bob", "bob@example.com", "555-0100", "Frontend Dev",
                null, null, null, null, List.of("React", "TypeScript")
        );
        String profRes = mockMvc.perform(post("/api/profiles")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(profileReq)))
                .andReturn().getResponse().getContentAsString();
        long profileId = objectMapper.readTree(profRes).get("id").asLong();

        JobOfferRequest jobReq = new JobOfferRequest(
                "React Dev", "WebInc", "City", "Full-time", null, "Desc", 1, List.of("React")
        );
        String jobRes = mockMvc.perform(post("/api/jobs")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(jobReq)))
                .andReturn().getResponse().getContentAsString();
        long jobId = objectMapper.readTree(jobRes).get("id").asLong();

        // Generate CV draft
        String docRes = mockMvc.perform(post("/api/documents/generate")
                        .param("profileId", String.valueOf(profileId))
                        .param("jobId", String.valueOf(jobId))
                        .param("type", "CV"))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.status", is("DRAFT")))
                .andExpect(jsonPath("$.content", containsString("Bob")))
                .andExpect(jsonPath("$.content", containsString("Frontend Dev")))
                .andReturn().getResponse().getContentAsString();
        long docId = objectMapper.readTree(docRes).get("id").asLong();

        // Edit document
        mockMvc.perform(put("/api/documents/" + docId)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(new DocumentRequest("Customized CV content"))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content", is("Customized CV content")))
                .andExpect(jsonPath("$.status", is("DRAFT")));

        // Approve document
        mockMvc.perform(post("/api/documents/" + docId + "/approve"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status", is("APPROVED")));
    }

    @Test
    void applicationTrackingAndPartialPatch() throws Exception {
        ProfileRequest profileReq = new ProfileRequest(
                "Charlie", "charlie@example.com", null, null, null, null, null, null, List.of()
        );
        String profRes = mockMvc.perform(post("/api/profiles")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(profileReq)))
                .andReturn().getResponse().getContentAsString();
        long profileId = objectMapper.readTree(profRes).get("id").asLong();

        JobOfferRequest jobReq = new JobOfferRequest(
                "Analyst", "DataCo", null, null, null, null, null, List.of()
        );
        String jobRes = mockMvc.perform(post("/api/jobs")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(jobReq)))
                .andReturn().getResponse().getContentAsString();
        long jobId = objectMapper.readTree(jobRes).get("id").asLong();

        // Create application with initial notes
        String appRes = mockMvc.perform(post("/api/applications")
                        .param("profileId", String.valueOf(profileId))
                        .param("jobId", String.valueOf(jobId))
                        .param("notes", "Submitted via referral"))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.status", is("DRAFT")))
                .andExpect(jsonPath("$.notes", is("Submitted via referral")))
                .andReturn().getResponse().getContentAsString();
        long appId = objectMapper.readTree(appRes).get("id").asLong();

        // Partial update: status only, notes must NOT be overwritten with null
        mockMvc.perform(patch("/api/applications/" + appId)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(new ApplicationRequest(ApplicationStatus.APPLIED, null))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status", is("APPLIED")))
                .andExpect(jsonPath("$.notes", is("Submitted via referral")));

        // Partial update: notes only, status must NOT be overwritten with null
        mockMvc.perform(patch("/api/applications/" + appId)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(new ApplicationRequest(null, "Interview scheduled"))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status", is("APPLIED")))
                .andExpect(jsonPath("$.notes", is("Interview scheduled")));

        // Check dashboard
        mockMvc.perform(get("/api/applications/dashboard?profileId=" + profileId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.total", is(1)))
                .andExpect(jsonPath("$.byStatus.APPLIED", is(1)));
    }

    @Test
    void automationPreviewAndConfirmationRequirement() throws Exception {
        ProfileRequest profileReq = new ProfileRequest(
                "Diana", "diana@example.com", "123-456", null, null, null, null, null, List.of()
        );
        String profRes = mockMvc.perform(post("/api/profiles")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(profileReq)))
                .andReturn().getResponse().getContentAsString();
        long profileId = objectMapper.readTree(profRes).get("id").asLong();

        // Preview
        String previewRes = mockMvc.perform(post("/api/automation/preview")
                        .param("profileId", String.valueOf(profileId))
                        .param("url", "https://careers.example.com/apply/123"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.submissionConfirmed", is(false)))
                .andExpect(jsonPath("$.fields", hasSize(4)))
                .andReturn().getResponse().getContentAsString();

        AutomationPreview unconfirmed = objectMapper.readValue(previewRes, AutomationPreview.class);

        // Submit unconfirmed should fail
        mockMvc.perform(post("/api/automation/submit")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(unconfirmed)))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.error", containsString("requires explicit user confirmation")));

        // Submit confirmed should succeed
        AutomationPreview confirmed = new AutomationPreview(unconfirmed.url(), unconfirmed.fields(), true);
        mockMvc.perform(post("/api/automation/submit")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(confirmed)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.submissionConfirmed", is(true)));
    }

    @Test
    void jobCollectionAndSeleniumAutomation() throws Exception {
        ProfileRequest profileReq = new ProfileRequest(
                "Edward", "edward@example.com", "+1-555-0199", "Backend Engineer",
                "BSc Software Engineering", "Remote", "Full-time", 3, List.of("Java", "Spring Boot", "PostgreSQL")
        );
        String profRes = mockMvc.perform(post("/api/profiles")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(profileReq)))
                .andReturn().getResponse().getContentAsString();
        long profileId = objectMapper.readTree(profRes).get("id").asLong();

        // Automated Job Collection
        mockMvc.perform(post("/api/jobs/collect-matching")
                        .param("profileId", String.valueOf(profileId)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalFound", greaterThanOrEqualTo(1)))
                .andExpect(jsonPath("$.newlyAdded", greaterThanOrEqualTo(1)));

        // Selenium automated form filling and submission
        mockMvc.perform(post("/api/automation/selenium-apply")
                        .param("profileId", String.valueOf(profileId))
                        .param("url", "https://careers.example.com/apply/proxym")
                        .param("coverLetter", "Tailored cover letter for Proxym Group")
                        .param("confirm", "true"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status", is("SUCCESS")))
                .andExpect(jsonPath("$.submitted", is(true)))
                .andExpect(jsonPath("$.fieldsFilled", hasSize(greaterThanOrEqualTo(3))));
    }
}
