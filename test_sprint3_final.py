import pytest
import os
import sqlite3
from unittest import mock
from unittest.mock import Mock
from unittest.mock import patch
from system import Menu, Jobs, System

@pytest.fixture #creates instance of System and calls Main Menu
def system_instance():
  s1 = System()
  s1.initMenu()
  return s1

@pytest.fixture #removes existing accounts from db while testing
def temp_remove_accounts(system_instance): 
  """Sets up the database for testing by saving and clearing any persistent records, 
  after a test finishes test records are cleared and saved records are restored."""
  data = {}
  # tables with FKs referencing other tables should come after the referenced table
  tables = ['accounts', 'friends', 'experiences', 'jobs']
  # store each of the tables into a dictionary
  for table in tables:
    system_instance.cursor.execute(f"SELECT * FROM {table}")
    data[table] = system_instance.cursor.fetchall()

  # delete all records from the the accounts table, 
  # and should auto delete all records from tables with FK to accounts
  if len(data[tables[0]]):
    system_instance.cursor.execute("DELETE FROM accounts")
    system_instance.conn.commit()
  # delete all records from the jobs table
  if len(data[tables[-1]]):
    system_instance.cursor.execute("DELETE FROM jobs")
  system_instance.conn.commit()
    
  yield
  # delete any testing records from the database 
  system_instance.cursor.execute("DELETE FROM accounts")
  system_instance.cursor.execute("DELETE FROM jobs")
  # restore saved records to all tables 
  for table in tables:
    if len(data[table]):
      # add a ? to the list of parameters for each column in the table
      parameters = f"({','.join('?' for col in data[table][0])})"
      query = f"INSERT INTO {table} VALUES {parameters}"
      system_instance.cursor.executemany(query, data[table])
  system_instance.conn.commit()


@pytest.fixture
def account_settings(temp_remove_accounts):
    # Create an instance of the System class or initialize your system
  # delete the value of the table job to do the test 
    conn = sqlite3.connect("accounts.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM accounts")
    conn.commit()
    conn.close()
    system = System()
    # Perform any necessary setup or data insertion for the test
    # For example, insert test data into the database
    conn = sqlite3.connect("accounts.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO accounts (username, password, fName, lName,university,major) VALUES (?, ?, ?, ?,?,?)", ('username', "Password123!", "Patrick","Shugerts","USF","CS"))
    conn.commit()
    conn.close()
    system.user.login("username","Patrick","Shugerts","usf","cs",True,True,True,"English")
    # Return the system instance for the test
    return system

@pytest.fixture #test that user can input first and last name when registering
def name_register(system_instance, temp_remove_accounts, capsys):
  inputs = ['2', 'ahmad', 'ah', 'mad','usf','cs', 'Asibai1$', 'Asibai1$', 'ahmad', 'Asibai1$', '0', '0']
  with mock.patch('builtins.input', side_effect=inputs):
    system_instance.home_page()
  captured = capsys.readouterr()
  output = captured.out
  assert  'Account created successfully.' in output
  
  yield

