Feature: Basic Text Capture
  As a user
  I want to capture text notes via API
  So that I can save my thoughts for later enrichment

  Scenario: Successfully capture text
    Given the API is running
    When I send a POST request with body '{"content": "Remember to buy milk", "source": "quick_note"}'
    Then the response status code should be 201
    And the response should contain "capture_id"
    And the response should contain "status" with value "queued"

  Scenario: Capture with validation error
    Given the API is running
    When I send a POST request with body '{"source": "quick_note"}'
    Then the response status code should be 422
