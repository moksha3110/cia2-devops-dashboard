# syntax=docker/dockerfile:1

# Build from source and run the tests; a host JDK or prebuilt JAR is not required.
FROM eclipse-temurin:21-jdk-jammy AS build
WORKDIR /workspace

COPY .mvn/ .mvn/
COPY mvnw pom.xml ./
COPY src/ src/

# Calling sh avoids relying on an executable bit from a Windows checkout.
# Normalize CRLF in case Git converted the Unix wrapper on Windows.
RUN sed -i 's/\r$//' mvnw \
    && sh ./mvnw --batch-mode --no-transfer-progress clean package

# The runtime contains the JRE and packaged application, without Maven or sources.
FROM eclipse-temurin:21-jre-alpine AS runtime
RUN addgroup -S -g 10001 app \
    && adduser -S -D -H -u 10001 -G app app
WORKDIR /app
COPY --from=build --chown=10001:10001 /workspace/target/devops-dashboard.jar ./app.jar

USER 10001:10001
EXPOSE 8080

# BusyBox wget is included in Alpine; no extra HTTP client needs installing.
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD wget -q -T 3 -O /dev/null http://127.0.0.1:8080/actuator/health || exit 1

# Exec form lets Java receive container stop signals for graceful shutdown.
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75.0", "-jar", "/app/app.jar"]
