import pytest
import sqlite3
import inspect
import re
from unittest import mock
from system import System
from user import User, profile, education, experience


# a list of test users with the attributes necessary for registration
TEST_USER = [ 
  ['user1', 'hank', 'hill', 'uni1', 'major1', 'Password1!'],
  ['user2', 'bobby', 'hill', 'uni2', 'major2', 'Password2@'],
  ['user3', 'dale', 'gribble', 'uni3', 'major3', 'Password3#'],
  ['user4', 'john', 'redcorn', 'uni4', 'major4', 'Password4$'],
  ['user5', 'khan', 'souphanousinph', 'uni5', 'major5', 'Password5%'],
]


#============================================== Fixtures ============================================================

@pytest.fixture
def system_instance():
  """Creates and instance of the system performs some menu initialization."""
  s1 = System()
  s1.initMenu()
  return s1


@pytest.fixture
def clear_restore_db(system_instance): 
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
def test_instance_1():
  # Create an instance of the System class or initialize your system
  # delete the value of the table job to do the test 
    conn = sqlite3.connect("accounts.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM accounts")
    conn.commit()
    conn.close()
    system = System()
    system.initMenu()
    # Perform any necessary setup or data insertion for the test
    # For example, insert test data into the database
    conn = sqlite3.connect("accounts.db")
    cursor = conn.cursor() 
    cursor.execute("INSERT INTO accounts (username, password, fName, lName,university,major) VALUES (?, ?, ?, ?,?,?)", ('username', "Password123!", "Patrick","Shugerts","USF","CS"))
    conn.commit()
    cursor.execute("INSERT INTO accounts (username, password, fName, lName,university,major) VALUES (?, ?, ?, ?,?,?)", ('username1', "Password123!", "Test","Test","USF","CS"))
    conn.commit()
    cursor.execute("INSERT INTO accounts (username, password, fName, lName,university,major) VALUES (?, ?, ?, ?,?,?)", ('username2', "Password123!", "Testing","Away","USF","CS"))
    conn.commit()
    conn.close()
  ###### Log In a User #####
    system.user.login("username","Patrick","Shugerts","usf","cs",True,True,True,"English")
    # system.user.logout()
    # Return the system instance for the test
    return system


@pytest.fixture #test that user can input first and last name when registering
def name_register(system_instance, clear_restore_db, capsys):
  inputs = ['2', 'ahmad', 'ah', 'mad', 'usf', 'cs', 'Asibai1$', 'Asibai1$', 'ahmad', 'Asibai1$', '0', '0']
  with mock.patch('builtins.input', side_effect=inputs):
    system_instance.home_page()
  captured = capsys.readouterr()
  output = captured.out
  assert 'Account created successfully.' in output
  yield
  

@pytest.fixture #Creates a second account to test with in the database
def name_register_1(system_instance, clear_restore_db, capsys):
  inputs = ['2', 'makdoodie', 'mahmood', 'sales','usf','cs', 'Test123!', 'Test123!', 'makdoodie', 'Test123!', '0', '0']
  with mock.patch('builtins.input', side_effect=inputs):
    system_instance.home_page()
  captured = capsys.readouterr()
  output = captured.out
  assert  'Account created successfully.' in output
  yield


#============================================== Story 1 Tests ======================================================

def test_accounts_schema(system_instance):
  # retreive experiences table schema from database
  query = 'PRAGMA table_info(accounts)'
  system_instance.cursor.execute(query)
  result = [(row[0], row[1], row[2], row[3], row[5]) for row in system_instance.cursor.fetchall()]
  # columns: col num, name, type, not null, primary key
  # note: the not null column is only 1 for explicit not null constraints
  expected = [(0, 'username', 'varchar2(25)', 0, 1),
              (1, 'password', 'varchar2(12)', 0, 0),
              (2, 'fName', 'varchar2(25)', 0, 0),
              (3, 'lName', 'varchar2(25)', 0, 0),
              (4, 'university', 'TEXT', 0, 0),
              (5, 'major', 'TEXT', 0, 0),
              (6, 'yearsAttended', 'INT', 0, 0),
              (7, 'title', 'varchar2(50)', 0, 0),
              (8, 'infoAbout', 'TEXT', 0, 0),
              (9, 'profile', 'BOOLEAN', 0, 0),
             ]
  # compare against expected schema
  assert result == expected


