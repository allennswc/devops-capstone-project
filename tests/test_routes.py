"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app

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

    # ADD YOUR TEST CASES HERE ...
    def test_read_account(self):
        """It should read an account when given ID"""
        account = self._create_accounts(1)[0]
        resp = self.client.get(
            f"{BASE_URL}/{account.id}", content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["name"], account.name)


    def test_read_account_not_found(self):
        """It should not read an unfound account """
        account = self._create_accounts(1)[0]
        resp = self.client.get(
            f"{BASE_URL}/0")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_account(self):
        """It should update an account when given ID"""
        # Make a test account and check if it got created
        samp_account = AccountFactory()
        response = self.client.post(
                BASE_URL,
                json=samp_account.serialize())
        self.assertEqual(response.status_code,status.HTTP_201_CREATED)
        
        # Update account name and email information
        samp2_accountinfo = response.get_json()
        samp2_accountinfo['name'] = "Updated Name String"
        samp2_accountinfo['email'] = "newemail@website.com"

        # Push the change to the database
        response2 = self.client.put(
            f"{BASE_URL}/{samp2_accountinfo['id']}",
            json=samp2_accountinfo)
        
        # Check if the information got changed
        self.assertEqual(response2.status_code,status.HTTP_200_OK)
        self.assertEqual(response2.get_json()['name'],"Updated Name String")
        self.assertEqual(response2.get_json()['email'],"newemail@website.com")

    def test_update_account_not_found(self):
        """It should not update an unfound account """
        account = self._create_accounts(1)[0]
        resp = self.client.put(
            f"{BASE_URL}/0")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


    def test_delete_account(self):
        """It should delete an account when given ID"""
        # Make a test account and check if it got created
        samp_account = self._create_accounts(1)[0]
        response = self.client.delete(
                f"{BASE_URL}/{samp_account.id}")

        self.assertEqual(response.status_code,status.HTTP_204_NO_CONTENT)

    def test_delete_account_not_found(self):
        """It should not do anything when given wrong ID"""
        # Make a test account and check if it got created
        samp_account = self._create_accounts(1)[0]
        response = self.client.delete(
                f"{BASE_URL}/0")

        self.assertEqual(response.status_code,status.HTTP_404_NOT_FOUND)


    def test_get_account_list(self):
        """It should return list of accounts"""
        # Make a test account and check if it got created
        numaccounts = 5
        self._create_accounts(numaccounts)
        response = self.client.get(
                f"{BASE_URL}")

        self.assertEqual(response.status_code,status.HTTP_200_OK)

        self.assertEqual(len(response.get_json()),numaccounts)

        
    def test_method_not_allowed(self):
        """It should not allow an illegal method call"""
        resp = self.client.delete(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)