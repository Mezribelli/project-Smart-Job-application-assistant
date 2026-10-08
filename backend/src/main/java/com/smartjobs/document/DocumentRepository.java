package com.smartjobs.document;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DocumentRepository extends JpaRepository<ApplicationDocument, Long> {
    List<ApplicationDocument> findByProfileId(Long profileId);
}
