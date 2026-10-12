package com.example.devopsdashboard;

import org.springframework.http.CacheControl;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class InfoController {

    private final DeploymentMetadata metadata;

    public InfoController(DeploymentMetadata metadata) {
        this.metadata = metadata;
    }

    @GetMapping("/api/info")
    public ResponseEntity<DeploymentMetadata> info() {
        // Always fetch current metadata when demonstrating a new deployment.
        return ResponseEntity.ok().cacheControl(CacheControl.noStore()).body(metadata);
    }
}
