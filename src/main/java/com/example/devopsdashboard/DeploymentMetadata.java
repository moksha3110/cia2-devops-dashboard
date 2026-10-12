package com.example.devopsdashboard;

import com.fasterxml.jackson.annotation.JsonInclude;
import org.springframework.boot.context.properties.ConfigurationProperties;

/** Deployment values come from application.yml and its environment placeholders. */
@ConfigurationProperties(prefix = "deployment")
@JsonInclude(JsonInclude.Include.NON_EMPTY)
public record DeploymentMetadata(
        String name,
        String version,
        String environment,
        String message,
        String commitSha
) {
}
