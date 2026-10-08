package com.smartjobs.profile;

public class ProfileNotFoundException extends RuntimeException {
    public ProfileNotFoundException(Long id) {
        super("Profile " + id + " was not found");
    }
}
