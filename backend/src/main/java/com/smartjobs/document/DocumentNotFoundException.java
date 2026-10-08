package com.smartjobs.document;

public class DocumentNotFoundException extends RuntimeException {
    public DocumentNotFoundException(Long id) { super("Document " + id + " was not found"); }
}
