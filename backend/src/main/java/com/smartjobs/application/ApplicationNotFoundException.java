package com.smartjobs.application;

public class ApplicationNotFoundException extends RuntimeException {
    public ApplicationNotFoundException(Long id) { super("Application " + id + " was not found"); }
}
