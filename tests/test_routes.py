"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from unittest.mock import patch
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app
from service import talisman

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        talisman.force_https = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_list_accounts(self):
        """It should list all persisted accounts."""
        self.assertEqual(self.client.get(BASE_URL).get_json(), [])
        accounts = self._create_accounts(3)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual({a['id'] for a in response.get_json()},
                         {a.id for a in accounts})

    def test_read_account(self):
        """It should read the account identified by its resource URL."""
        account = self._create_accounts(1)[0]
        response = self.client.get(f'{BASE_URL}/{account.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), account.serialize())

    def test_read_missing_account(self):
        """It should return 404 for an unknown account."""
        self.assertEqual(self.client.get(f'{BASE_URL}/99999').status_code, 404)

    def test_update_account(self):
        """It should persist updates without changing the resource identity."""
        account = self._create_accounts(1)[0]
        body = account.serialize()
        body['name'] = 'Updated Customer'
        body['id'] = account.id + 100
        response = self.client.put(f'{BASE_URL}/{account.id}', json=body)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['id'], account.id)
        self.assertEqual(self.client.get(f'{BASE_URL}/{account.id}')
                         .get_json()['name'], 'Updated Customer')

    def test_update_missing_account(self):
        """It should return 404 when updating an unknown account."""
        response = self.client.put(f'{BASE_URL}/99999',
                                   json=AccountFactory().serialize())
        self.assertEqual(response.status_code, 404)

    def test_update_invalid_account(self):
        """It should reject incomplete JSON and unsupported media."""
        account = self._create_accounts(1)[0]
        url = f'{BASE_URL}/{account.id}'
        self.assertEqual(self.client.put(url, json={}).status_code, 400)
        self.assertEqual(self.client.put(url, data='bad').status_code, 415)

    def test_delete_account(self):
        """It should remove only the requested account."""
        accounts = self._create_accounts(2)
        url = f'{BASE_URL}/{accounts[0].id}'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b'')
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(len(self.client.get(BASE_URL).get_json()), 1)

    def test_delete_missing_account(self):
        """It should allow repeated DELETE requests without an error."""
        self.assertEqual(self.client.delete(f'{BASE_URL}/99999').status_code, 204)

    def test_unsupported_method(self):
        """It should reject collection deletion without deleting accounts."""
        self._create_accounts(1)
        response = self.client.delete(BASE_URL)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.get_json()['status'], 405)
        self.assertEqual(len(self.client.get(BASE_URL).get_json()), 1)

    def test_internal_server_error(self):
        """It should return a structured error when persistence fails."""
        with patch.dict(app.config, {'PROPAGATE_EXCEPTIONS': False}):
            with patch('service.routes.Account.all',
                       side_effect=RuntimeError('Database unavailable')):
                response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_json()['status'], 500)
        self.assertNotIn('Database unavailable', response.get_json()['message'])

    def test_security_headers(self):
        """It should attach browser security headers to HTTPS responses."""
        response = self.client.get('/', base_url='https://localhost')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['X-Frame-Options'], 'SAMEORIGIN')
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response.headers['X-XSS-Protection'], '1; mode=block')
        self.assertIn("default-src 'self'", response.headers['Content-Security-Policy'])
        self.assertIn('max-age=', response.headers['Strict-Transport-Security'])

    def test_https_redirect(self):
        """It should redirect insecure requests when HTTPS is required."""
        with patch.object(talisman, 'force_https', True):
            response = self.client.get('/accounts', base_url='http://localhost')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], 'https://localhost/accounts')

    def test_allowed_cors_origin(self):
        """It should allow the configured frontend without credential sharing."""
        response = self.client.get(BASE_URL, headers={'Origin': 'http://localhost:3000'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], 'http://localhost:3000')
        self.assertNotIn('Access-Control-Allow-Credentials', response.headers)

    def test_unapproved_cors_origin(self):
        """It should not grant browser access to an unapproved origin."""
        response = self.client.get(BASE_URL, headers={'Origin': 'https://untrusted.example'})
        self.assertNotIn('Access-Control-Allow-Origin', response.headers)

    def test_cors_preflight(self):
        """It should permit JSON requests from the configured frontend."""
        response = self.client.options(BASE_URL, headers={
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('POST', response.headers['Access-Control-Allow-Methods'])
        self.assertIn('Content-Type', response.headers['Access-Control-Allow-Headers'])
