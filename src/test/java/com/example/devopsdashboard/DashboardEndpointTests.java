package com.example.devopsdashboard;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT, properties = {
        // Use the actual environment placeholder names rather than overriding deployment.*.
        "APP_NAME=Pipeline Test Dashboard",
        "APP_VERSION=v2-test",
        "APP_ENVIRONMENT=integration-test",
        "DEPLOYMENT_MESSAGE=Version 2 deployed by the test pipeline.",
        "COMMIT_SHA=0123456789abcdef0123456789abcdef01234567"
})
@AutoConfigureMockMvc
class DashboardEndpointTests {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private TestRestTemplate http;

    @Test
    void dashboardRootServesAnHtmlDocument() {
        // A real local request follows the welcome-page forward; MockMvc alone does not.
        var response = http.getForEntity("/", String.class);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getHeaders().getContentType()).isNotNull();
        assertThat(response.getHeaders().getContentType().isCompatibleWith(MediaType.TEXT_HTML)).isTrue();
        assertThat(response.getBody())
                .isNotBlank()
                .matches("(?is)\\s*<!doctype\\s+html>\\s*<html\\b[^>]*>\\s*"
                        + "<head\\b[^>]*>.*?</head>\\s*<body\\b[^>]*>.*?</body>\\s*</html>\\s*")
                .containsPattern("(?is)<title\\b[^>]*>\\s*[^<\\s].*?</title>")
                .containsPattern("(?is)<main\\b[^>]*>.*?</main>");
    }

    @Test
    void infoReturnsEnvironmentConfiguredMetadataAsJson() throws Exception {
        mockMvc.perform(get("/api/info").accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON))
                .andExpect(header().string(HttpHeaders.CACHE_CONTROL, "no-store"))
                .andExpect(jsonPath("$.name").value("Pipeline Test Dashboard"))
                .andExpect(jsonPath("$.version").value("v2-test"))
                .andExpect(jsonPath("$.environment").value("integration-test"))
                .andExpect(jsonPath("$.message").value("Version 2 deployed by the test pipeline."))
                .andExpect(jsonPath("$.commitSha").value("0123456789abcdef0123456789abcdef01234567"));
    }

    @Test
    void healthReportsUpWithoutExposingDetails() throws Exception {
        mockMvc.perform(get("/actuator/health").accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.status").value("UP"))
                .andExpect(jsonPath("$.components").doesNotExist())
                .andExpect(jsonPath("$.details").doesNotExist());
    }

    @Test
    void livenessProbeReportsUp() throws Exception {
        mockMvc.perform(get("/actuator/health/liveness"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("UP"));
    }

    @Test
    void readinessProbeReportsUp() throws Exception {
        mockMvc.perform(get("/actuator/health/readiness"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("UP"));
    }
}