def test_experiences_schema(system_instance):
  # retreive experiences table schema from database
  query = 'PRAGMA table_info(experiences)'
  system_instance.cursor.execute(query)
  result = [(row[0], row[1], row[2], row[3], row[5]) for row in system_instance.cursor.fetchall()]
  # columns: col num, name, type, not null, primary key
  # note: the not null column is only 1 for explicit not null constraints
  expected = [(0, 'expID', 'INTEGER', 0, 1),
              (1, 'username', 'VARCHAR(25)', 0, 0),
              (2, 'title', 'TEXT', 0, 0),
              (3, 'employer', 'TEXT', 0, 0),
              (4, 'dateStarted', 'TEXT', 0, 0),
              (5, 'dateEnded', 'TEXT', 0, 0),
              (6, 'location', 'TEXT', 0, 0),
              (7, 'description', 'TEXT', 0, 0),
             ]
  # compare against expected schema
  assert result == expected


def test_experiences_FK(system_instance, clear_restore_db):
  # insert 2 test users into accounts table
  validUsers = [('user1',), ('user2',)]
  tables = ['accounts', 'experiences']
  query = f"INSERT INTO {tables[0]} (username) VALUES (?)"
  system_instance.cursor.executemany(query, validUsers)
  system_instance.conn.commit()
  # insert same 2 test users into the experiences table
  query = f"INSERT INTO {tables[1]} (username) VALUES (?)"
  print(query)
  system_instance.cursor.executemany(query, validUsers)
  system_instance.conn.commit()
  # insert invalid test user into experiences table expecting integrity error
  try:
    system_instance.cursor.execute(query, ('userINVALID',))
    system_instance.conn.commit()
    assert False
  except sqlite3.IntegrityError as e:
    assert str(e) == 'FOREIGN KEY constraint failed'
  # delete 1 test user from accounts and check for correct FK cleanup
  query = f"DELETE FROM {tables[0]} WHERE username = ? RETURNING username"
  system_instance.cursor.execute(query, validUsers[0])
  result = system_instance.cursor.fetchone()
  assert result == validUsers[0] # result should match deleted test user
  query = f"SELECT username FROM {tables[1]}"
  system_instance.cursor.execute(query)
  result = system_instance.cursor.fetchall()
  system_instance.conn.commit()
  assert len(result) == 1 and result[0] == validUsers[1] # result should match remaining test user


#============================================== Story 3 Tests =====================================================

def test_profile_class():
  """Confirms that the profile class has the correct attributes."""
  profileObj = profile()
  assert hasattr(profileObj, 'headline')
  assert hasattr(profileObj, 'about')
  assert hasattr(profileObj, 'education')
  assert hasattr(profileObj, 'experiences')


def test_education_class():
  """Confirms that the education class has the correct attributes."""
  eduObj = education('uni', 'major', 'yA')
  assert hasattr(eduObj, 'university')
  assert hasattr(eduObj, 'major')
  assert hasattr(eduObj, 'yearsAttended')


def test_experience_class():
  """Confirms that the experience class has the correct attributes."""
  expObj = experience(1, 'emp', 'title', 'YYYY-MM-DD', 'YYYY-MM-DD', 'loc', 'desc')
  assert hasattr(expObj, 'ID')
  assert hasattr(expObj, 'title')
  assert hasattr(expObj, 'employer')
  assert hasattr(expObj, 'startDate')
  assert hasattr(expObj, 'endDate')
  assert hasattr(expObj, 'location')
  assert hasattr(expObj, 'description')


def test_user_profile_attr():
  """Checks that the user class contains the new profile attribute, 
  and that the constructor includes a profile parameter that defaults to none"""
  # test the constructor signature for the profile parameter
  profile = 'Profile'
  sig = inspect.signature(User.__init__)
  params = sig.parameters
  assert profile in params and params[profile].default is None
  # test a user instance for the profile attribute 
  minimal_user = User('user1', 'firstname', 'lastname')
  assert hasattr(minimal_user, profile)
  assert minimal_user.Profile is None


def test_basic_has_profile():
  """Checks that boolean hasProfile function of the user class 
  returns true for users with a profile and false for users without one."""
  # setup users with and without a profile and test checkprofile function
  minimal_user = User('user1', 'firstname', 'lastname')
  profile_user = User('user2', 'firstname', 'lastname', Profile=profile())
  assert minimal_user.hasProfile() == False
  assert profile_user.hasProfile() == True


def test_integrated_has_profile(system_instance, clear_restore_db):
  """Checks that user's has profile function operates correctly during a simulated user interaction"""
  # register a user in the system
  inputs = TEST_USER[0]
  inputs.append(TEST_USER[0][-1]) # duplicate password  for pass check input
  with mock.patch('builtins.input', side_effect=inputs):
    system_instance.register()
  # login user
  inputs = [TEST_USER[0][0], TEST_USER[0][-1]]
  with mock.patch('builtins.input', side_effect=inputs):
    system_instance.login()
  # check that new test user does not have profile
  assert system_instance.user.hasProfile() == False
  # trigger the user profile menu and select to create profile
  inputs = ['1','0','0']
  with mock.patch('builtins.input', side_effect=inputs):
    system_instance.user_profile_menu()
  # check that the user now has a profile
  system_instance.user.hasProfile() == True
  # ensure the profile is cleaned up on logout
  system_instance.user.logout()
  system_instance.user.hasProfile() == False