def test_notloggedin(system_instance, temp_remove_accounts, capsys): #tests that signing up from the general option in useful links can only be accessed when a user is not logged in
  input = ['5', '1', '0', '0', '0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
  captured = capsys.readouterr()
  output = captured.out
  assert '[1] Sign Up' in output

def test_loggedin(system_instance, name_register, capsys):  #tests that signing up is not an option from the general option in useful links to logged in users
  input = ['1', 'ahmad', 'Asibai1$', '5', '1', '0', '0', '0', '0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
  captured = capsys.readouterr()
  output = captured.out
  assert  '[1] Help Center' in output

def test_signup1(system_instance, temp_remove_accounts, capsys): #tests that registering from the signup general option is valid and saves the new users information in the db
  input = ['5', '1', '1', '2', 'ahmad', 'ah', 'mad', 'usf','cs','Asibai1$', 'Asibai1$', 'ahmad', 'Asibai1$', '0', '0', '0', '0', '0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
  captured = capsys.readouterr()
  output = captured.out
  assert '[2] Register' in output
  assert  'Enter Username: ' in output
  assert 'Enter First Name: ' in output
  assert 'Enter Last Name: ' in output
  assert 'Enter Password: ' in output
  assert 'Confirm Password: ' in output
  assert 'Account created successfully.' in output
  assert 'You Have Successfully Logged In!' in output
  username = "ahmad"
  cursor = system_instance.conn.cursor()
  cursor.execute('Select * From accounts where username = (?);', (username,))
  result = cursor.fetchone()
  assert type(result) == tuple
  assert result[0] == 'ahmad' and result[1] == system_instance.encryption('Asibai1$') and result[2] == 'ah' and result[3] == 'mad'

def test_signup2(system_instance, name_register, capsys): #tests that a registered  user can login from the general signup option
  input = ['5', '1', '1', '1', 'ahmad', 'Asibai1$', '0', '0', '0', '0', '0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
  captured = capsys.readouterr()
  output = captured.out
  assert '[1] Login' in output
  assert 'Enter Username: ' in output
  assert 'Enter Password: ' in output
  assert 'You Have Successfully Logged In!' in output

def test_helpcenter(system_instance, temp_remove_accounts, capsys): #tests that the help center can be accessed from the general useful links option
  input = ['5', '1', '2', '0', '0', '0', '0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
  captured = capsys.readouterr()
  output = captured.out.split('\n')
  assert output[37] == "We're here to help"

def test_about(system_instance, temp_remove_accounts, capsys): #tests that about can be accessed from the general useful links option
  input = ['5', '1', '3', '0', '0', '0', '0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
  captured = capsys.readouterr()
  output = captured.out.split('\n')
  assert output[37] == "In College: Welcome to In College, the world's largest college student"

def test_press(system_instance, temp_remove_accounts, capsys): #tests that the press can be accessed from the general useful links option
  input = ['5', '1', '4', '0', '0', '0', '0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
  captured = capsys.readouterr()
  output = captured.out.split('\n')
  assert output[37] == 'In College Pressroom: Stay on top of the latest news, updates, and reports'

def test_blog(system_instance, temp_remove_accounts, capsys): #tests that the blog can be accessed from the general useful links option
  input = ['5', '1', '5', '0', '0', '0', '0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
  captured = capsys.readouterr()
  output = captured.out.split('\n')
  assert output[36] == 'Under Construction'
  
def test_careers(system_instance, temp_remove_accounts, capsys): #tests that the careers section can be accessed from the general useful links option
  input = ['5', '1', '6', '0', '0', '0', '0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
  captured = capsys.readouterr()
  output = captured.out.split('\n')
  assert output[36] == 'Under Construction'
  
def test_developers(system_instance, temp_remove_accounts, capsys): #tests that the developers section can be accessed from the general useful links option
  input = ['5', '1', '7', '0', '0', '0', '0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
  captured = capsys.readouterr()
  output = captured.out.split('\n')
  assert output[36] == 'Under Construction'

def test_guestnotloggedin(system_instance, temp_remove_accounts, capsys): #tests that guest controls cannot be accessed without being logged in
  input = ['6', '5', '0', '0', '0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
  captured = capsys.readouterr()
  output = captured.out.split('\n')
  assert '[1] Guest Controls' not in output
  assert output[47] == '[0] Exit'

def test_guestloggedin(system_instance, name_register, capsys):  #tests that guest controls can be accessed when a user is logged in
  input = ['1', 'ahmad', 'Asibai1$', '6', '5', '0', '0', '0', '0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
  captured = capsys.readouterr()
  output = captured.out
  assert '[1] Guest Controls' in output

def test_controlsoff(system_instance, name_register, capsys):  #tests that guest controls are all off
  input = ['1', 'ahmad', 'Asibai1$', '6', '5', '1', '1', '2', '3', '0', '0', '0', '0', '0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
  captured = capsys.readouterr()
  output = captured.out
  assert '[1] Email [OFF]' in output
  assert '[2] SMS [OFF]' in output
  assert '[3] Targeted Advertising [OFF]' in output
  username = 'ahmad'
  cursor = system_instance.conn.cursor()
  cursor.execute('Select * From account_settings where username = (?);', (username,))
  result = cursor.fetchone()
  assert type(result) == tuple
  assert result[1] == 0 and result[2] == 0 and result[3] == 0

#story: As a new user, I want to be able to learn about important information about InCollege
# inCollage important information link  appear in the home page menu 
def test_inCollegeImportantInformationHomePage():
  system_instance = System()  # Create an instance of the System class
  system_instance.initMenu()
  # Get the menu items from the homePage
  menu_items = system_instance.homePage.selections
  # Check if the "InCollege Important Links" option exists in the home page manu
  inCollege_links_option = next(
    (item
     for item in menu_items if item['label'] == 'InCollege Important Links'),
    None)
  # Assert that the option exists
  assert inCollege_links_option is not None


# inCollage Important information link appear in the main manu when user logged in 
def test_inCollageImportantInformationMainMenu():
  system_instance = System()
  # Call the initMenu method to initialize the menu
  system_instance.initMenu()
  # Get the menu items from the mainMenu
  menu_items = system_instance.mainMenu.selections
  # Check if the "InCollege Important Links" option exists in the main manu
  inCollege_links_option = next(
    (item
     for item in menu_items if item['label'] == 'InCollege Important Links'),
    None)
  # Assert that the option exists
  assert inCollege_links_option is not None


# test to check when the user select the option 6 it display the menu for inCollage important links
def test_incollege_important_links_SubMenu(capsys):
 # instance of the class system and call the initmenu
  system = System()
  system.initMenu()
  #simulate the input of the option 6 
  with mock.patch('builtins.input', side_effect=['6', '0', '0', '0']):
    system.important_links()
  # Capture the output
  captured = capsys.readouterr()
  output = captured.out
  print(output)
  # Assert that the expected message is displayed
  expected_message = '''
Welcome to the Important Links Page

[1] Copyright Notice
[2] About
[3] Accessibility
[4] User Agreement
[5] Privacy Policy
[6] Cookie Policy
[7] Brand Policy
[0] Return To Home Page
'''
  assert expected_message in output



# #Task 1:Add a "Copyright Notice" link and have it contain relevant content


def test_copyRightNoticelink(capsys, ):
  system_instance = System()
  # Call the initMenu method to initialize the menu
  system_instance.initMenu()
  # Get the menu items from the mainMenu
  menu_items = system_instance.importantLinks.selections
  # Check if the "InCollege Important Links" option exists in the main manu
  inCollege_links_option = next(
    (item for item in menu_items if item['label'] == 'Copyright Notice'), None)
  # Assert that the option exists
  assert inCollege_links_option is not None


# Select the Copy Rigth Notice Option
def test_select_copyright_notice_content(capsys):
  # Go to the "InCollege Important Links" menu
  system = System()
  system.initMenu()

  # system.importantLinks.addItem('Copyright Notice', lambda:      system.quick_menu(System.content["Copyright Notice"]))

  # # Select the "Copyright Notice" option
  with mock.patch('builtins.input', side_effect=['1', '0', '0', '0']):
    system.important_links()

  # Capture the output
  captured = capsys.readouterr()
  output = captured.out
  print(output)
  # Assert that the expected message is displayed
  expected_message = '''
---------------------------
      COPYRIGHT NOTICE
---------------------------

All content and materials displayed on the InCollege website, including but not limited to text, graphics, logos, images, audio clips, and software, are the property of InCollege and are protected by international copyright laws.

The unauthorized reproduction, distribution, or modification of any content on the InCollege website is strictly prohibited without prior written permission from InCollege.

For any inquiries regarding the use of our copyrighted materials, please contact us at legal@incollege.com.

By accessing and using the InCollege website, you agree to comply with all applicable copyright laws and regulations.

---------------------------
'''
  assert expected_message in output


# #Task 2:Add an "About" link and have it contain a history of the company and why it was created.


def test_aboutLink(capsys):
  system_instance = System()
  # Call the initMenu method to initialize the menu
  system_instance.initMenu()
  # Get the menu items from the mainMenu
  menu_items = system_instance.importantLinks.selections
  # Check if the "InCollege Important Links" option exists in the main manu
  inCollege_links_option = next(
    (item for item in menu_items if item['label'] == 'About'), None)
  # Assert that the option exists
  assert inCollege_links_option is not None


def test_aboutLinkContent(capsys, monkeypatch):
  # Go to the "InCollege Important Links" menu
  system = System()
  system.initMenu()
  # select about option
  with mock.patch('builtins.input', side_effect=['2', '0', '0', '0']):
    system.important_links()

  # Capture the output
  captured = capsys.readouterr()
  output = captured.out
  print(output)
  # Assert that the expected message is displayed
  expected_message = '''
--------------------------------------
               ABOUT US
--------------------------------------

Welcome to InCollege - Where Connections and Opportunities Thrive!

At InCollege, we are dedicated to providing a vibrant online platform for college students to connect with friends, explore exciting career opportunities, and foster meaningful professional relationships. Our mission is to empower students like you to unleash your full potential and shape a successful future.

Through our innovative features and cutting-edge technology, we strive to create a dynamic virtual space that bridges the gap between your academic journey and the professional world. Whether you're searching for internships, part-time jobs, or launching your post-graduation career, InCollege is your trusted companion.

Join our vibrant community today and embark on an exciting journey of personal growth, professional development, and lifelong connections.

--------------------------------------
'''
  assert expected_message in output


#Task 3:Add a "User Agreement" link and have it contain relevant content
def test_userAgreement(capsys):
  system_instance = System()
  # Call the initMenu method to initialize the menu
  system_instance.initMenu()
  # Get the menu items from the mainMenu
  menu_items = system_instance.importantLinks.selections
  # Check if the "InCollege Important Links" option exists in the main manu
  inCollege_links_option = next(
    (item for item in menu_items if item['label'] == 'User Agreement'), None)
  # Assert that the option exists
  assert inCollege_links_option is not None

def test_userAgreementContent(capsys, monkeypatch):
  # Go to the "InCollege Important Links" menu
  system = System()
  system.initMenu()
  # select about option
  with mock.patch('builtins.input', side_effect=['4', '0', '0', '0']):
    system.important_links()

  # Capture the output
  captured = capsys.readouterr()
  output = captured.out
  print(output)
  # Assert that the expected message is displayed
  expected_message = '''
------------------------
    USER AGREEMENT
------------------------

Welcome to InCollege! This User Agreement ("Agreement") governs your use of our text-based app. By accessing or using our app, you agree to be bound by the terms and conditions outlined in this Agreement.

1. Acceptance of Terms:
   By using our app, you acknowledge that you have read, understood, and agreed to be bound by this Agreement. If you do not agree with any part of this Agreement, please refrain from using our app.

3. Privacy:
   We respect your privacy and are committed to protecting your personal information. Our Privacy Policy outlines how we collect, use, and disclose your information. By using our app, you consent to the collection and use of your data as described in our Privacy Policy.

4. Limitation of Liability:
   In no event shall InCollege or its affiliates be liable for any damages arising out of or in connection with the use of our app.

5. Modification of Agreement:
   We reserve the right to modify or update this Agreement at any time. 

6. Termination:
   We reserve the right to terminate your access to our app at any time, without prior notice, if we believe you have violated this Agreement or any applicable laws.

By continuing to use our app, you acknowledge that you have read and agreed to this User Agreement.

------------------------
'''
  assert expected_message in output


#Task 4:Add a "Privacy Policy" link and have it contain relevant content

def test_privacyPolicy(capsys):
  system_instance = System()
  # Call the initMenu method to initialize the menu
  system_instance.initMenu()
  # Get the menu items from the mainMenu
  menu_items = system_instance.importantLinks.selections
  # Check if the "InCollege Important Links" option exists in the main manu
  inCollege_links_option = next(
    (item for item in menu_items if item['label'] == 'Privacy Policy'), None)
  # Assert that the option exists
  assert inCollege_links_option is not None
# this test will test the content  inside the privacy policy 
def test_privacyPolicyContent(capsys, monkeypatch):
  # Go to the "InCollege Important Links" menu
  system = System()
  system.initMenu()
  # select about option
  with mock.patch('builtins.input', side_effect=['5', '0', '0', '0']):
    system.important_links()

  # Capture the output
  captured = capsys.readouterr()
  output = captured.out
  print(output)
  # Assert that the expected message is displayed
  expected_message = '''
------------------------
   PRIVACY POLICY
------------------------

At InCollege, we value your privacy and are committed to protecting your personal information. Here's a summary of our privacy practices:

1. Information Collection:
   We collect limited personal information when you register and interact with our platform.

2. Data Usage:
   We use your information to personalize your experience, deliver relevant content, and improve our services. We employ industry-standard security measures to protect your information from unauthorized access.

3. Cookies and Tracking:
   We may use cookies to enhance your browsing experience.
------------------------
'''
  assert expected_message in output


# #Task5:Add a "Cookie Policy" link and have it contain relevant content

def test_cookiePolicy(capsys):
  system_instance = System()
  # Call the initMenu method to initialize the menu
  system_instance.initMenu()
  # Get the menu items from the mainMenu
  menu_items = system_instance.importantLinks.selections
  # Check if the "InCollege Important Links" option exists in the main manu
  inCollege_links_option = next(
    (item for item in menu_items if item['label'] == 'Cookie Policy'), None)
  # Assert that the option exists
  assert inCollege_links_option is not None

def test_cookiePolicyContent(capsys, monkeypatch):
  # Go to the "InCollege Important Links" menu
  system = System()
  system.initMenu()
  # select about option
  with mock.patch('builtins.input', side_effect=['6', '0', '0', '0']):
    system.important_links()

  # Capture the output
  captured = capsys.readouterr()
  output = captured.out
  print(output)
  # Assert that the expected message is displayed
  expected_message = '''
------------------------
   COOKIE POLICY
------------------------

At InCollege, we use cookies to enhance your browsing experience and improve our services. This Cookie Policy explains how we use cookies on our website.

   We use cookies for the following purposes:

   - Authentication: Cookies help us authenticate and secure your account.
   - Preferences: Cookies remember your settings and preferences.
   - Analytics: Cookies gather information about your usage patterns to improve our website's performance.
   - Advertising: Cookies may be used to display relevant ads based on your interests.
------------------------
'''
  assert expected_message in output

# #Task6: Clicking the Privacy Policy link will provide the user with the option to access Guest Controls, but only when they are logged in
def test_PrivacyPolicyGuestControls(capsys):
  system = System()
  system.initMenu()
  # assert that user is logged in to have language option appear
  system.user.loggedOn = True
  with mock.patch('builtins.input', side_effect=['5', '0', '0', '0']):
    system.important_links()

  captured = capsys.readouterr()
  output = captured.out
  print(output)
  # Assert that the expected message is displayed
  expected_message = '''
[1] Guest Controls
[0] Exit
'''
  assert expected_message in output

# check the guess control link

def test_GuestControlslink(capsys):
  system = System()
  system.initMenu()
  # assert that user is logged in to have language option appear
  system.user.loggedOn = True
  with mock.patch('builtins.input', side_effect=['1', '0', '0', '0']):
    system.guest_controls()

  captured = capsys.readouterr()
  output = captured.out
  print(output)
  # Assert that the expected message is displayed
  expected_message = '''
[1] Email [ON]
[2] SMS [ON]
[3] Targeted Advertising [ON]
[0] Back
'''
  assert expected_message in output

# #Task7:Add a "Brand Policy" link and have it contain relevant content

def test_brandPolicy(capsys):
  system_instance = System()
  # Call the initMenu method to initialize the menu
  system_instance.initMenu()
  # Get the menu items from the mainMenu
  menu_items = system_instance.importantLinks.selections
  # Check if the "InCollege Important Links" option exists in the main manu
  inCollege_links_option = next(
    (item for item in menu_items if item['label'] == 'Brand Policy'), None)
  # Assert that the option exists
  assert inCollege_links_option is not None

# test the content for the brand policy option 

def test_brandPolicyContent(capsys, monkeypatch):
  # Go to the "InCollege Important Links" menu
  system = System()
  system.initMenu()
  # select about option
  with mock.patch('builtins.input', side_effect=['7', '0', '0', '0']):
    system.important_links()

  # Capture the output
  captured = capsys.readouterr()
  output = captured.out
  print(output)
  # Assert that the expected message is displayed
  expected_message = '''
------------------------
     BRAND POLICY
------------------------

InCollege is committed to protecting its brand identity and ensuring consistent and accurate representation across all platforms. This Brand Policy outlines the guidelines for using the InCollege brand assets.

   1. Logo Usage: The InCollege logo should be used in its original form and should not be altered, distorted, or modified in any way.
   2. Colors and Typography: The official InCollege colors and typography should be used consistently to maintain brand consistency.
   3. Prohibited Usage: The InCollege brand assets should not be used in any manner that implies endorsement, affiliation, or partnership without proper authorization.

Any unauthorized usage of the InCollege brand assets is strictly prohibited.

------------------------
'''
  assert expected_message in output
# Accessibility link option 
def test_Accessibility(capsys):
  system_instance = System()
  # Call the initMenu method to initialize the menu
  system_instance.initMenu()
  # Get the menu items from the mainMenu
  menu_items = system_instance.importantLinks.selections
  # Check if the "InCollege Important Links" option exists in the main manu
  inCollege_links_option = next(
    (item for item in menu_items if item['label'] == 'Accessibility'), None)
  # Assert that the option exists
  assert inCollege_links_option is not None
# Accessibility link content test
def test_AccessibilityContent(capsys, monkeypatch):
  # Go to the "InCollege Important Links" menu
  system = System()
  system.initMenu()
  # select about option
  with mock.patch('builtins.input', side_effect=['3', '0', '0', '0']):
    system.important_links()

  # Capture the output
  captured = capsys.readouterr()
  output = captured.out
  print(output)
  # Assert that the expected message is displayed
  expected_message = '''
------------------------
ACCESSIBILITY STATEMENT
------------------------

InCollege is committed to ensuring accessibility and inclusion for all users of our text-based app. We strive to provide a user-friendly experience for individuals with diverse abilities.

Accessibility Features:
- Clear Text Formatting: We use clear and legible text formatting to enhance readability for all users.
- Keyboard Navigation: Our app supports keyboard navigation, allowing users to navigate through the app using keyboard shortcuts.
- Text Resizing: You can easily adjust the text size within the app to suit your preferences.
- Simple and Intuitive Design: Our app features a simple and intuitive design, making it easy to navigate and use.

Feedback and Support:
We value your feedback and are continuously working to improve the accessibility of our app. If you have any suggestions or encounter any barriers while using the app, please let us know. 

------------------------
'''
  assert expected_message in output

# #Task8:Add a "Language" link Note:
def test_languageLink(capsys):
  system_instance = System()  # Create an instance of the System class
  system_instance.initMenu()
  # Get the menu items from the homePage
  menu_items = system_instance.importantLinks.selections
  # Check if the "InCollege Important Links" option exists in the home page manu
  inCollege_links_option = next(
    (item for item in menu_items if item['label'] == 'Languages'), None)
  # Assert that the option exists
  assert inCollege_links_option is not None


# #story: As a signed in user, I want to be able to switch the language

# #Task 1:Add an option to switch to Spanish

def test_languageSpanish(capsys):
  system = System()
  system.initMenu()
  # assert that user is logged in to have language option appear
  system.user.loggedOn = True
  with mock.patch('builtins.input', side_effect=['8', '0', '0', '0']):
    system.important_links()

  # capture output
  captured = capsys.readouterr()

  # check that spanish option is available and turned off by default
  assert "Spanish [ ]" in captured.out


# #Task2: Add an option to switch to English,
def test_slanguageEnglish(capsys):
  system = System()
  system.initMenu()
  # assert that user is logged in to have language option appear
  system.user.loggedOn = True

  with mock.patch('builtins.input', side_effect=['8', '0', '0', '0']):
    system.important_links()

  # capture output
  captured = capsys.readouterr()

  # check that english option is available and turned on by default
  assert "English [X]" in captured.out
# check the option to switch to Spanish 
def test_switchToSpanish(capsys):
  system = System()
  system.initMenu()
  # simulate the option spanish is the user select it 
  with mock.patch('builtins.input', side_effect=['2', '0', '0', '0',]):
    system.language_menu()

   # capture output
  captured = capsys.readouterr()

  # check that spanish option is available and turn on 
  assert "Spanish [X]" in captured.out
# check the option to switch to English
def test_switchToEnglish(capsys):
  system = System()
  system.initMenu()
  with mock.patch('builtins.input', side_effect=['1', '0', '0', '0',]):
    system.language_menu()

   # capture output
  captured = capsys.readouterr()

  # check that English option is available and turned on 
  assert "English [X]" in captured.out
  
def test_menu_navigation_to_useful_links(system_instance,capsys):
    # Create an instance of the System class
    # Mock the user input for menu navigation tests all routes
    with mock.patch('builtins.input', side_effect=['5','1','0','2','0','3','0','4','0','0']):
        # Call the menu navigation function
        system_instance.useful_links()
    # Capture the standard output
    captured = capsys.readouterr()
    # Assert that the captured output contains the expected text
    # This in combination with the patch
    assert 'Useful Links' in captured.out
    assert 'General' in captured.out
    assert 'Browse InCollege' in captured.out
    assert 'Business Solutions' in captured.out
    assert 'Directories' in captured.out
    assert 'Exit' in captured.out
     
def test_user_setting_init(system_instance):
    # Test Initial Settings in Guest User
    assert system_instance.user.sms == True
    assert system_instance.user.email == True
    assert system_instance.user.targetedAds == True
    assert system_instance.user.language == "English"
  
def test_account_settings_table_schema():
    # Connect to the database
    conn = sqlite3.connect("accounts.db")
    cursor = conn.cursor()
    # Get the column information of the jobs table
    cursor.execute("PRAGMA table_info(account_settings)")
    columns = cursor.fetchall()
    # Define the expected field types and primary keys
   #A value of 1 means the column does not allow NULL values, and 0 means NULL values are allowed.
    expected_schema = {
        'username': ('VARCHAR(25)', 0, None, 1),
        'email': ('BOOLEAN', 0, None, 0),
        'sms': ('BOOLEAN', 1, None, 0),
        'targetedAds': ('BOOLEAN', 1, None, 0),
        'language': ('VARCHAR(12)', 1, None, 0)
    }
 # Iterate over the columns and compare with expected schema
    for column in columns:
        column_name = column[1]
        field_type = column[2]
        is_primary_key = column[5]
        # Assert field type
        assert field_type == expected_schema[column_name][0]
        # Assert primary key
        assert is_primary_key == expected_schema[column_name][3]
    # Cleanup: Close the connection
    conn.close()

def test_set_sms(account_settings):
  # Ensure the user's SMS setting is initially True
  assert account_settings.user.sms == True
  # Perform the test by calling the relevant method on account_settings
  assert account_settings.user.loggedOn == True
  account_settings.setUserSMS()
  # Grab the user's SMS setting toconfirm update
  conn = sqlite3.connect("accounts.db")
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM account_settings WHERE username=?", ('username',))
  result = cursor.fetchone()
  conn.close()
  print(result)
  assert result[0] == "username"
  assert result[2] ==  0
  
def test_set_targetedAds(account_settings):
  # Ensure the user's SMS setting is initially True
  assert account_settings.user.targetedAds == True
  assert account_settings.user.loggedOn == True
  # Perform the test by calling the relevant method on account_settings
  account_settings.setUserTargetedAds()
  # Grab the user's SMS setting toconfirm update
  conn = sqlite3.connect("accounts.db")
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM account_settings WHERE username=?", ('username',))
  result = cursor.fetchone()
  conn.close()
  print(result)
  assert result[0] == "username"
  assert result[3] ==  0
  
def test_set_email(account_settings):
  # Ensure the user's SMS setting is initially True
  assert account_settings.user.email == True
  # Perform the test by calling the relevant method on account_settings
  assert account_settings.user.loggedOn == True
  account_settings.setUserEmail()
  # Grab the user's setting to confirm update
  conn = sqlite3.connect("accounts.db")
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM account_settings WHERE username=?", ('username',))
  result = cursor.fetchone()
  conn.close()
  print(result)
  assert result[0] == "username"
  assert result[1] ==  0