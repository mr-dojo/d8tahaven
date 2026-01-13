Feature: File Upload Capture
  As a user
  I want to upload files (PDF, DOCX, TXT) via API
  So that I can capture document content for enrichment

  Scenario: Successfully upload a TXT file
    Given the API is running
    When I upload a TXT file with content "Hello from a text file"
    Then the response status code should be 201
    And the response should contain "capture_id"
    And the response should contain "status" with value "queued"

  Scenario: Successfully upload a PDF file
    Given the API is running
    When I upload a valid PDF file
    Then the response status code should be 201
    And the response should contain "capture_id"

  Scenario: Reject unsupported file type
    Given the API is running
    When I upload a file with extension ".exe"
    Then the response status code should be 415

  Scenario: Reject file exceeding size limit
    Given the API is running
    When I upload a file larger than 10MB
    Then the response status code should be 413