def test_display_profile_user(): # previously test_display_profile but renamed to avoid test conflict
  """
  Tests the output of the user's display profile function in both partial and full modes.
  The test user information used in this function was generated with the assistance of ChatGPT.
  """
  # basic user info
  username, fName, lName = 'user1', 'Emily', 'Johnson'
  # profile info
  headline = "Computer Science Student | University of Cambridge | Passionate about Problem-Solving and Innovation"
  about = """I am Emily Johnson, a passionate computer science student at the University of Cambridge. With a strong interest in problem-solving and innovation, I constantly strive to explore the endless possibilities offered by the world of technology. Throughout my three years at university, I have gained a solid foundation in programming languages, algorithms, and software development methodologies. I am always eager to expand my knowledge and keep up with the latest advancements in the field. My goal is to contribute to the development of cutting-edge solutions that positively impact people's lives and revolutionize the way we interact with technology."""
  # education info
  uni, major, years_attended = 'University of Cambridge', 'Computer Science', 3
  edu = education(uni, major, years_attended)
  # experience 1 info
  exp_fields = ['Title', 'Employer', 'Start Date', 'End Date', 'Location', 'Description']
  experiences = []
  exp = {'id': 1,
          'title': 'Software Engineering Intern',
          'emp': 'XYZ Tech Solutions',
          'start': '2022-06-30',
          'end': '2022-09-01',
          'loc': 'London, United Kingdom',
          'desc': """As a software engineering intern at XYZ Tech Solutions, I collaborated with a team of developers to design and implement new features for a web-based application. I participated in agile development processes, conducted code reviews, and contributed to troubleshooting and debugging tasks. Additionally, I gained hands-on experience in utilizing various programming languages and frameworks, enhancing my skills in software development and problem-solving."""
        }
  experiences.append(experience(exp['id'], exp['title'], exp['emp'], exp['start'], exp['end'], exp['loc'], exp['desc']))
  # experience 2 info
  exp = {'id': 2,
          'title': 'Research Assistant',
          'emp': 'University of Cambridge, Department of Computer Science',
          'start': '2022-01-01',
          'end': '2022-06-01',
          'loc': 'Cambridge, United Kingdom',
          'desc': """During my role as a research assistant at the University of Cambridge, Department of Computer Science, I worked closely with a professor on a project focusing on artificial intelligence and machine learning. I conducted extensive literature reviews, gathered and analyzed data, and assisted in developing algorithms and models. I also collaborated with other team members to prepare research papers for publication, gaining valuable insights into the research process and enhancing my analytical and critical thinking skills."""
        }
  experiences.append(experience(exp['id'], exp['title'], exp['emp'], exp['start'], exp['end'], exp['loc'], exp['desc']))
  # experience 3 info
  exp = {'id': 3,
          'title': 'Software Development Intern',
          'emp': 'ABC Software Solutions',
          'start': '2021-06-01',
          'end': '2021-08-31',
          'loc': 'San Francisco, California, United States',
          'desc': """As a software development intern at ABC Software Solutions, I had the opportunity to work on a cross-functional team to develop and test software applications. I assisted in the implementation of new features, performed software testing and debugging, and collaborated with designers and product managers to ensure smooth functionality and user experience. This experience allowed me to deepen my understanding of the software development lifecycle and refine my coding and problem-solving skills."""
        }
  experiences.append(experience(exp['id'], exp['title'], exp['emp'], exp['start'], exp['end'], exp['loc'], exp['desc']))
  # setup the expected output starting with base fields that will be displayed in every user profile
  # note: the user is not required to enter all of these fields so some may be N/A
  expected_base = lambda user: {"Viewing Profile",
                    *({"Education"} if user.Profile and user.Profile.education else set()),
                    f"Name: {fName} {lName}",
                    *({f"Title: {headline if user.Profile.headline else 'N/A'}"} if user.Profile else set()),
                    *({f"About: {about if user.Profile.about else 'N/A'}"} if user.Profile else set()),
                    *({f"University: {uni.title() if user.Profile.education.university else 'N/A'}"} if user.Profile and user.Profile.education else set()),
                    *({f"Degree: {major.title() if user.Profile.education.major else 'N/A'}"} if user.Profile and user.Profile.education else set()),
                    *({f"Years Attended: {years_attended if user.Profile.education.yearsAttended else 'N/A'}"} if user.Profile and user.Profile.education else set())
}
  # setup the expected experiences output for each of the 3 experiences
  expected_exp = [] # list of 3 sets, 1 for each of the experiences above
  for n, exper in enumerate(experiences, start=1):
    expi = set() # holds output for each attribute of the current experience
    # add the expected output for each attribute to the set
    expi.add(f"Experience {n}")
    i = 0
    expi.add(f"{exp_fields[i]}: {exper.title}")
    i = i + 1
    expi.add(f"{exp_fields[i]}: {exper.employer}")
    i = i + 1
    expi.add(f"{exp_fields[i]}: {exper.startDate}")
    i = i + 1
    expi.add(f"{exp_fields[i]}: {exper.endDate}")
    i = i + 1
    expi.add(f"{exp_fields[i]}: {exper.location}")
    i = i + 1
    expi.add(f"{exp_fields[i]}: {exper.description}")
    expected_exp.append(expi) # append the expected output for the current experience to the list

  # List of users with different profile states ranging from no profile to a full profile.
  # Users are packed in tuples with the number of lines expected to be displayed in full mode for said user.
  # This number refers to the number of lines expected to be matched from the expected_base and
  # expected_exp sets, it does not include formatting lines matched by the regex below.
  users = [(User(username, fName, lName), 2),
           (User(username, fName, lName, Profile=profile()), 4),
           (User(username, fName, lName, Profile=profile(headline)), 4),
           (User(username, fName, lName, Profile=profile(about=about)), 4),
           (User(username, fName, lName, Profile=profile(headline, education=edu)), 8),
           (User(username, fName, lName, Profile=profile(about=about, education=edu)), 8),
           (User(username, fName, lName, Profile=profile(headline, about, edu)), 8),
           (User(username, fName, lName, Profile=profile(headline, about, edu, experiences[0:1])), 15),
           (User(username, fName, lName, Profile=profile(headline, about, edu, experiences[0:2])), 22),
           (User(username, fName, lName, Profile=profile(headline, about, edu, experiences)), 29),]

  # test the outputs of the partial and full profile displays for each user in the list
  for user, num_lines in users:
    # partial profile display should only ever include the first and last name
    assert user.displayProfile('part') == f"Name: {fName} {lName}"
    # output of full profile display depends on the contents of the profile
    result = [line.strip() for line in user.displayProfile('full').split('\n')]
    expected = expected_base(user)
    # union the current user's experiences to the set of expected outputs
    if user.Profile and user.Profile.experiences and len(user.Profile.experiences):
      expected = expected | set.union(*expected_exp[0:len(user.Profile.experiences)])
    # create a dictionary from the set of expected output lines,
    # key: line, value: number of lines matched in result (initially 0)
    expected = dict.fromkeys(expected, 0)
    # Each line of the result should match one of the expected outputs or a formatting line matched by the regex.
    # The regex matches lines that exclusively contain 1 of the following options:
    # no characters, only periods, only whitespaces, only hyphens.
    for line in result:
      if line in expected:
        # expected output lines should only be matched once per result
        expected[line] += 1
        assert line in expected and expected[line] == 1
      else:
        assert re.match(r'^[\.]+$|^[\s]*$|^[-]+$|', line)
    # number of matching lines in result should equal the number of matches expected for the user
    assert sum(expected.values()) == num_lines


