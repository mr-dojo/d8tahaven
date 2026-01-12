Feature: Basic Text Capture
  As a user of the PDC system
  I want to capture text content via API
  So that it can be enriched and stored for later retrieval

  Background:
    Given the capture service is running
    And the Redis queue is available
    And the database is available

  # ============================================================================
  # Happy Path Scenarios
  # ============================================================================

  Scenario: Successfully capture text with minimal fields
    When I POST to "/v1/capture" with JSON:
      """
      {
        "content": "This is my note about AI agents and context collection",
        "source": "manual_entry"
      }
      """
    Then the response status code should be 201
    And the response should contain a "capture_id" field
    And the "capture_id" should be a valid UUID
    And the response should contain a "status" field with value "queued"
    And the response should contain a "queued_at" timestamp
    And the response time should be less than 100 milliseconds
    And a task should be queued in Redis for enrichment
    And the task should contain the captured content

  Scenario: Successfully capture text with full metadata
    When I POST to "/v1/capture" with JSON:
      """
      {
        "content": "Strategic planning notes for Phoenix project",
        "source": "meeting_notes",
        "metadata": {
          "project": "Phoenix",
          "priority": "high",
          "tags": ["planning", "strategy"]
        }
      }
      """
    Then the response status code should be 201
    And the response should contain a "capture_id" field
    And the response should contain a "status" field with value "queued"
    And the metadata should be preserved in the queued task
    And the queued task metadata should contain "project" with value "Phoenix"
    And the queued task metadata should contain "priority" with value "high"
    And the queued task metadata should contain "tags" array with 2 items

  Scenario: Successfully capture text with custom timestamp
    When I POST to "/v1/capture" with JSON:
      """
      {
        "content": "Backdated note from yesterday",
        "source": "manual_entry",
        "captured_at": "2024-01-14T10:30:00Z"
      }
      """
    Then the response status code should be 201
    And the response should contain a "capture_id" field
    And the queued task should have "captured_at" set to "2024-01-14T10:30:00Z"

  Scenario: Capture text with special characters and formatting
    When I POST to "/v1/capture" with JSON:
      """
      {
        "content": "Text with special chars: émojis 🚀, quotes \"test\", and\nnewlines",
        "source": "test"
      }
      """
    Then the response status code should be 201
    And the response should contain a "capture_id" field
    And the queued task content should exactly match the original content

  # ============================================================================
  # Validation Error Scenarios
  # ============================================================================

  Scenario: Reject request with missing content field
    When I POST to "/v1/capture" with JSON:
      """
      {
        "source": "manual_entry"
      }
      """
    Then the response status code should be 422
    And the response should contain an error about "content"
    And the error message should indicate "required"
    And no task should be queued in Redis

  Scenario: Reject request with empty content
    When I POST to "/v1/capture" with JSON:
      """
      {
        "content": "",
        "source": "manual_entry"
      }
      """
    Then the response status code should be 422
    And the response should contain an error about "content"
    And the error message should indicate content cannot be empty
    And no task should be queued in Redis

  Scenario: Reject request with whitespace-only content
    When I POST to "/v1/capture" with JSON:
      """
      {
        "content": "   \n  \t  ",
        "source": "manual_entry"
      }
      """
    Then the response status code should be 422
    And the response should contain an error about "content"
    And no task should be queued in Redis

  Scenario: Reject request with missing source field
    When I POST to "/v1/capture" with JSON:
      """
      {
        "content": "Some content here"
      }
      """
    Then the response status code should be 422
    And the response should contain an error about "source"
    And the error message should indicate "required"
    And no task should be queued in Redis

  Scenario: Reject request with content exceeding maximum length
    Given a text content of 101000 characters
    When I POST to "/v1/capture" with that content
    Then the response status code should be 422
    And the response should contain an error about "content"
    And the error message should indicate maximum length is 100000 characters
    And no task should be queued in Redis

  Scenario: Reject request with invalid JSON
    When I POST to "/v1/capture" with malformed JSON:
      """
      {
        "content": "test"
        "source": "manual_entry"
      }
      """
    Then the response status code should be 422
    And the response should contain an error about JSON parsing
    And no task should be queued in Redis

  Scenario: Reject request with invalid captured_at timestamp
    When I POST to "/v1/capture" with JSON:
      """
      {
        "content": "Test content",
        "source": "manual_entry",
        "captured_at": "not-a-timestamp"
      }
      """
    Then the response status code should be 422
    And the response should contain an error about "captured_at"
    And no task should be queued in Redis

  # ============================================================================
  # Performance Scenarios
  # ============================================================================

  Scenario: Capture responds quickly under normal load
    Given I have 10 capture requests ready
    When I send all requests sequentially
    Then all responses should return within 100 milliseconds each
    And all 10 tasks should be queued in Redis
    And all 10 responses should have status code 201

  Scenario: Capture handles large but valid content efficiently
    Given a text content of 50000 characters
    When I POST to "/v1/capture" with that content
    Then the response status code should be 201
    And the response time should be less than 100 milliseconds
    And the full content should be preserved in the queued task

  # ============================================================================
  # Edge Cases
  # ============================================================================

  Scenario: Capture with minimal valid content
    When I POST to "/v1/capture" with JSON:
      """
      {
        "content": "x",
        "source": "test"
      }
      """
    Then the response status code should be 201
    And the response should contain a "capture_id" field

  Scenario: Capture with maximum valid content length
    Given a text content of exactly 100000 characters
    When I POST to "/v1/capture" with that content
    Then the response status code should be 201
    And the response should contain a "capture_id" field
    And the queued task should contain all 100000 characters

  Scenario: Capture with empty metadata object
    When I POST to "/v1/capture" with JSON:
      """
      {
        "content": "Test content",
        "source": "manual_entry",
        "metadata": {}
      }
      """
    Then the response status code should be 201
    And the response should contain a "capture_id" field
    And the queued task should have an empty metadata object

  Scenario: Capture with null metadata
    When I POST to "/v1/capture" with JSON:
      """
      {
        "content": "Test content",
        "source": "manual_entry",
        "metadata": null
      }
      """
    Then the response status code should be 201
    And the response should contain a "capture_id" field

  Scenario: Capture without metadata field (should use default)
    When I POST to "/v1/capture" with JSON:
      """
      {
        "content": "Test content",
        "source": "manual_entry"
      }
      """
    Then the response status code should be 201
    And the queued task should have an empty or null metadata field

  # ============================================================================
  # API Authentication & Headers (Future Enhancement)
  # ============================================================================

  @future
  Scenario: Reject request without API key
    Given API authentication is enabled
    When I POST to "/v1/capture" without an API key
    Then the response status code should be 401
    And the response should indicate authentication is required

  @future
  Scenario: Reject request with invalid API key
    Given API authentication is enabled
    When I POST to "/v1/capture" with an invalid API key
    Then the response status code should be 401
    And the response should indicate invalid credentials

  # ============================================================================
  # System Failure Scenarios
  # ============================================================================

  @integration
  Scenario: Handle Redis unavailability gracefully
    Given Redis is unavailable
    When I POST to "/v1/capture" with JSON:
      """
      {
        "content": "Test content",
        "source": "manual_entry"
      }
      """
    Then the response status code should be 503
    And the response should indicate the service is temporarily unavailable
    And the error message should mention queue unavailability

  @integration
  Scenario: Capture succeeds even if database is slow
    Given the database is responding slowly
    When I POST to "/v1/capture" with JSON:
      """
      {
        "content": "Test content",
        "source": "manual_entry"
      }
      """
    Then the response status code should be 201
    And the response time should be less than 100 milliseconds
    And the task should be queued successfully
