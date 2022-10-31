from django.test import TestCase

# Create your tests here.

# Path: subscription/core/tests.py
def test_check_mail_ajax(self):
    response = self.client.get('/check_mail_ajax/', {'email': 'someone@something.com'})
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.content, b'{"success": "Email available"}')

def test_check_phone_ajax(self):
    response = self.client.get('/check_phone_ajax/', {'phone': '+8801712345678'})
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.content, b'{"success": "Phone number available"}')

def test_signin(self):
    response = self.client.get('/signin/')
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'login.html')

def test_register(self):
    response = self.client.post('/register/', {'email': 'someone@something.com', 'password': '12345678', 'phone': '+8801712345678'})
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.content, b'{"success": "Registration successful."}')

def test_login(self):
    response = self.client.post('/login/', {'email': 'someone@something.com', 'password': '12345678'})
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.content, b'{"success": "Login successful."}')

def test_index(self):
    response = self.client.get('/')
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'index.html')