#=========================================== Story 2 and 5 Tests ==================================================

def test_profile_title_menu(test_instance_1,capsys):  #tests that signing up is not an option from the general option in useful links to logged in users
  input = ['1', '1','0','0','0']
  with mock.patch('builtins.input', side_effect=input):
    test_instance_1.home_page()
  captured = capsys.readouterr()
  output = captured.out
  assert "[1] Profile" in output
  assert "[1] Create Profile" in output
  assert "[1] Edit Profile" in output
  assert "[2] View Profile" in output


def test_profile_title_edit_menu(test_instance_1,capsys):  #tests that signing up is not an option from the general option in useful links to logged in users
  input = ['1', '1', '1', 'This is a Title' ,'0','1','','0','0','0','0']
  with mock.patch('builtins.input', side_effect=input):
    test_instance_1.home_page()
  captured = capsys.readouterr()
  output = captured.out
  assert "Title: This is a Title" in output
  assert "Successfully Added Title to Profile" in output


def test_profile_about_edit_menu(test_instance_1,capsys):  #tests that signing up is not an option from the general option in useful links to logged in users
  input = ['1', '1', '2', 'This is an about section' ,'0','2','','0','0','0','0']
  with mock.patch('builtins.input', side_effect=input):
    test_instance_1.home_page()
  captured = capsys.readouterr()
  output = captured.out
  assert "About: This is an about section" in output
  assert "Successfully Added About to Profile" in output


