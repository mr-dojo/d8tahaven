import pytest
from pytest_bdd import given, when, then, scenarios, parsers
from starlette.testclient import TestClient
from src.capture.api import app
import json

scenarios('../features/01-capture-basic.feature')

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def response():
    return {}

@given("the API is running")
def api_running(client):
    pass

@when(parsers.parse("I send a POST request with body '{body}'"))
def send_post_request(client, response, body):
    endpoint = "/v1/capture"
    data = json.loads(body)
    res = client.post(endpoint, json=data)
    response['status_code'] = res.status_code
    response['json'] = res.json()

@then(parsers.parse('the response status code should be {status_code:d}'))
def check_status_code(response, status_code):
    assert response['status_code'] == status_code

@then(parsers.parse('the response should contain "{key}"'))
def check_response_key(response, key):
    assert key in response['json']

@then(parsers.parse('the response should contain "{key}" with value "{value}"'))
def check_response_key_value(response, key, value):
    assert response['json'][key] == value
