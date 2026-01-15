Feature: File Upload Capture
  As a user
  I want to upload files (PDF, DOCX, TXT) via API
  So that I can capture document content for later enrichment

  Background:
    Given the API is running

  # ============================================================================
  # Happy Path Scenarios
  # ============================================================================

  @happy-path
  Scenario: Successfully upload a TXT file
    When I upload a file "sample.txt" with content "This is my important note"
    Then the response status code should be 201
    And the response should contain "capture_id"
    And the response should contain "status" with value "completed"
    And the response should contain "filename" with value "sample.txt"
    And the response should contain "content_type" with value ".txt"

  @happy-path
  Scenario: Successfully upload a PDF file
    When I upload a valid PDF file "document.pdf"
    Then the response status code should be 201
    And the response should contain "capture_id"
    And the response should contain "extracted_text_preview"

  @happy-path
  Scenario: Successfully upload a DOCX file
    When I upload a valid DOCX file "report.docx"
    Then the response status code should be 201
    And the response should contain "capture_id"
    And the response should contain "content_type" with value ".docx"

  @happy-path
  Scenario: Duplicate file content returns existing capture_id
    Given I have previously uploaded content "Unique document content"
    When I upload a file "duplicate.txt" with content "Unique document content"
    Then the response status code should be 201
    And the response should return the same capture_id as before

  # ============================================================================
  # Validation Error Scenarios
  # ============================================================================

  @validation
  Scenario: Reject unsupported file type
    When I upload a file "image.png"
    Then the response status code should be 415
    And the response should contain error "Unsupported file type"

  @validation
  Scenario: Reject file exceeding size limit
    When I upload a file larger than 10MB
    Then the response status code should be 413
    And the response should contain error "File too large"

  @validation
  Scenario: Reject file with empty extracted text
    When I upload a blank PDF file "empty.pdf"
    Then the response status code should be 422
    And the response should contain error "Extracted text is empty"

  # ============================================================================
  # Encoding Detection Scenarios
  # ============================================================================

  @encoding
  Scenario: Handle UTF-8 encoded TXT file
    When I upload a UTF-8 file with special characters "café résumé naïve"
    Then the response status code should be 201
    And the extracted text should contain "café résumé naïve"

  @encoding
  Scenario: Handle Latin-1 encoded TXT file
    When I upload a Latin-1 encoded file
    Then the response status code should be 201
    And the text should be properly decoded

  @encoding
  Scenario: Reject file with undecodable content
    When I upload a file with binary garbage that cannot be decoded
    Then the response status code should be 422
    And the response should contain error "Failed to decode"

  # ============================================================================
  # Edge Cases
  # ============================================================================

  @edge-case
  Scenario: Handle file without extension
    When I upload a file with no extension
    Then the response status code should be 415

  @edge-case
  Scenario: Handle very long extracted text
    When I upload a file with content exceeding 32000 characters
    Then the response status code should be 201
    And the embedding should be generated from truncated text

  @edge-case
  Scenario: Handle file with only whitespace content
    When I upload a file "whitespace.txt" with content "   \n\t\n   "
    Then the response status code should be 422
    And the response should contain error "Extracted text is empty"
