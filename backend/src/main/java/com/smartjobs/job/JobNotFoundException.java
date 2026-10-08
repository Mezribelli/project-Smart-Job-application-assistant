package com.smartjobs.job;

public class JobNotFoundException extends RuntimeException {
    public JobNotFoundException(Long id) {
        super("Job offer " + id + " was not found");
    }
}
