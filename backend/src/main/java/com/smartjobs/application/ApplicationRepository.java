package com.smartjobs.application;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ApplicationRepository extends JpaRepository<JobApplication, Long> {
    List<JobApplication> findByProfileId(Long profileId);
}