def test_profile_edu_edit_menu(test_instance_1,capsys):  #tests that signing up is not an option from the general option in useful links to logged in users
  input = ['1', '1', '3','1', 'FSU' ,'0','2','CS','0','3','4','0','0','0','0','0']
  with mock.patch('builtins.input', side_effect=input):
    test_instance_1.home_page()
  captured = capsys.readouterr()
  output = captured.out
  assert "Successfully Added University to Profile" in output
  assert "Successfully Added Degree to Profile" in output
  assert "Successfully Added Years Attended to Profile" in output
  assert "Successfully Added University to Profile" in output 


def test_profile_exp1_edit_menu(test_instance_1,capsys):  #tests that signing up is not an option from the general option in useful links to logged in users
  input = ['1', '1', '4','1', 'My first job' ,'0','2','My first employer','0','3','2021-05-27','0','4','2023-05-27','0','5','Somewhere, Florida','0','6','Flipping Burgers','0','0','0','0','0']
  with mock.patch('builtins.input', side_effect=input):
    test_instance_1.home_page()
  captured = capsys.readouterr()
  output = captured.out
  assert "Successfully Added Title to Profile" in output
  assert "Successfully Added Start Date to Profile" in output
  assert "Successfully Added End Date to Profile" in output
  assert "Successfully Added Location to Profile" in output
  assert "Successfully Added Description to Profile" in output 


def test_profile_exp2_edit_menu(test_instance_1,capsys):  #tests that signing up is not an option from the general option in useful links to logged in users
  input = ['1', '1', '5','1', 'My second job' ,'0','2','My second employer','0','3','2021-05-27','0','4','2023-05-27','0','5','Somewhere Else, Florida','0','6','Flipping Burgers','0','0','0','0','0']
  with mock.patch('builtins.input', side_effect=input):
    test_instance_1.home_page()
  captured = capsys.readouterr()
  output = captured.out
  assert "Successfully Added Title to Profile" in output
  assert "Successfully Added Start Date to Profile" in output
  assert "Successfully Added End Date to Profile" in output
  assert "Successfully Added Location to Profile" in output
  assert "Successfully Added Description to Profile" in output  


def test_profile_exp3_edit_menu(test_instance_1,capsys):  #tests that signing up is not an option from the general option in useful links to logged in users
  input = ['1', '1', '6','1', 'My third job' ,'0','2','My third employer','0','3','2021-05-27','0','4','2023-05-27','0','5','Somewhere Else Not there, Florida','0','6','Flipping Burgers','0','0','0','0','0']
  with mock.patch('builtins.input', side_effect=input):
    test_instance_1.home_page()
  captured = capsys.readouterr()
  output = captured.out
  assert "Successfully Added Title to Profile" in output
  assert "Successfully Added Start Date to Profile" in output
  assert "Successfully Added End Date to Profile" in output
  assert "Successfully Added Location to Profile" in output
  assert "Successfully Added Description to Profile" in output 


def test_profile_friend_name_menu_name_only(test_instance_1,capsys):  
  #tests that signing up is not an option from the general option in useful links to logged in users
  field = "university"
  value = "USF"
  query = f"""
  SELECT username, fName, lName, university, major FROM accounts WHERE {field} LIKE ? COLLATE NOCASE and username != ?"""
  test_instance_1.cursor.execute(query, (f"%{value}%", test_instance_1.user.userName))
  results = [
    User(uname, fname, lname, university=uni, major=maj) for uname, fname, lname, uni, maj in test_instance_1.cursor.fetchall()
  ]
  for friend in results:
    test_instance_1.sendFriendRequest(friend)
  test_instance_1.user.login("username1","Test","Test","usf","cs",True,True,True,"English")
  test_instance_1.loadAllFriends()
  for uname, friend in test_instance_1.user.receivedRequests.items():
     test_instance_1.acceptFriendRequest(friend)
  test_instance_1.loadAllFriends() 
  test_instance_1.user.login("username","Patrick","Shugerts","usf","cs",True,True,True,"English")
  ################################################################################################
  input = ['3','2','1','0','0','0','0']
  with mock.patch('builtins.input', side_effect=input):
    test_instance_1.home_page()
  captured = capsys.readouterr()
  output = captured.out
  assert "Name: Test Test" in output


