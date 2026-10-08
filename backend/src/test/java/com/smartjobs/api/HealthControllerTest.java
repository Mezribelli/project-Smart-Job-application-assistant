package com.smartjobs.api;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class HealthControllerTest {

    @Test
    void returnsBackendHealth() {
        HealthController controller = new HealthController();

        assertThat(controller.health())
                .containsEntry("status", "UP")
                .containsEntry("service", "backend");
    }
}
