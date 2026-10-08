package com.smartjobs.profile;

import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/profiles")
@CrossOrigin(origins = "http://localhost:5173")
public class ProfileController {

    private final ProfileRepository profiles;

    public ProfileController(ProfileRepository profiles) {
        this.profiles = profiles;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public Profile create(@Valid @RequestBody ProfileRequest request) {
        return profiles.save(toProfile(request));
    }

    @GetMapping
    public List<Profile> list() {
        return profiles.findAll();
    }

    @GetMapping("/{id}")
    public Profile get(@PathVariable Long id) {
        return profiles.findById(id).orElseThrow(() -> new ProfileNotFoundException(id));
    }

    @PutMapping("/{id}")
    public Profile update(@PathVariable Long id, @Valid @RequestBody ProfileRequest request) {
        Profile profile = get(id);
        profile.update(request.fullName(), request.email(), request.phone(), request.professionalTitle(),
                request.education(), request.preferredLocation(), request.desiredEmploymentType(),
                request.yearsOfExperience(), request.skills());
        return profiles.save(profile);
    }

    private Profile toProfile(ProfileRequest request) {
        return new Profile(request.fullName(), request.email(), request.phone(), request.professionalTitle(),
                request.education(), request.preferredLocation(), request.desiredEmploymentType(),
                request.yearsOfExperience(), request.skills());
    }
}