def test_profile_friend_pending_menu_name_only(test_instance_1,capsys):  
  #tests that signing up is not an option from the general option in useful links to logged in users
  field = "university"
  value = "USF"
  query = f"""
  SELECT username, fName, lName, university, major FROM accounts WHERE {field} LIKE ? COLLATE NOCASE and username != ?"""
  test_instance_1.cursor.execute(query, (f"%{value}%", test_instance_1.user.userName))
  results = [
    User(uname, fname, lname, university=uni, major=maj) for uname, fname, lname, uni, maj in test_instance_1.cursor.fetchall()
  ]
  for friend in results:
    test_instance_1.sendFriendRequest(friend)
  test_instance_1.user.login("username1","Test","Test","usf","cs",True,True,True,"English")
  test_instance_1.loadAllFriends()
  ################################################################################################
  input = ['3','3','1','0','0','0','0','0','0']
  with mock.patch('builtins.input', side_effect=input):
    test_instance_1.home_page()
  captured = capsys.readouterr()
  output = captured.out
  assert "Name: Patrick Shugerts" in output  


def test_view_profile(test_instance_1,capsys):
  test_instance_1.user.login("username","Patrick","Shugerts","usf","cs",True,True,True,"English")
  input = ['1', '1', '1', 'This is a Title' ,'0','1','','0','0','0','0']
  with mock.patch('builtins.input', side_effect=input):
    test_instance_1.home_page()
    test_instance_1.user.login("username","Patrick","Shugerts","usf","cs",True,True,True,"English")
  input = ['1', '1', '2', 'This is an about section' ,'0','2','','0','0','0','0']
  with mock.patch('builtins.input', side_effect=input):
    test_instance_1.home_page()
    test_instance_1.user.login("username","Patrick","Shugerts","usf","cs",True,True,True,"English")
  input = ['1', '1', '3','1', 'FSU' ,'0','2','CS','0','3','4','0','0','0','0','0']
  with mock.patch('builtins.input', side_effect=input):
    test_instance_1.home_page()
  test_instance_1.user.login("username","Patrick","Shugerts","usf","cs",True,True,True,"English")
  input = ['1', '1', '6','1', 'My third job' ,'0','2','My third employer','0','3','2021-05-27','0','4','2023-05-27','0','5','Somewhere Else Not there, Florida','0','6','Flipping Burgers','0','0','0','0','1','2','0','0','0']
  with mock.patch('builtins.input', side_effect=input):
    test_instance_1.home_page()
  captured = capsys.readouterr()
  output = captured.out
  query = """
---------------
Viewing Profile
---------------

Name: Patrick Shugerts
Title: This is a Title
About: This is an about section
"""
  query2 = """
Education
..........

 University: Fsu
 Degree: Cs
 Years Attended: 4
"""
  query3 = """
Experience 1
.............

 Title: My first job
 Employer: My first employer
 Start Date: 2021-05-27
 End Date: 2023-05-27
 Location: Somewhere, Florida
 Description: Flipping Burgers
"""
  query4 = """
Experience 2
.............

 Title: My second job
 Employer: My second employer
 Start Date: 2021-05-27
 End Date: 2023-05-27
 Location: Somewhere Else, Florida
 Description: Flipping Burgers
"""
  query5 = """
Experience 3
.............

 Title: My third job
 Employer: My third employer
 Start Date: 2021-05-27
 End Date: 2023-05-27
 Location: Somewhere Else Not there, Florida
 Description: Flipping Burgers
"""
  assert query in output
  assert query2 in output
  assert query3 in output
  assert query4 in output
  assert query5 in output


