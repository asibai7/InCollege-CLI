import pytest
import string
import random
from unittest import mock
from system import System


# creates an instance of the system class to be used for testing
@pytest.fixture
def system_instance():
  return System()

# setup and teardown style method that
# temporarily removes existing accounts and associated records from DB when testing
@pytest.fixture
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

@pytest.fixture #test that user can input first and last name when registering
def name_register(system_instance, temp_remove_accounts, capsys):
  system_instance.initMenu()
  inputs = ['2', 'ahmad', 'ah', 'mad','USF','CS','Asibai1$', 'Asibai1$', 'ahmad', 'Asibai1$', '0', '0']
  with mock.patch('builtins.input', side_effect=inputs):
    system_instance.home_page()
  captured = capsys.readouterr()
  output = captured.out
  expected_message = "Account created successfully"
  assert expected_message in output #22nd line of ouput from the program should be Account created successfully
  yield

# validate password
def test_validate_valid_password(system_instance):
  # Call the validate function with a valid password
  valid_password = "ValidPas123!"
  valid_password_again = "ValidPas123!"
  result = system_instance.validatePassword(valid_password,
                                            valid_password_again)
  # Assert that the result is True
  assert result is True


# test invalid password
def test_validate_invalid_password(system_instance):
  # Call the validate function with an invalid password
  invalid_password = "invalid"
  retry = "invalid1"
  result = system_instance.validatePassword(invalid_password, retry)
  # Assert that the result is False
  assert result is False


@pytest.mark.usefixtures("temp_remove_accounts")
def test_login_successful(system_instance, capsys):
  system_instance.initMenu()

  login_success_msg = "You Have Successfully Logged In!"

  with mock.patch('builtins.input',side_effect=['2', 'Jane35', 'Jane', 'Smith', 'USF','Cs','Testing12*', 'Testing12*',
'Jane35', 'Testing12*', '0', '0', '0']):
    system_instance.home_page()

  captured = capsys.readouterr()

  assert login_success_msg in captured.out


def test_login_account_not_found(system_instance, capsys):
  # initialize menu options
  system_instance.initMenu()

  failed_login_msg = "Account Not Found, Check Username/Password."

  # simulate user logging in with an account that does not exist
  with mock.patch('builtins.input', side_effect=['1', 'User55', 'Testing12*', '0']):
    system_instance.home_page()

  # capture output
  captured = capsys.readouterr()

  # assert expected output
  assert failed_login_msg in captured.out

@pytest.mark.usefixtures("temp_remove_accounts")
def test_invalid_credentials(system_instance, capsys):
  # Set up a test user account
  system_instance.initMenu()

  login_success_msg = "Invalid Username/Password, Try Again!"

  with mock.patch('builtins.input',side_effect=['2', 'Jane35', 'Jane', 'Smith','UF','Art', 'Testing12*', 'Testing12*',
'Jane35', 'Testing', '0', '0', '0']):
    system_instance.home_page()

  captured = capsys.readouterr()

  assert login_success_msg in captured.out
  

