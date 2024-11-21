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

DATABASE_URI=os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL="/accounts"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"]=True
        app.config["DEBUG"]=False
        app.config["SQLALCHEMY_DATABASE_URI"]=DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client=app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts=[]
        for _ in range(count):
            account=AccountFactory()
            response=self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account=response.get_json()
            account.id=new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response=self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp=self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data=resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account=AccountFactory()
        response=self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location=response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account=response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response=self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account=AccountFactory()
        response=self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...
    def test_read_an_account(self):
        account={
            'name': 'John Doe',
            'email': 'johndoe@example.com',
            'address': '123 Main St',
            'phone_number': '555-1234',  # Optional field
            'date_joined': '2024-01-01'  # Optional field, if needed
        }

        created_response=self.client.post(BASE_URL, json = account)
        created_data=created_response.get_json()
        account_id=created_data['id']
        get_response=self.client.get(f'{BASE_URL}/{account_id}', content_type = 'application/json')
        retrieved_data=get_response.get_json()
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieved_data['email'], 'johndoe@example.com')
        self.assertEqual(retrieved_data['name'], 'John Doe') 
        self.assertEqual(retrieved_data['address'], '123 Main St')
        self.assertEqual(retrieved_data['phone_number'], '555-1234')
        self.assertEqual(retrieved_data['date_joined'], '2024-01-01')

    def test_account_not_found(self):
        response=self.client.get(f'{BASE_URL}/0')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_an_account(self):
        account=AccountFactory()
        response=self.client.post(f'{BASE_URL}', json = account.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_account=response.get_json()
        account_id=new_account['id']
        new_account['name'] = "Something Known"
        response=self.client.put(f'{BASE_URL}/{account_id}', json = new_account)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_account=response.get_json()
        self.assertEqual(updated_account['name'], 'Something Known')

    def test_update_non_updatable_field(self):
        account=AccountFactory()
        response=self.client.post(f'{BASE_URL}', json = account.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_account=response.get_json()
        account_id=new_account['id']
        new_account['id'] = 999

        response=self.client.put(f'{BASE_URL}/{account_id}', json = new_account)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_account_not_found(self):
        response=self.client.put(f'{BASE_URL}/9999', json = {'name': 'not found'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_an_account(self):
        account=AccountFactory()
        response=self.client.post(f'{BASE_URL}', json = account.serialize())
        data=response.get_json()
        account_id=data['id']

        response=self.client.delete(f'{BASE_URL}/{account_id}')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def delete_account_not_found(self):
        response=self.client.delete(f'{BASE_URL}/9999')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_method_not_allowed(self):
        response=self.client.delete(f'{BASE_URL}')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_list_accounts(self):
        self._create_accounts(5)
        response=self.client.get(f'{BASE_URL}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data=response.get_json()
        self.assertEqual(len(data), 5)