def test_view_friend_profile(test_instance_1,capsys):
#tests that signing up is not an option from the general option in useful links to logged in users
  field = "university"
  value = "USF"
  query = f"""
  SELECT username, fName, lName, university, major FROM accounts WHERE {field} LIKE ? COLLATE NOCASE and username != ?"""
  test_instance_1.cursor.execute(query, (f"%{value}%", test_instance_1.user.userName))
  results = [
    User(uname, fname, lname, university=uni, major=maj) for uname, fname, lname, uni, maj in test_instance_1.cursor.fetchall()
  ]
  for friend in results:
    test_instance_1.sendFriendRequest(friend)
  test_instance_1.user.login("username1","Test","Test","usf","cs",True,True,True,"English")
  test_instance_1.loadAllFriends()
  for uname, friend in test_instance_1.user.receivedRequests.items():
     test_instance_1.acceptFriendRequest(friend)
  test_instance_1.loadAllFriends() 
  
  test_instance_1.user.login("username","Patrick","Shugerts","usf","cs",True,True,True,"English")
  input = ['1', '1', '1', 'This is a Title' ,'0','1','','0','0','0','0']
  with mock.patch('builtins.input', side_effect=input):
    test_instance_1.home_page()
    test_instance_1.user.login("username","Patrick","Shugerts","usf","cs",True,True,True,"English")
  input = ['1', '1', '2', 'This is an about section' ,'0','2','','0','0','0','0']
  with mock.patch('builtins.input', side_effect=input):
    test_instance_1.home_page()
    test_instance_1.user.login("username","Patrick","Shugerts","usf","cs",True,True,True,"English")
  input = ['1', '1', '3','1', 'FSU' ,'0','2','CS','0','3','4','0','0','0','0','0']
  with mock.patch('builtins.input', side_effect=input):
    test_instance_1.home_page()
  test_instance_1.user.login("username","Patrick","Shugerts","usf","cs",True,True,True,"English")
  input = ['1', '1', '6','1', 'My third job' ,'0','2','My third employer','0','3','2021-05-27','0','4','2023-05-27','0','5','Somewhere Else Not there, Florida','0','6','Flipping Burgers','0','0','0','0','1','2','0','0','0']
  with mock.patch('builtins.input', side_effect=input):
    test_instance_1.home_page()
    test_instance_1.user.login("username1","Test","Test","usf","cs",True,True,True,"English")
  input = ['3','2','1','1','0','0','0','0','0','0','0']
  with mock.patch('builtins.input', side_effect=input):
    test_instance_1.home_page()
  captured = capsys.readouterr()
  output = captured.out
  query = """
---------------
Viewing Profile
---------------

Name: Patrick Shugerts
Title: This is a Title
About: This is an about section
"""
  query2 = """
Education
..........

 University: Fsu
 Degree: Cs
 Years Attended: 4
"""
  query3 = """
Experience 1
.............

 Title: My first job
 Employer: My first employer
 Start Date: 2021-05-27
 End Date: 2023-05-27
 Location: Somewhere, Florida
 Description: Flipping Burgers
"""
  query4 = """
Experience 2
.............

 Title: My second job
 Employer: My second employer
 Start Date: 2021-05-27
 End Date: 2023-05-27
 Location: Somewhere Else, Florida
 Description: Flipping Burgers
"""
  query5 = """
Experience 3
.............

 Title: My third job
 Employer: My third employer
 Start Date: 2021-05-27
 End Date: 2023-05-27
 Location: Somewhere Else Not there, Florida
 Description: Flipping Burgers
"""
  assert query in output
  assert query2 in output
  assert query3 in output
  assert query4 in output
  assert query5 in output


# ============================================== Story 4 Tests ====================================================

#Epic 5, Story 4: I want to be able to see the profile of any friend I have.