def test_menu(system_instance, capsys):
  # create an instance of system
  system_instance.initMenu()
  input = ['0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
  captured = capsys.readouterr()
  output = captured.out.split('\n')
  assert '[1] Login' in output
  assert '[2] Register' in output

# all these functions are under contructions
# search for a job or internship
def test_job_search_under_construction(system_instance, name_register, capsys):
  input = ['1', 'ahmad', 'Asibai1$', '2', '0', '0', '0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
  captured = capsys.readouterr()
  output = captured.out.split('\n')
  assert 'Welcome to the Job Postings Page' in output

#find someone the user knows friend
def test_find_friend_under_construction(system_instance, name_register, capsys):
  input = ['1', 'ahmad', 'Asibai1$', '3', '0', '0', '0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
  captured = capsys.readouterr()
  output = captured.out.split('\n')
  assert '[1] Find A Friend' in output

def test_skill_option(system_instance, name_register, capsys):
  input = ['1', 'ahmad', 'Asibai1$', '0', '0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
  captured = capsys.readouterr()
  output = captured.out.split('\n')
  assert '[4] Learn A Skill' in output


def test_numOfSkills(system_instance, name_register, capsys):
  input = ['1', 'ahmad', 'Asibai1$', '4', '0', '0', '0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
  captured = capsys.readouterr()
  output = captured.out.split('\n')
  assert '[1] Project Management' in output
  assert '[2] Networking' in output
  assert '[3] System Design' in output
  assert '[4] Coding' in output
  assert '[5] Professional Communication' in output

def test_skillA(system_instance, capsys):
  system_instance.skillA()
  captured = capsys.readouterr()
  assert "Under Construction" in captured.out
  assert "Project Management" in captured.out


def test_skillB(system_instance, capsys):
  system_instance.skillB()
  captured = capsys.readouterr()
  assert "Under Construction" in captured.out
  assert "Networking" in captured.out


def test_skillC(system_instance, capsys):
  system_instance.skillC()
  captured = capsys.readouterr()
  assert "Under Construction" in captured.out
  assert "System Design" in captured.out


def test_skillD(system_instance, capsys):
  system_instance.skillD()
  captured = capsys.readouterr()
  assert "Under Construction" in captured.out
  assert "Coding" in captured.out


def test_skillE(system_instance, capsys):
  system_instance.skillE()
  captured = capsys.readouterr()
  assert "Under Construction" in captured.out
  assert "Professional Communication" in captured.out


# generates a random string based on the provided parameters
# @param length - the total number of characters in the string
# @param num_upper - the number of uppercase characters in the string
# @param num_digits - the number of digits in the string
# @param num_special - the number of special characters in the string
def generate_random_string(length, num_upper, num_digits, num_special):
  special = '!@#$%^&*()_+-=[]{}|;:,.<>/?`~\'\"\\'
  selected_chars = []
  # exception sum of number of uppercase, digits, and specials must not exceed string length
  if length < (num_upper + num_digits + num_special):
    raise Exception(
      "Total number of uppercase, digits, and special characters exceeds length."
    )
  # add special characters
  for i in range(num_special):
    selected_chars.append(random.choice(special))
  # add digits
  for i in range(num_digits):
    selected_chars.append(random.choice(string.digits))
  # add uppercase letter
  for i in range(num_upper):
    selected_chars.append(random.choice(string.ascii_uppercase))
  # add remaining lowercase letters
  length = length - num_digits - num_special - num_upper
  for i in range(length):
    selected_chars.append(random.choice(string.ascii_lowercase))
  # shuffle password and return as string
  random.shuffle(selected_chars)
  return ''.join(selected_chars)


# tests that passwords are validated according to the appropriate criteria
def test_validate_password(system_instance, capfd):
  msg_pass_length = "Password Must Be 8-12 Characters In Length"
  msg_pass_upper = "Password Must Contain At Least One Upper Case Letter"
  msg_pass_digit = "Password Must Contain At Least One Number"
  msg_pass_special = "Password Must Contain At Least One Special Character"
  # empty password must fail
  password = generate_random_string(0, 0, 0, 0)
  assert system_instance.validatePassword(password, password) is False
  std = capfd.readouterr()
  assert std.out.strip() == msg_pass_length
  # less than 8 characters must fail
  password = generate_random_string(3, 1, 1, 1)
  assert system_instance.validatePassword(password, password) is False
  std = capfd.readouterr()
  assert std.out.strip() == msg_pass_length
  # more than 12 characters must fail
  password = generate_random_string(13, 1, 1, 1)
  assert system_instance.validatePassword(password, password) is False
  std = capfd.readouterr()
  assert std.out.strip() == msg_pass_length
  # no uppercase letters must fail
  password = generate_random_string(8, 0, 1, 1)
  assert system_instance.validatePassword(password, password) is False
  std = capfd.readouterr()
  assert std.out.strip() == msg_pass_upper
  # no digits must fail
  password = generate_random_string(10, 1, 0, 1)
  assert system_instance.validatePassword(password, password) is False
  std = capfd.readouterr()
  assert std.out.strip() == msg_pass_digit
  # no special characters must fail
  password = generate_random_string(12, 1, 1, 0)
  assert system_instance.validatePassword(password, password) is False
  std = capfd.readouterr()
  assert std.out.strip() == msg_pass_special
  # valid password containing 8-12 chars including
  # at least 1 digit, special, and uppercase char
  for i in range(8, 13):
    password = generate_random_string(i, 1, 1, 1)
    assert system_instance.validatePassword(password, password) is True


# test that usernames are properly validated based on their length
def test_validate_username_length(system_instance, capfd):
  usr_length_msg = "Username Must Be 1-25 Characters in Length"
  min_len, max_len = 1, 25
  # no username / too short
  username = ''
  system_instance.conn.commit()
  result = system_instance.validateUserName(username)
  std = capfd.readouterr()
  assert result is False and std.out.strip() == usr_length_msg
  # username exceeds max length
  length = random.randint(max_len + 1, 100)
  username = generate_random_string(length, 1, 0,
                                    0)  # contains upper character
  result = system_instance.validateUserName(username)
  std = capfd.readouterr()
  assert result is False and std.out.strip() == usr_length_msg
  # username of acceptable length
  while True:  # generate username and ensure uniqueness
    length = random.randint(min_len, max_len)
    username = generate_random_string(length, 0, 1,
                                      0)  # contains digit character
    system_instance.cursor.execute("SELECT * FROM accounts WHERE username = ?",
                                   (username, ))
    account = system_instance.cursor.fetchone()
    if account is None:
      break
  # confirm username is validated successfully
  result = system_instance.validateUserName(username)
  capfd.readouterr()
  assert result is True


# tests that usernames are validated based on uniqueness
def test_validate_username_not_unique(system_instance, capfd):
  # username not unique (already taken)
  usr_taken_msg = "Username Has Been Taken."
  system_instance.cursor.execute('SELECT username FROM accounts LIMIT 1')
  rez = system_instance.cursor.fetchone()
  if rez is not None:
    username = rez[0]
  else:
    username = None
  test_user = True
  system_instance.initMenu()
  if not username:  # no accounts, create a test user
    length = random.randint(5, 25)
    username = generate_random_string(length, 1, 0, 0)
    length = random.randint(8, 12)
    password = generate_random_string(length, 1, 1, 1)
    fName = generate_random_string(8, 1, 0, 0)
    lName = generate_random_string(8, 1, 0, 0)
    university= "USF"
    major ="CS"
    with mock.patch('builtins.input', side_effect=['2', username, fName, lName, university, major, password, password, username, password, '0','0']):
      system_instance.home_page()
  else:
    test_user = False
  # confirm non-unique username is rejected and appropriate message displayed
  result = system_instance.validateUserName(username)
  capfd.readouterr() # discard menu messages
  assert result is False
  if test_user:  # delete test user
    system_instance.cursor.execute('DELETE FROM accounts where username = (?)', (username,))
    system_instance.conn.commit()


# tests that the maximum number of accounts can be registered and stored in the database
# also tests that new account are rejected once the account limit is reached
def test_register_success(system_instance, capfd, temp_remove_accounts):
  system_instance.initMenu()
  account_limit = 10
  msg_max_accounts = "Maximum Number Of Accounts Created!"
  msg_reg_success = "Account created successfully."

  # register max number of accounts
  temp_accounts = []
  for i in range(account_limit):
    length = random.randint(5, 25)
    username = generate_random_string(length, 1, 1, 0)
    length = random.randint(8, 12)
    password = generate_random_string(length, 1, 1, 1)
    fName = generate_random_string(8, 1, 0, 0)
    lName = generate_random_string(8, 1, 0, 0)
    university="US"
    major="CS"
    # simulate 5 users creating an account
    with mock.patch('builtins.input', side_effect=['2', username, fName, lName,university,major,password, password, username, password, '0', '0']):
      system_instance.home_page()
      
    std = capfd.readouterr()
    assert msg_reg_success in std.out.strip()
    password = system_instance.encryption(password)
    temp_accounts.append((username, password))

  # account limit reached, registering next account must fail
  length = random.randint(5, 25)
  username = generate_random_string(length, 1, 1, 0)
  length = random.randint(8, 12)
  password = generate_random_string(length, 1, 1, 1)
  fName = generate_random_string(8, 1, 0, 0)
  lName = generate_random_string(8, 1, 0, 0)
  
  # simulate 6th user creating an account 
  with mock.patch('builtins.input', side_effect=['2', username, fName, lName, password, password, username, password, '0', '0']):
      system_instance.home_page()
    
  std = capfd.readouterr()
  user_query = "SELECT * FROM accounts WHERE (username, password) = (?, ?)"
  system_instance.cursor.execute(
    user_query, (username, system_instance.encryption(password)))
  account = system_instance.cursor.fetchone()
  assert msg_max_accounts in std.out.strip() and account is None

  # use a new connection to ensure registered accounts are committed
  system2 = System()
  users = ', '.join(['(?, ?)'] * len(temp_accounts))
  query = f"SELECT username, password FROM accounts WHERE (username, password) in ({users})"
  tmp_acc_list = [item for acc in temp_accounts for item in acc]
  system2.cursor.execute(query, tmp_acc_list)
  result = system2.cursor.fetchall()
  assert len(result) == len(temp_accounts)
  for acc in result:
    assert acc in temp_accounts


# tests that registration fails when username is invalid
def test_register_fail_username(system_instance, capfd, temp_remove_accounts):
  system_instance.initMenu()
  msg_username_length = "Username Must Be Less Than 25 Characters in Length"
  msg_username_length = "Username Must Be 1-25 Characters in Length"
  msg_usr_not_unique = "Username Has Been Taken."
  user_query = "SELECT * FROM accounts WHERE username = ?"
  # username too short (none)
  username = ''
  length = random.randint(8, 12)
  password = generate_random_string(length, 1, 1, 1)
  fName = generate_random_string(8, 1, 0, 0)
  lName = generate_random_string(8, 1, 0, 0)
  university="USF"
  major="CS"
  
  with mock.patch('builtins.input', side_effect=['2',username, fName, lName,university,major, password, password, username, password, '0', '0']):
      system_instance.home_page()
 
  std = capfd.readouterr()
  system_instance.cursor.execute(user_query, (username, ))
  account = system_instance.cursor.fetchone()
  assert msg_username_length in std.out.strip() and account is None
  # username too long
  length = random.randint(26, 100)
  username = generate_random_string(length, 1, 1, 1)
  length = random.randint(8, 12)
  password = generate_random_string(length, 1, 1, 1)
  fName = generate_random_string(8, 1, 0, 0)
  lName = generate_random_string(8, 1, 0, 0)
  university="USF"
  major="CS"
  with mock.patch('builtins.input', side_effect=['2', username, fName, lName, university,major,password, password, username, password, '0', '0']):
    system_instance.home_page()
    
  std = capfd.readouterr()
  system_instance.cursor.execute(user_query, (username, ))
  account = system_instance.cursor.fetchone()
  assert msg_username_length in std.out.strip() and account is None
  # username not unique
  length = random.randint(1, 25)
  username = generate_random_string(length, 1, 0, 0)
  length = random.randint(8, 12)
  password = generate_random_string(length, 1, 1, 1)
  for i in range(2):  # attempt to double register new user
    fName = generate_random_string(8, 1, 0, 0)
    lName = generate_random_string(8, 1, 0, 0)
    university="USF"
    major="CS"
    with mock.patch('builtins.input', side_effect=['2', username, fName, lName, university,major,password, password, username, password, '0', '0']):
      system_instance.home_page()
    std = capfd.readouterr()
  assert msg_usr_not_unique in std.out.strip()  


# tests that registration fails when password is invalid
def test_register_fail_password(system_instance, capfd, temp_remove_accounts):
  system_instance.initMenu()
  password_warnings = {
    'length': "Password Must Be 8-12 Characters In Length",
    'uppercase': "Password Must Contain At Least One Upper Case Letter",
    'digit': "Password Must Contain At Least One Number",
    'special': "Password Must Contain At Least One Special Character"
  }
  user_query = "SELECT * FROM accounts WHERE (username, password) = (?, ?)"

  # no password
  length = random.randint(5, 25)
  username = generate_random_string(length, 1, 0, 1)
  password = ''
  fName = generate_random_string(8, 1, 0, 0)
  lName = generate_random_string(8, 1, 0, 0)
  university="USF"
  major="Computer Sciences"
  with mock.patch('builtins.input', side_effect=['2', username, fName, lName,university,major, password, password, '0', '0']):
    system_instance.home_page()
  std = capfd.readouterr()
  system_instance.cursor.execute(
    user_query, (username,system_instance.encryption(password)))
  account = system_instance.cursor.fetchone()
  assert password_warnings['length'] in std.out.strip() and account is None
  # password below minimum length
  length = random.randint(5, 25)
  username = generate_random_string(length, 1, 0, 1)
  length = random.randint(3, 7)
  password = generate_random_string(length, 1, 1, 1)
  fName = generate_random_string(8, 1, 0, 0)
  lName = generate_random_string(8, 1, 0, 0)
  university="USF"
  major="Computer Sciences"
  with mock.patch('builtins.input', side_effect=['2', username, fName, lName, university,major,password, password, username, password, '0', '0']):
    system_instance.home_page()
  std = capfd.readouterr()
  system_instance.cursor.execute(
    user_query, (username, system_instance.encryption(password)))
  account = system_instance.cursor.fetchone()
  assert password_warnings['length'] in std.out.strip() and account is None
  # password exceeds maximum length
  length = random.randint(5, 25)
  username = generate_random_string(length, 1, 0, 1)
  length = random.randint(13, 100)
  password = generate_random_string(length, 1, 1, 1)
  fName = generate_random_string(8, 1, 0, 0)
  lName = generate_random_string(8, 1, 0, 0)
  university="USF"
  major="Computer Sciences"
  
  with mock.patch('builtins.input', side_effect=['2', username, fName, lName,university,major, password, password, username, password, '0', '0']):
    system_instance.home_page()
  std = capfd.readouterr()
  system_instance.cursor.execute(
    user_query, (username, system_instance.encryption(password)))
  account = system_instance.cursor.fetchone()
  assert password_warnings['length'] in std.out.strip() and account is None
  # no uppercase letter in password
  length = random.randint(5, 25)
  username = generate_random_string(length, 1, 0, 1)
  length = random.randint(8, 12)
  password = generate_random_string(length, 0, 1, 1)
  fName = generate_random_string(8, 1, 0, 0)
  lName = generate_random_string(8, 1, 0, 0)
  university="USF"
  major="Computer Sciences"
  with mock.patch('builtins.input', side_effect=['2', username, fName, lName,university,major,password, password, username, password, '0', '0']):
    system_instance.home_page()
  std = capfd.readouterr()
  system_instance.cursor.execute(
    user_query, (username, system_instance.encryption(password)))
  account = system_instance.cursor.fetchone()
  assert password_warnings['uppercase'] in std.out.strip() and account is None
  # no digit in password
  length = random.randint(5, 25)
  username = generate_random_string(length, 1, 0, 1)
  length = random.randint(8, 12)
  password = generate_random_string(length, 1, 0, 1)
  fName = generate_random_string(8, 1, 0, 0)
  lName = generate_random_string(8, 1, 0, 0)
  university="USF"
  major="Computer Sciences"
  with mock.patch('builtins.input', side_effect=['2', username, fName, lName,university,major, password, password, username, password, '0', '0']):
    system_instance.home_page()
  std = capfd.readouterr()
  system_instance.cursor.execute(
    user_query, (username, system_instance.encryption(password)))
  account = system_instance.cursor.fetchone()
  assert  password_warnings['digit'] in std.out.strip() and account is None
  # no special character in password
  length = random.randint(5, 25)
  username = generate_random_string(length, 1, 0, 1)
  length = random.randint(8, 12)
  password = generate_random_string(length, 1, 1, 0)
  fName = generate_random_string(8, 1, 0, 0)
  lName = generate_random_string(8, 1, 0, 0)
  university="USF"
  major="Computer Sciences"
  with mock.patch('builtins.input', side_effect=['2', username, fName, lName, university,major,password, password, username, password, '0', '0']):
    system_instance.home_page()
  std = capfd.readouterr()
  system_instance.cursor.execute(
    user_query, (username, system_instance.encryption(password)))
  account = system_instance.cursor.fetchone()
  assert password_warnings['special'] in std.out.strip() and account is None


# tests that the register menu prompts the user for username and password
def test_login_menu_register(system_instance, temp_remove_accounts,capsys):
  # register menu prompts
  prompts = ["Enter Username:", "Enter First Name: ", "Enter Last Name: ","Enter University Name: ","Enter Major:", "Enter Password: ", "Confirm Password:"]
  # simulated inputs for testing register menu
  register = '2'
  length = random.randint(5, 25)
  username = generate_random_string(length, 0, 1, 0)
  fName = generate_random_string(8, 1, 0, 0)
  lName = generate_random_string(8, 1, 0, 0)
  university="USf"
  major="CS"
  length = random.randint(8, 12)
  password = generate_random_string(length, 1, 1, 1)
  pass_check = 'fail'
  exit_app = '0'
  inputs = [register, username, fName, lName,university, major,password, pass_check, exit_app]

  # run the registration menu with the simulated inputs
  with mock.patch('builtins.input', side_effect=inputs):
    system_instance.initMenu()
    system_instance.home_page()

  # clear additional non-input prompts
  captured = capsys.readouterr()

  #  check that all registration prompts were displayed
  for item in prompts:
    assert item in captured.out


# tests the return/exit option in the skills menu
# allowing users to return to the main/top level menu
def test_return_option(system_instance, capfd):
  exit_opt = "[0] Log Out\n"
  main_menu_opts = ['Profile', 'Job/Internship Search', 'Friends', 'Learn A Skill', 'Useful Links', 'InCollege Important Links']
  skills = ['Project Management', 'Networking', 'System Design', 'Coding', 'Professional Communication']
  # construct options for main and skill menus
  skill_choices = [
    f"[{i+1}] {skill}\n" for i, skill in enumerate(skills)
  ]
  main_choices = [f"[{i+1}] {name}\n" for i, name in enumerate(main_menu_opts)]
  main_choices += exit_opt
  skill_choices += "[0] Return To Main Menu"
  # construct full prompts for main and skill menu
  main_prompt = ''.join(main_choices)
  skill_prompt = ''.join(skill_choices)
  
  # simulated inputs: learn a skill, return to main menu, exit app
  inputs = ['4', '0', '0']

  # run the main menu with the simulated inputs
  with mock.patch('builtins.input', side_effect=inputs):
    system_instance.initMenu()
    system_instance.main_menu()

  # confirm output matches with expected
  std = capfd.readouterr()
  assert exit_opt in std.out.strip()
  for item in main_menu_opts:
    assert item in std.out.strip()
  assert main_prompt in std.out.strip()
  assert skill_prompt in std.out.strip()
  assert "Exiting" in std.out.strip()