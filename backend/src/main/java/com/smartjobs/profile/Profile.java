package com.smartjobs.profile;

import jakarta.persistence.CollectionTable;
import jakarta.persistence.ElementCollection;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.Table;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "profiles")
public class Profile {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @NotBlank
    private String fullName;

    @NotBlank
    @Email
    private String email;

    private String phone;
    private String professionalTitle;
    private String education;
    private String preferredLocation;
    private String desiredEmploymentType;
    private Integer yearsOfExperience;

    @ElementCollection
    @CollectionTable(name = "profile_skills", joinColumns = @JoinColumn(name = "profile_id"))
    private List<String> skills = new ArrayList<>();

    protected Profile() {
    }

    public Profile(String fullName, String email, String phone, String professionalTitle,
                   String education, String preferredLocation, String desiredEmploymentType,
                   Integer yearsOfExperience, List<String> skills) {
        this.fullName = fullName;
        this.email = email;
        this.phone = phone;
        this.professionalTitle = professionalTitle;
        this.education = education;
        this.preferredLocation = preferredLocation;
        this.desiredEmploymentType = desiredEmploymentType;
        this.yearsOfExperience = yearsOfExperience;
        this.skills = skills == null ? new ArrayList<>() : new ArrayList<>(skills);
    }

    public Long getId() { return id; }
    public String getFullName() { return fullName; }
    public String getEmail() { return email; }
    public String getPhone() { return phone; }
    public String getProfessionalTitle() { return professionalTitle; }
    public String getEducation() { return education; }
    public String getPreferredLocation() { return preferredLocation; }
    public String getDesiredEmploymentType() { return desiredEmploymentType; }
    public Integer getYearsOfExperience() { return yearsOfExperience; }
    public List<String> getSkills() { return List.copyOf(skills); }

    public void update(String fullName, String email, String phone, String professionalTitle,
                       String education, String preferredLocation, String desiredEmploymentType,
                       Integer yearsOfExperience, List<String> skills) {
        this.fullName = fullName;
        this.email = email;
        this.phone = phone;
        this.professionalTitle = professionalTitle;
        this.education = education;
        this.preferredLocation = preferredLocation;
        this.desiredEmploymentType = desiredEmploymentType;
        this.yearsOfExperience = yearsOfExperience;
        this.skills = skills == null ? new ArrayList<>() : new ArrayList<>(skills);
    }
}