#Subtask 1: In Show my Network, you may click on any connection and have the option to view their profile in addition to the already created disconnect and exit options, this is only an option if the connection has created a profile
def test_friend_profile(system_instance, clear_restore_db, capsys, name_register ,name_register_1):
  #adds a friendship between the users
  system_instance.cursor.execute('INSERT INTO friends (sender, receiver, status) VALUES ("ahmad", "makdoodie", "accepted");')
  #makes sure there's no view profile option
  input = ['1', 'ahmad', 'Asibai1$', '3', '2', '1', '0' '0', '0','0', '0','0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
  captured = capsys.readouterr()
  output = captured.out
  assert '[1] View Profile' not in output
  #logs in and adds things to profile
  input = ['1', 'makdoodie', 'Test123!', '1', '1','1', 'placeholder title', '0', '0', '0','0', '0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
  #now that profile options are added, checks that view profile button is present
  input = ['1', 'ahmad', 'Asibai1$', '3', '2', '1', '0' '0', '0','0', '0', '0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
  captured = capsys.readouterr()
  output = captured.out
  assert '[1] View Profile' in output


#Subtask 2: Clicking on a connection should not display the user’s profile automatically
def test_display_profile(system_instance, clear_restore_db, capsys, name_register ,name_register_1):
  #adds a friendship between the users
  system_instance.cursor.execute('INSERT INTO friends (sender, receiver, status) VALUES ("ahmad", "makdoodie", "accepted");')
  #logs in and adds things to profile
  input = ['1', 'makdoodie', 'Test123!', '1', '1','1', 'placeholder title', '0', '0', '0','0', '0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
    input = ['1', 'ahmad', 'Asibai1$', '3', '2', '1', '0' '0', '0','0', '0', '0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
  captured = capsys.readouterr()
  output = captured.out
  assert 'placeholder title' not in output


#Subtask 3: Once view profile is pressed, that connection’s profile will be displayed and so 0 (an exit) will take you back to the previous menu
def test_view_friend(system_instance, clear_restore_db, capsys, name_register ,name_register_1):
  #adds a friendship between the users
  system_instance.cursor.execute('INSERT INTO friends (sender, receiver, status) VALUES ("ahmad", "makdoodie", "accepted");')
  #adds some sample data to the user's profile
  sql = "UPDATE accounts SET yearsAttended=5, title='Software Engineer Intern', infoAbout='Just a bit about me', profile = True WHERE username='makdoodie';"
  system_instance.cursor.execute(sql)
  input = ['1', 'ahmad', 'Asibai1$', '3', '2', '1', '1', '0', '0' '0', '0','0', '0', '0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
  captured = capsys.readouterr()
  output = captured.out.split("\n")
  with open("out.txt", 'w') as f:
    for line in output:
      f.write(f"{line}\n")
  
  assert output[55] == 'Title: Software Engineer Intern'
  assert output[56] == 'About: Just a bit about me'
  assert output[63] == ' Years Attended: 5'
  #Makes sure exit will take you back to the previous menu
  assert output[77] == 'Exiting'


# ============================================= Story 6 Tests ======================================================
# Epic 5, Story 6: Edit load process after a user log in

#Subtask 1: Load year attended (education: INT), title (varchar 50), info (text)) from the accounts table after a user log in
def test_loads_info(system_instance, name_register, capsys):
  #logs in and adds things to profile
  input = ['1', 'ahmad', 'Asibai1$', '1', '1','1', 'Software Engineer Intern', '0', '2', 'Just a bit about me', '0', '3','3','5','0', '0', '0','0', '0', '0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
  #throwing away output so it doesn't make false positive later
  captured = capsys.readouterr()
  output = captured.out
  #logs in and views profile
  input = ['1', 'ahmad', 'Asibai1$', '1', '2', '0', '0','0', '0', '0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
  #confirms all data in database is shown when user views profile
  captured = capsys.readouterr()
  output = captured.out
  assert 'Years Attended: 5' in output
  assert 'Software Engineer Intern' in output
  assert 'Just a bit about me' in output


#Subtask 2: Load all experiences (title, employer, date started, date ended, location, and then a description of what they did (text)) from the experience table
def test_load_experiences(system_instance, name_register, capsys):
  #Makes it so the user has a profile and adds an experience
  system_instance.cursor.execute("UPDATE accounts SET profile = True WHERE username='ahmad';")
  system_instance.cursor.execute("INSERT INTO experiences (expID, username, title, employer, dateStarted, dateEnded, location, description) VALUES (1, 'ahmad', 'Software Developer', 'ABC Corp', '2020-01-19', '2020-06-21', 'New York, NY', 'Developed and maintained software for a variety of corporate functions.');")
  #logs in and views profile
  input = ['1', 'ahmad', 'Asibai1$', '1', '2', '0', '0','0', '0', '0']
  with mock.patch('builtins.input', side_effect=input):
    system_instance.home_page()
  #confirms all data in database is shown when user views profile
  captured = capsys.readouterr()
  output = captured.out
  assert """Title: Software Developer
 Employer: ABC Corp
 Start Date: 2020-01-19
 End Date: 2020-06-21
 Location: New York, NY
 Description: Developed and maintained software for a variety of corporate functions.""" in output


#Subtask 3: Edit loadacceptedfriends to load all profile information
def test_loadacceptedfriends(system_instance, clear_restore_db, capsys, name_register ,name_register_1):
    #adds a friendship between the users
    system_instance.cursor.execute('INSERT INTO friends (sender, receiver, status) VALUES ("ahmad", "makdoodie", "accepted");')
    #inserts profile information for one user
    username = "makdoodie"
    sql = "UPDATE accounts SET yearsAttended=5, title='Software Engineer Intern', infoAbout='Just a bit about me', profile = True WHERE username=?;"
    system_instance.cursor.execute(sql, (username,))
    with mock.patch('builtins.input', side_effect=['ahmad', 'Asibai1$', '0']):
      system_instance.login()
    system_instance.loadAcceptedFriends()
    assert 'makdoodie' in system_instance.user.acceptedRequests
    makdoodie = system_instance.user.acceptedRequests['makdoodie']
    system_instance.loadFriendProfile(makdoodie)
    assert makdoodie.Profile.headline == "Software Engineer Intern"
    assert makdoodie.Profile.about == "Just a bit about me"
    assert makdoodie.Profile.education.yearsAttended == 5


# ============================================== Story 7 Tests ===================================================

def test_title_case(system_instance, name_register):
  result = system_instance.cursor.execute("SELECT university FROM accounts")
  result = system_instance.cursor.fetchone()
  assert result[0] == 'Usf', "usf does not have a capital U"