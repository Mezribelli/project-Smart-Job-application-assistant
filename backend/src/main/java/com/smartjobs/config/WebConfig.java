package com.smartjobs.config;

import java.util.ArrayList;
import java.util.List;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * Single source of truth for cross-origin access. Controllers must not declare their own
 * {@code @CrossOrigin}: a handler-level annotation overrides this mapping and silently pins the
 * API to whichever origin it names.
 */
@Configuration
public class WebConfig implements WebMvcConfigurer {

    private static final List<String> LOCAL_ORIGINS = List.of(
            "http://localhost:5173",
            "http://127.0.0.1:5173");

    private final List<String> allowedOrigins;

    public WebConfig(
            @Value("${BASE44_PREVIEW_MODE:}") String previewMode,
            @Value("${BASE44_PUBLIC_HOST_SUFFIX:}") String publicHostSuffix) {
        List<String> origins = new ArrayList<>(LOCAL_ORIGINS);

        // Sandbox preview only: the frontend is served from https://3000-<public host suffix>, a
        // different site from this API, so that origin has to be allowed. The override is gated on
        // BASE44_PREVIEW_MODE being exactly "1"; when the flag is absent or anything else, the
        // allowlist keeps its original local development behaviour.
        if ("1".equals(previewMode) && publicHostSuffix != null && !publicHostSuffix.isBlank()) {
            origins.add("https://3000-" + publicHostSuffix.trim());
        }

        this.allowedOrigins = List.copyOf(origins);
    }

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/**")
                .allowedOrigins(allowedOrigins.toArray(String[]::new))
                .allowedMethods("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
                .allowedHeaders("*")
                .allowCredentials(true);
    }
}
