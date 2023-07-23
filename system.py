import sqlite3
import datetime
import re
import hashlib
from user import User, education, experience, profile
import os

#list of languages currently supported by InCollege
LANGUAGES = ('English', 'Spanish')
MSG_ERR_RETRY = "Your Request Could Not Be Competed at This Time.\nPlease Try Again Later."


class Jobs:
    def __init__(self, title, employer, location, salary, posterFirstName, posterLastName, description=None):
        self.title = title
        self.description = description
        self.employer = employer
        self.location = location
        self.salary = salary
        self.posterFirstName = posterFirstName
        self.posterLastName = posterLastName
  
class Menu:
  ## Constructor
  ## Hold Menu Items Internally
    def __init__(self):
      self.opening = "" # please update the hasOpening function if this values changes
      self.exitStatement = "Exit"
      self.selections = []  # full list of selections(label, action, visibiliity) for the menu
      self.currSelections = [] # dyanmic list of menu selections that is updated every iteration of the menu
      self.backgroundActions = [] # a list of functions that will be called each iteration before displaying the menu

  
    #destructor
    def __del__(self):
      # print('Menu Deconstructed')
      pass
      
    ##clear console  
    def clear(self):
        if os.name == 'nt':
            _ = os.system('cls')
        else:
            _ = os.system('clear')

  
    ## Set Each Menu Item for the menu
    ## addItem function simply takes in menu option name and then function name
    def addItem(self, item, func, vis = lambda: True):
        self.selections.append({'label': item, 'action': func, 'visible': vis})


    def addBackgroundAction(self,func):
      self.backgroundActions.append(func)

    def hasBackgroundActions(self):
      """Returns a value equal to True if the menu has at least one background action and a value equal to False otherwise."""
      return len(self.backgroundActions)

    def clearBackgroundActions(self):
      self.backgroundActions = []
  
    def setOpening(self,opening):
      self.opening = opening

    def hasOpening(self):
      return self.opening != ""

    def getOpening(self):
      """Returns the menu's opening statement as string."""
      opening = self.opening
      if callable(opening):
        opening = opening()
      return opening

  
    def setExitStatement(self,exit):
      self.exitStatement = exit

    def clearSelections(self):
      """Clears all selections from the menu."""
      self.selections = []
    

    def getValidSelections(self):
      """
      Generates a list of valid selections for the menu based on 
      the current visibility of each selection in the menu's full list of selections
      """
      return [sel for sel in self.selections if sel['visible']()]
  
    ## Displays Each Set Menu Item; System Class performs the action
    ## Display List
    def displaySelections(self):
        print(f"{self.getOpening()}\n")
        for idx, sel in enumerate(self.currSelections, start=1):
          label = sel['label']
          if callable(label):  # allow functions to be used as dynamic labels
            label = label()
          print(f"[{idx}] {label}")
        print(f"[0] {self.exitStatement}")

  
    # Function to take in number as selection
    def selectOption(self):
        while True:
            try:
                choice = int(input("\nEnter the number of your selection: "))
                if choice < 0 or choice > len(self.currSelections):
                    raise ValueError()
                return choice
            except ValueError:
                print("Invalid selection. Please try again.")

  
    def start(self):
    #Main menu loop
      selection = None
      while True:
        # run any tasks that need to be performed before displaying the menu
        for action in self.backgroundActions:
          action()
        self.currSelections = self.getValidSelections()
        if selection is None:  # skip displaying menu & prompting user if previous selection set new selection
          #Displays selections and stores what the user chooses
          self.displaySelections()
          selection = self.selectOption()
        
        if selection == 0:
          print("Exiting")
          self.clear()
          break
        elif callable(selection):  # the previous selection returned another function
          selection = selection()
        else:
          self.clear()
          selection = self.currSelections[selection - 1]
          selection = selection['action']() # current function may return a new selection



class System:
  def __init__(self): #create and connect to db
    self.conn = sqlite3.connect("accounts.db") #establishes connection to SQLite database called accounts
    self.cursor = self.conn.cursor() #creates cursor object which is later used to execute SQL queries
    self.cursor.execute(
      """
      CREATE TABLE IF NOT EXISTS accounts (
        username varchar2(25) PRIMARY KEY, 
        password varchar2(12), 
        fName varchar2(25), 
        lName varchar2(25),
        university TEXT,
        major TEXT,
        yearsAttended INT,
        title varchar2(50),
        infoAbout TEXT,
        profile BOOLEAN
        )
      """
    ) #execute method and cursor object are used to create table if one does not exist
    self.conn.commit() #commit method used to save changes
    # SQL code to create the jobs table if one does not exist
    create_jobs_table = """
    CREATE TABLE IF NOT EXISTS jobs (
      title VARCHAR(128) PRIMARY KEY,
      description TEXT,
      employer VARCHAR(128) NOT NULL,
      location VARCHAR(128) NOT NULL,
      salary INT NOT NULL,
      posterFirstName VARCHAR(128),
      posterLastName VARCHAR(128)
    );
    """
    # Execute the SQL code
    self.cursor.execute(create_jobs_table)
    
    # Commit the transaction
    self.conn.commit()

    #create account settings table
    table_acc_settings = """
    CREATE TABLE IF NOT EXISTS account_settings (
      username VARCHAR(25) PRIMARY KEY, 
      email BOOLEAN,
      sms BOOLEAN,
      targetedAds BOOLEAN,
      language VARCHAR(12),
      FOREIGN KEY(username) REFERENCES accounts(username));
    """
    self.cursor.execute(table_acc_settings)
    self.conn.commit()
      #create trigger add account settings trigger on accounts table
    default_lang = LANGUAGES[0].replace("'", "''")
    default_lang = f"'{default_lang}'"
    trigger_add_settings = f"""
    CREATE TRIGGER IF NOT EXISTS add_acc_settings
    AFTER INSERT ON accounts
    BEGIN
      INSERT INTO account_settings (username, email, sms, targetedAds, language)
      VALUES(NEW.username, True, True, True, {default_lang});
    END;
    """
    self.cursor.execute(trigger_add_settings)
    self.conn.commit()

    #create trigger remove account settings trigger on accounts table
    trigger_add_settings = """
    CREATE TRIGGER IF NOT EXISTS rm_acc_settings
    AFTER DELETE ON accounts
    BEGIN
      DELETE FROM account_settings WHERE username = OLD.username;
    END;
    """
    self.cursor.execute(trigger_add_settings)
    self.conn.commit()

    #create friends table
    table_friends = """
    CREATE TABLE IF NOT EXISTS friends (
      sender VARCHAR(25),
      receiver VARCHAR(25),
      status VARCHAR(12),
      PRIMARY KEY(sender, receiver),
      FOREIGN KEY(sender) REFERENCES accounts(username),
      FOREIGN KEY(receiver) REFERENCES accounts(username));
    """
    self.cursor.execute(table_friends)
    self.conn.commit()

    #create trigger unique friendships trigger on friends table
    #enforces that the sender,receiver combination is a unique relation
    #by preventing permutations so if friendA,friendB is a key then friendB,friendA is invalid
    trigger_unique_friends = """
    CREATE TRIGGER IF NOT EXISTS unique_friend_combinations
    BEFORE INSERT ON friends
    FOR EACH ROW
    BEGIN
      --sender,receiver must not already have a friend relation as receiver,sender - abort if such a relation is found
      SELECT CASE
        WHEN ((SELECT rowid FROM friends WHERE sender = NEW.receiver AND receiver = NEW.sender) IS NOT NULL)
        THEN RAISE(ABORT, 'UNIQUE constraint failed: friends.sender, friends.receiver')
      END;
    END;
    """
    self.cursor.execute(trigger_unique_friends)
    self.conn.commit()

    #create trigger remove friendships trigger on accounts table
    trigger_rm_friends = """
    CREATE TRIGGER IF NOT EXISTS rm_friendships
    AFTER DELETE ON accounts
    FOR EACH ROW
    BEGIN
      DELETE FROM friends WHERE sender = OLD.username OR receiver = OLD.username;
    END;
    """
    self.cursor.execute(trigger_rm_friends)
    self.conn.commit()

    # turn on foreign key constraint enforcement (off by default in SQLite)
    self.cursor.execute("PRAGMA foreign_keys = ON")
    self.conn.commit()
# Create the experience table
    self.cursor.execute("""
    CREATE TABLE IF NOT EXISTS experiences (
        expID INTEGER PRIMARY KEY,
        username VARCHAR(25),
        title TEXT,
        employer TEXT,
        dateStarted TEXT,
        dateEnded TEXT,
        location TEXT,
        description TEXT,
        FOREIGN KEY (username) REFERENCES accounts(username) ON DELETE CASCADE)
""")
# Commit the changes and close the connection for experience table
    self.conn.commit()
       
    ## Instantiate User Class Here
    self.user = User("guest","","",False)
    ## Menus
    self.homePage = Menu()
    self.mainMenu = Menu()
    self.jobsMenu = Menu()
    self.friendMenu = Menu()
    self.videoMenu = Menu()
    self.skillsMenu = Menu()
    self.joinMenu = Menu()
    self.importantLinks = Menu()
    self.usefulLinks = Menu()
    self.privacyMenu = Menu()
    self.guestControls = Menu()
    self.generalMenu = Menu()
    self.quickMenu = Menu() # generic menu used to display content to user with no selections
    self.languageMenu = Menu()
    self.findAFriend = Menu() # allows searching for users by last name, university, or major
    self.receivedFriendsMenu = Menu() # displays the list of user's who have sent friend requests to the current user
    self.userResultsMenu = Menu() # displays the list of users generated by the Find A Friend search
    self.sendFriendRequestMenu = Menu()
    self.receiveFriendReqMenu = Menu()
    self.networkMenu = Menu()
    self.displayFriendInfo = Menu()
    self.viewFriendProfile = Menu()
    self.userProfileMenu = Menu()
    self.editProfileMenu = Menu()
    self.viewUserProfile = Menu()
    self.titleMenu = Menu()
    self.aboutMenu = Menu()
    self.educationMenu = Menu()
    self.uniMenu = Menu()
    self.degreeMenu = Menu()
    self.yearsMenu = Menu()
    self.experience1Menu = Menu()
    self.title1Menu = Menu()
    self.employer1Menu = Menu()
    self.sDate1Menu = Menu()
    self.eDate1Menu = Menu()
    self.location1Menu = Menu()
    self.description1Menu = Menu()
    self.experience2Menu = Menu()
    self.title2Menu = Menu()
    self.employer2Menu = Menu()
    self.sDate2Menu = Menu()
    self.eDate2Menu = Menu()
    self.location2Menu = Menu()
    self.description2Menu = Menu()
    self.experience3Menu = Menu()
    self.title3Menu = Menu()
    self.employer3Menu = Menu()
    self.sDate3Menu = Menu()
    self.eDate3Menu = Menu()
    self.location3Menu = Menu()
    self.description3Menu = Menu()
    
    
    
    
  def __del__(self): #closes connection to db
    self.conn.close()
    
  #System Level Controls for Menus    
  def home_page(self):
   if not(self.user.loggedOn):
     self.homePage.start()
   else:
     self.mainMenu.start()
     self.user.logout()
     
  def join_menu(self, opening = "Would You Like To Join Your Friends On InCollege?", exit = "Return To Home Page"):
    self.joinMenu.setOpening(opening)
    self.joinMenu.setExitStatement(exit)
    if not(self.user.loggedOn):
     self.joinMenu.start()
    else:
     self.mainMenu.start()
     self.user.logout()
     

  def quick_menu(self, opening, exit='Back'):
    """
    Allows the caller to display text to the user in a simple menu with no selections.
    
    Args:
      opening (str): The menu's opening statement.
      exit (str): Optional label for the menu's exit statement/hotkey. The default is 'Back'. 
    """
    
    self.quickMenu.setOpening(opening)
    self.quickMenu.setExitStatement(exit)
    self.quickMenu.start()

  """
  The following functions ending in postfix _menu are essentially menu managers, 
  that may perform setup before calling the associated menu and may cleanup afterwards.
  """
  def main_menu(self):
      self.mainMenu.start()
  def jobs_menu(self):
      self.jobsMenu.start()
  def friend_menu(self):
      self.friendMenu.start()
  def video_menu(self):
      self.videoMenu.start()
  def skills_menu(self):
      self.skillsMenu.start()
  def important_links(self):
      self.importantLinks.start()
  def privacy_menu(self):
      self.privacyMenu.start()
  def guest_controls(self):
      self.guestControls.start()
  def useful_links(self):
      self.usefulLinks.start()
  def general_menu(self):
      self.generalMenu.start()
  def language_menu(self):
      self.languageMenu.start()
  def find_a_friend_menu(self):
      self.findAFriend.start()
  def received_friends_menu(self):
      # set the opening statement
      if not self.receivedFriendsMenu.hasOpening():
        opening = lambda: f"You Have Received Friend Requests From {len(self.user.receivedRequests)} Users."
        self.receivedFriendsMenu.setOpening(opening)
      # add background task to update pending friends
      if not self.receivedFriendsMenu.hasBackgroundActions():
        self.receivedFriendsMenu.addBackgroundAction(self.populateReceivedFriendSelections)
      # start the menu
      self.receivedFriendsMenu.start()  
  def user_results_menu(self):
      self.userResultsMenu.start()
  def send_friend_request_menu(self, friend):
      """Performs setup and cleanup for the send friend request menu."""
      # create the dynamic opening statement
      opening = (
        lambda: f"""{friend.displayProfile("part")}\n
      {"You Have Sent a Friend Request to This User." if friend.userName in self.user.sentRequests 
        else "You Have Received a Friend Request From This User." if friend.userName in self.user.receivedRequests 
        else "You Are Friends With This User." if friend.userName in self.user.acceptedRequests 
        else "You Are Not Friends With This User."}"""
      )
      # initialize the menu components
      self.sendFriendRequestMenu.setOpening(opening)
      self.sendFriendRequestMenu.addBackgroundAction(self.loadAllFriends)
      self.sendFriendRequestMenu.addItem(
        'Send Friend Request',
        lambda: self.sendFriendRequest(friend),
        lambda: True if friend.userName not in self.user.sentRequests 
        and friend.userName not in self.user.receivedRequests
        and friend.userName not in self.user.acceptedRequests 
        else False
      )
      self.sendFriendRequestMenu.start() #start the menu
      # cleanup the menu components
      self.sendFriendRequestMenu.clearBackgroundActions()
      self.sendFriendRequestMenu.clearSelections()


  def receive_friend_req_menu(self, friend):
      """Performs setup and cleanup for the receive friend request menu."""
      # create the dynamic opening statement
      opening = (
        lambda: f"""{friend.displayProfile("part")}\n
      {"You Have Sent a Friend Request to This User." if friend.userName in self.user.sentRequests 
        else "You Have Received a Friend Request From This User." if friend.userName in self.user.receivedRequests 
        else "You Are Friends With This User." if friend.userName in self.user.acceptedRequests 
        else "You Are Not Friends With This User."}"""
      )
      # initialize the menu components
      self.receiveFriendReqMenu.setOpening(opening)
      self.receiveFriendReqMenu.addBackgroundAction(self.loadAllFriends)
      self.receiveFriendReqMenu.addItem(
    		'Accept',
    		lambda: self.acceptFriendRequest(friend),
    		lambda: True if friend.userName in self.user.receivedRequests else False
      )
      self.receiveFriendReqMenu.addItem(
    		'Reject',
    		lambda: self.rejectFriendRequest(friend),
    		lambda: True if friend.userName in self.user.receivedRequests else False
      )
      # start the menu
      self.receiveFriendReqMenu.start()
      # cleanup the menu
      self.receiveFriendReqMenu.clearBackgroundActions()
      self.receiveFriendReqMenu.clearSelections()    
    
  def show_pending_message(self):
    # check receivedRequest dictionary to determine opening statement
    self.loadAllFriends()
    numRequests = len(self.user.receivedRequests)
    if numRequests:
      self.mainMenu.setOpening(f'Welcome User!\n\nYou Have {numRequests} Pending Friend Requests!')
    else:
      self.mainMenu.setOpening('Welcome User!') 

  def network_menu(self):
    self.networkMenu.start()
  def display_friend_info(self):
    self.displayFriendInfo.start()
  

  def view_friend_profile(self, friend):
    self.loadFriendProfile(friend)
    full_profile = friend.displayProfile("full")
    partial_profile = friend.displayProfile("part")
    self.viewFriendProfile.setOpening(lambda: full_profile if friend.hasProfile() and friend.userName in self.user.acceptedRequests else partial_profile)
    self.viewFriendProfile.start()

  def display_network(self, friend):
    # create a dynamic opening
    self.displayFriendInfo.setOpening(lambda: f"""Additional Friend Information: \n\n{friend.displayProfile("part")}\n\n{"You Have Disconnected From This User" if friend.userName not in self.user.acceptedRequests else "You Are Friends With This User"}""")
   
  # view Profile adding into the friends connections if the friend has a profile 

    self.displayFriendInfo.addItem("View Profile", 
                                   lambda: self.view_friend_profile(friend), 
                                   lambda: True if friend.hasProfile() and friend.userName in self.user.acceptedRequests else False )
     # provide an option to disconnect from selected connection
    self.displayFriendInfo.addItem("Disconnect", 
                                   lambda: self.disconnectFriend(friend), 
                                   lambda: True if friend.userName in self.user.acceptedRequests else False)
    
    self.displayFriendInfo.setExitStatement("Exit")
    self.displayFriendInfo.start()
    # clean up menu
    self.displayFriendInfo.clearSelections()

  def show_network(self):
    self.networkMenu.clearSelections()
    self.loadAcceptedFriends()
    connections = self.user.acceptedRequests
    # check if user has connections
    if connections:
      self.networkMenu.setOpening("Your Connections: ")    
      for uname, user in reversed(connections.items()):
        full_name = f'{user.fName.capitalize()} {user.lName.capitalize()}'
        # create an option for each connection and
        # provide additional info when clicked on
        self.networkMenu.addItem(full_name, lambda usr=user: self.display_network(usr))
    else:
      self.networkMenu.setOpening("You Have No Connections.")

  
  def check_user_profile(self):
    query = 'SELECT profile FROM accounts WHERE username = ?'
    self.cursor.execute(query,(self.user.userName,))
    result = self.cursor.fetchone()
    # if true, create a dummy profile for the user
    if result[0]:
      self.user.Profile = profile()

  def view_user_profile(self):
    if not self.viewUserProfile.hasBackgroundActions():
      self.viewUserProfile.addBackgroundAction(self.loadUserProfile)
    self.viewUserProfile.setOpening(lambda: self.user.displayProfile("full"))
    self.viewUserProfile.start()
  
  def user_profile_menu(self):
    if not self.userProfileMenu.hasBackgroundActions():
      self.userProfileMenu.addBackgroundAction(self.check_user_profile)
    if not self.userProfileMenu.hasOpening():
      self.userProfileMenu.setOpening("Welcome to the Profile Menu")
    if len(self.userProfileMenu.selections) == 0:
      # create a dynamic option based on
      # if the user created a profile
      self.userProfileMenu.addItem(lambda: f"""{"Create Profile" if self.user.hasProfile() == False else "Edit Profile"}""", lambda: self.edit_profile_menu)
      self.userProfileMenu.addItem("View Profile", 
                                   lambda: self.view_user_profile, 
                                   lambda: self.user.hasProfile())
      self.userProfileMenu.setExitStatement("Return to Main Menu")
    self.userProfileMenu.start()

  
  def edit_profile_menu(self):
    # also for view menu
    if not self.editProfileMenu.hasBackgroundActions():
      self.editProfileMenu.addBackgroundAction(self.loadUserProfile)
    if not self.editProfileMenu.hasOpening():
      self.editProfileMenu.setOpening("Choose A Section To Edit:")
    if len(self.editProfileMenu.selections) == 0:
      self.editProfileMenu.addItem("Title", 
                                   lambda: self.edit_section("head"), 
                                   lambda: self.user.hasProfile)
      self.editProfileMenu.addItem("About", 
                                   lambda: self.edit_section("about"), 
                                   lambda: self.user.hasProfile)
      self.editProfileMenu.addItem("Education", 
                                   lambda: self.education_menu, 
                                   lambda: self.user.hasProfile)
      self.editProfileMenu.addItem("Experience 1", 
                                   lambda: self.experience1_menu, 
                                   lambda: self.user.hasProfile)
      self.editProfileMenu.addItem("Experience 2", 
                                   lambda: self.experience2_menu, 
                                   lambda: self.user.hasProfile)
      self.editProfileMenu.addItem("Experience 3",
                                   lambda: self.experience3_menu, 
                                   lambda: self.user.hasProfile)
    self.editProfileMenu.start()

  def education_menu(self):
    if not self.educationMenu.hasBackgroundActions():
      self.educationMenu.addBackgroundAction(self.loadUserProfile)
    if not self.educationMenu.hasOpening():
      self.educationMenu.setOpening("Choose A Section To Edit:")
    if len(self.educationMenu.selections) == 0:
      self.educationMenu.addItem("University", 
                                 lambda: self.edit_section("uni"))
      self.educationMenu.addItem("Degree", 
                                 lambda: self.edit_section("deg"))
      self.educationMenu.addItem("Years Attended", 
                                 lambda: self.edit_section("years"))
    self.educationMenu.start()

  def experience1_menu(self):
    if not self.experience1Menu.hasBackgroundActions():
      self.experience1Menu.addBackgroundAction(self.loadUserProfile)
    if not self.experience1Menu.hasOpening():
      self.experience1Menu.setOpening("Share Your Experience: ")
    if len(self.experience1Menu.selections) == 0:
      self.experience1Menu.addItem("Title", 
                                   lambda: self.edit_exp_title("title1"))
      self.experience1Menu.addItem("Employer", 
                                   lambda: self.edit_exp_employer("employer1"))
      self.experience1Menu.addItem("Start Date", 
                                   lambda: self.edit_exp_startDate("start1"))
      self.experience1Menu.addItem("End Date", 
                                   lambda: self.edit_exp_endDate("end1"))
      self.experience1Menu.addItem("Location", 
                                   lambda: self.edit_exp_location("location1"))
      self.experience1Menu.addItem("Description", 
                                   lambda: self.edit_exp_description("description1"))
    self.experience1Menu.start()

  def experience2_menu(self):
    if not self.experience2Menu.hasBackgroundActions():
      self.experience2Menu.addBackgroundAction(self.loadUserProfile)
    if not self.experience2Menu.hasOpening():
      self.experience2Menu.setOpening("Share Your Experience: ")
    if len(self.experience2Menu.selections) == 0:
      self.experience2Menu.addItem("Title", 
                                   lambda: self.edit_exp_title("title2"))
      self.experience2Menu.addItem("Employer", 
                                   lambda: self.edit_exp_employer("employer2"))
      self.experience2Menu.addItem("Start Date", 
                                   lambda: self.edit_exp_startDate("start2"))
      self.experience2Menu.addItem("End Date", 
                                   lambda: self.edit_exp_endDate("end2"))
      self.experience2Menu.addItem("Location", 
                                   lambda: self.edit_exp_location("location2"))
      self.experience2Menu.addItem("Description", 
                                   lambda: self.edit_exp_description("description2"))
    self.experience2Menu.start()

  def experience3_menu(self):
    if not self.experience3Menu.hasBackgroundActions():
      self.experience3Menu.addBackgroundAction(self.loadUserProfile)
    if not self.experience3Menu.hasOpening():
      self.experience3Menu.setOpening("Share Your Experience: ")
    if len(self.experience3Menu.selections) == 0:
      self.experience3Menu.addItem("Title", 
                                   lambda: self.edit_exp_title("title3"))
      self.experience3Menu.addItem("Employer", 
                                   lambda: self.edit_exp_employer("employer3"))
      self.experience3Menu.addItem("Start Date", 
                                   lambda: self.edit_exp_startDate("start3"))
      self.experience3Menu.addItem("End Date", 
                                   lambda: self.edit_exp_endDate("end3"))
      self.experience3Menu.addItem("Location", 
                                   lambda: self.edit_exp_location("location3"))
      self.experience3Menu.addItem("Description", 
                                   lambda: self.edit_exp_description("description3"))
    self.experience3Menu.start()
    

  def edit_section(self, section):
    username = self.user.userName
    # edit profile title and update db
    if section == "head":
      old_headline = self.user.Profile.headline
      print("""--------------\nEditing Title\n--------------\n""")
      if old_headline == None:
        print("Title: N/A\n")
      else:
        print("Title:", old_headline, "\n")
      print("Enter A Title: ", end="")
      headline = input()
      if headline:
        headline_query = 'UPDATE accounts SET title = ?, profile = True WHERE username = ?'
        params = (headline, username)
        self.cursor.execute(headline_query, params)
        self.conn.commit()
        print("\nSuccessfully Added Title to Profile")
      else: 
        print("\nInvalid input. Please try again.")
      self.titleMenu.start()
    elif section == "about":
      old_about = self.user.Profile.about
      print("""--------------\nEditing About\n--------------\n""")
      if old_about == None:
        print("About: N/A\n")
      else:
        print("About:", old_about, "\n")
      print("Introduce Yourself: ", end="")
      about = input()
      if about:
        about_query = 'UPDATE accounts SET infoAbout = ?, profile = True WHERE username = ?'
        params = (about, username)
        self.cursor.execute(about_query, params)
        self.conn.commit()
        print("\nSuccessfully Added About to Profile")
      else:
        print("\nInvalid input. Please try again.")
      self.aboutMenu.start()
    elif section == "uni":
      old_uni = self.user.Profile.education.university.title()
      print("""------------------\nEditing University\n------------------\n""")
      if old_uni == None: 
        print("University: N/A\n")
      else:
        print("University:", old_uni, "\n")
      print("Enter Your University: ", end="")
      uni = input()
      if uni:
        uni_query = 'UPDATE accounts SET university = ?, profile = True WHERE username = ?'
        params = (uni, username)
        self.cursor.execute(uni_query, params)
        self.conn.commit()
        print("\nSuccessfully Added University to Profile")
      else:
        print("\nInvalid input. Please try again.")
      self.uniMenu.start()
    elif section == "deg":
      old_degree = self.user.Profile.education.major.title()
      print("""--------------\nEditing Degree\n--------------\n""")
      if old_degree == None:
        print("Degree: N/A\n")
      else:
        print("Degree:", old_degree, "\n")
      print("Enter Your Degree: ", end="")
      degree = input()
      if degree:
        degree_query = 'UPDATE accounts SET major = ?, profile = True WHERE username = ?'
        params = (degree, username)
        self.cursor.execute(degree_query, params)
        self.conn.commit()
        print("\nSuccessfully Added Degree to Profile")
      else:
        print("\nInvalid input. Please try again.")
      self.degreeMenu.start()
    elif section == "years":
      old_years = self.user.Profile.education.yearsAttended
      print("""--------------\nEditing Years\n--------------\n""")
      if old_years == None:
        print("Years Attended: N/A\n")
      else: 
        print("Years Attended:", old_years, "\n")
      print("Enter Years Attended: ", end="")
      years = input()
      if years.isnumeric():
        years_query = 'UPDATE accounts SET yearsAttended = ?, profile = True WHERE username = ?'
        params = (years, username)
        self.cursor.execute(years_query, params)
        self.conn.commit()
        print("\nSuccessfully Added Years Attended to Profile")
      else: 
        print("\n\nError: Input not a number")
      self.yearsMenu.start()


  def edit_exp_title(self, section):
    username = self.user.userName
    # title queries
    search_title = 'SELECT title, ROWID FROM experiences WHERE username = ?'
    insert_title = 'INSERT INTO experiences (username, title) VALUES (?, ?)'
    update_title = 'UPDATE experiences SET title = ? WHERE username = ? AND ROWID = ?'
    # update profile 
    update_profile = 'UPDATE accounts SET profile = True WHERE username = ?'

    if section == "title1":
      print("""--------------\nEditing Title\n--------------\n""")
      self.cursor.execute(search_title, (username,))
      result = self.cursor.fetchall()
      # check if query isn't None
      if result: 
        # get the rowID of first experience
        rowID = result[0][1]
        old_title = result[0][0]
        if old_title == None:
          print("Title: N/A\n")
        else:
          print("Title:", old_title, "\n")
        # prompt user for input
        print("Enter A Title: ", end="")
        title = input()
        # if valid input then update first exp in db
        if title:
          self.cursor.execute(update_title, (title, username, rowID))
          self.conn.commit()
          # set profile to true in accounts table
          self.cursor.execute(update_profile, (username,))
          self.conn.commit()
          print("\nSuccessfully Added Title to Profile")
        else:
          print("\nInvalid input. Please try again.")
      else:
        print("Title: N/A\n")
        print("Enter A Title: ", end="")
        title = input()
        if title:
          self.cursor.execute(insert_title, (username, title))
          self.conn.commit()
          self.cursor.execute(update_profile, (username,))
          self.conn.commit()
          print("\nSuccessfully Added Title to Profile")
        else:
          print("\nInvalid input. Please try again.")
      self.title1Menu.start()
    elif section == "title2":
      print("""--------------\nEditing Title\n--------------\n""")
      self.cursor.execute(search_title, (username,))
      result = self.cursor.fetchall()
      # check if query isn't None
      if len(result) > 1: 
        # get the rowID of second experience
        rowID = result[1][1]
        # get title of second experience
        old_title = result[1][0]
        if old_title == None:
          print("Title: N/A\n")
        else:
          print("Title:", old_title, "\n")
        # prompt user for input
        print("Enter A Title: ", end="")
        title = input()
        # if valid input then update second exp in db
        if title:
          self.cursor.execute(update_title, (title, username, rowID))
          self.conn.commit()
          # set profile to true in accounts table
          self.cursor.execute(update_profile, (username,))
          self.conn.commit()
          print("\nSuccessfully Added Title to Profile")
        else:
          print("\nInvalid input. Please try again.")
      else:
        print("Title: N/A\n")
        print("Enter A Title: ", end="")
        title = input()
        if title:
          self.cursor.execute(insert_title, (username, title))
          self.conn.commit()
          self.cursor.execute(update_profile, (username,))
          self.conn.commit()
          print("\nSuccessfully Added Title to Profile")
        else:
          print("\nInvalid input. Please try again.")
      self.title2Menu.start()
    elif section == "title3":
      print("""--------------\nEditing Title\n--------------\n""")
      self.cursor.execute(search_title, (username,))
      result = self.cursor.fetchall()
      # check if query isn't None
      if len(result) > 2: 
        # get the rowID of third experience
        rowID = result[2][1]
        old_title = result[2][0]
        if old_title == None:
          print("Title: N/A\n")
        else:
          print("Title:", old_title, "\n")
        # prompt user for input
        print("Enter A Title: ", end="")
        title = input()
        # if valid input then update third exp in db
        if title:
          self.cursor.execute(update_title, (title, username, rowID))
          self.conn.commit()
          # set profile to true in accounts table
          self.cursor.execute(update_profile, (username,))
          self.conn.commit()
          print("\nSuccessfully Added Title to Profile")
        else:
          print("\nInvalid input. Please try again.")
      else:
        print("Title: N/A\n")
        print("Enter A Title: ", end="")
        title = input()
        if title:
          self.cursor.execute(insert_title, (username, title))
          self.conn.commit()
          self.cursor.execute(update_profile, (username,))
          self.conn.commit()
          print("\nSuccessfully Added Title to Profile")
        else:
          print("\nInvalid input. Please try again.")
      self.title3Menu.start()
      

  def edit_exp_employer(self, section):
    username = self.user.userName
    # employer queries
    search_employer = 'SELECT employer, ROWID FROM experiences WHERE username = ?'
    insert_employer = 'INSERT INTO experiences (username, employer) VALUES (?, ?)'
    update_employer = 'UPDATE experiences SET employer = ? WHERE username = ? AND ROWID = ?'
   # update profile 
    update_profile = 'UPDATE accounts SET profile = True WHERE username = ?'

    if section == "employer1":
      print("""----------------\nEditing Employer\n----------------\n""")
      self.cursor.execute(search_employer, (username,))
      result = self.cursor.fetchall()
      # check if query isn't None
      if result: 
        rowID = result[0][1]
        old_employer = result[0][0]
        if old_employer == None:
          print("Employer: N/A\n")
        else:
          print("Employer:", old_employer, "\n")
        print("Enter Employer: ", end="")
        employer = input()
        if employer:
          self.cursor.execute(update_employer, (employer, username, rowID))
          self.conn.commit()
          self.cursor.execute(update_profile, (username,))
          self.conn.commit()
          print("\nSuccessfully Added Employer to Profile")
        else:
          print("\nInvalid input. Please try again.")
      else:
        print("Employer: N/A\n")
        print("Enter Employer: ", end="")
        employer = input()
        if employer:
          self.cursor.execute(insert_employer, (username, employer))
          self.conn.commit()
          self.cursor.execute(update_profile, (username,))
          self.conn.commit()
          print("\nSuccessfully Added Employer to Profile")
        else: 
          print("\nInvalid input. Please try again.")
      self.employer1Menu.start()
    elif section == "employer2":
      print("""----------------\nEditing Employer\n----------------\n""")
      self.cursor.execute(search_employer, (username,))
      result = self.cursor.fetchall()
      # check if query isn't None
      if len(result) > 1: 
        rowID = result[1][1]
        old_employer = result[1][0]
        if old_employer == None:
          print("Employer: N/A\n")
        else:
          print("Employer:", old_employer, "\n")
        print("Enter Employer: ", end="")
        employer = input()
        if employer:
          self.cursor.execute(update_employer, (employer, username, rowID))
          self.conn.commit()
          self.cursor.execute(update_profile, (username,))
          self.conn.commit()
          print("\nSuccessfully Added Employer to Profile")
        else:
          print("\nInvalid input. Please try again.")
      else:
        print("Employer: N/A\n")
        print("Enter Employer: ", end="")
        employer = input()
        if employer:
          self.cursor.execute(insert_employer, (username, employer))
          self.conn.commit()
          self.cursor.execute(update_profile, (username,))
          self.conn.commit()
          print("\nSuccessfully Added Employer to Profile")
        else: 
          print("\nInvalid input. Please try again.")
      self.employer2Menu.start()
    elif section == "employer3":
      print("""----------------\nEditing Employer\n----------------\n""")
      self.cursor.execute(search_employer, (username,))
      result = self.cursor.fetchall()
      # check if query isn't None
      if len(result) > 2: 
        rowID = result[2][1]
        old_employer = result[2][0]
        if old_employer == None:
          print("Employer: N/A\n")
        else:
          print("Employer:", old_employer, "\n")
        print("Enter Employer: ", end="")
        employer = input()
        if employer:
          self.cursor.execute(update_employer, (employer, username, rowID))
          self.conn.commit()
          self.cursor.execute(update_profile, (username,))
          self.conn.commit()
          print("\nSuccessfully Added Employer to Profile")
        else:
          print("\nInvalid input. Please try again.")
      else:
        print("Employer: N/A\n")
        print("Enter Employer: ", end="")
        employer = input()
        if employer:
          self.cursor.execute(insert_employer, (username, employer))
          self.conn.commit()
          self.cursor.execute(update_profile, (username,))
          self.conn.commit()
          print("\nSuccessfully Added Employer to Profile")
        else: 
          print("\nInvalid input. Please try again.")
      self.employer3Menu.start()


  def edit_exp_startDate(self, section):
    username = self.user.userName
    # start date queries
    search_startDate = 'SELECT dateStarted, ROWID FROM experiences WHERE username = ?'
    insert_startDate = 'INSERT INTO experiences (username, dateStarted) VALUES (?, ?)'
    update_startDate = 'UPDATE experiences SET dateStarted = ? WHERE username = ? AND ROWID = ?'
    # update profile 
    update_profile = 'UPDATE accounts SET profile = True WHERE username = ?'
    # format for date
    date_format = '%Y-%m-%d'

    if section == "start1":
      print("""------------------\nEditing Start Date\n------------------\n""")
      self.cursor.execute(search_startDate, (username,))
      result = self.cursor.fetchall()
      # check if query isn't None
      if result: 
        rowID = result[0][1]
        old_startDate = result[0][0]
        if old_startDate == None:
          print("Start Date: N/A\n")
        else:
          print("Start Date:", old_startDate, "\n")
        print("Enter Start Date (YYYY-MM-DD): ", end="")
        startDate = input()
        # validate string format
        if startDate:
          try:
            dateObject = datetime.datetime.strptime(startDate, date_format)
            if dateObject:
              self.cursor.execute(update_startDate, (startDate, username, rowID))
              self.conn.commit()
              self.cursor.execute(update_profile, (username,))
              self.conn.commit()
              print("\nSuccessfully Added Start Date to Profile")
          except ValueError:
            print("\nIncorrect format. Please try again.")
        else: 
          print("\nIncorrect format. Please try again.")
      else:
        print("Start Date: N/A\n")
        print("Enter Start Date (YYYY-MM-DD): ", end="")
        startDate = input()
        # validate string format
        if startDate:
          try:
            dateObject = datetime.datetime.strptime(startDate, date_format)
            if dateObject:
              self.cursor.execute(insert_startDate, (username, startDate))
              self.conn.commit()
              self.cursor.execute(update_profile, (username,))
              self.conn.commit()
              print("\nSuccessfully Added Start Date to Profile")
          except ValueError:
            print("\nIncorrect format. Please try again.")
        else:
          print("\nIncorrect format. Please try again.")
      self.sDate1Menu.start()
    elif section == "start2":
      print("""------------------\nEditing Start Date\n------------------\n""")
      self.cursor.execute(search_startDate, (username,))
      result = self.cursor.fetchall()
      # check if query isn't None
      if len(result) > 1: 
        rowID = result[1][1]
        old_startDate = result[1][0]
        if old_startDate == None:
          print("Start Date: N/A\n")
        else:
          print("Start Date:", old_startDate, "\n")
        print("Enter Start Date (YYYY-MM-DD): ", end="")
        startDate = input()
        if startDate:
          try:
            dateObject = datetime.datetime.strptime(startDate, date_format)
            if dateObject:
              self.cursor.execute(update_startDate, (startDate, username, rowID))
              self.conn.commit()
              self.cursor.execute(update_profile, (username,))
              self.conn.commit()
              print("\nSuccessfully Added Start Date to Profile")
          except ValueError:
            print("\nIncorrect format. Please try again.")
        else: 
          print("\nIncorrect format. Please try again.")
      else:
        print("Start Date: N/A\n")
        print("Enter Start Date (YYYY-MM-DD): ", end="")
        startDate = input()
        # validate string format
        if startDate:
          try:
            dateObject = datetime.datetime.strptime(startDate, date_format)
            if dateObject:
              self.cursor.execute(insert_startDate, (username, startDate))
              self.conn.commit()
              self.cursor.execute(update_profile, (username,))
              self.conn.commit()
              print("\nSuccessfully Added Start Date to Profile")
          except ValueError:
            print("\nIncorrect format. Please try again.")
        else:
          print("\nIncorrect format. Please try again.")
      self.sDate2Menu.start()
    elif section == "start3":
      print("""------------------\nEditing Start Date\n------------------\n""")
      self.cursor.execute(search_startDate, (username,))
      result = self.cursor.fetchall()
      # check if query isn't None
      if len(result) > 2: 
        rowID = result[2][1]
        old_startDate = result[2][0]
        if old_startDate == None:
          print("Start Date: N/A\n")
        else:
          print("Start Date:", old_startDate, "\n")
        print("Enter Start Date (YYYY-MM-DD): ", end="")
        startDate = input()
        if startDate:
          try:
            dateObject = datetime.datetime.strptime(startDate, date_format)
            if dateObject:
              self.cursor.execute(update_startDate, (startDate, username, rowID))
              self.conn.commit()
              self.cursor.execute(update_profile, (username,))
              self.conn.commit()
              print("\nSuccessfully Added Start Date to Profile")
          except ValueError:
            print("\nIncorrect format. Please try again.")
        else: 
          print("\nIncorrect format. Please try again.")
      else:
        print("Start Date: N/A\n")
        print("Enter Start Date (YYYY-MM-DD): ", end="")
        startDate = input()
        # validate string format
        if startDate:
          try:
            dateObject = datetime.datetime.strptime(startDate, date_format)
            if dateObject:
              self.cursor.execute(insert_startDate, (username, startDate))
              self.conn.commit()
              self.cursor.execute(update_profile, (username,))
              self.conn.commit()
              print("\nSuccessfully Added Start Date to Profile")
          except ValueError:
            print("\nIncorrect format. Please try again.")
        else:
          print("\nIncorrect format. Please try again.")
      self.sDate3Menu.start()

  def edit_exp_endDate(self, section):
    username = self.user.userName
    # end date queries
    search_endDate = 'SELECT dateEnded, ROWID FROM experiences WHERE username = ?'
    insert_endDate = 'INSERT INTO experiences (username, dateEnded) VALUES (?, ?)'
    update_endDate = 'UPDATE experiences SET dateEnded = ? WHERE username = ? AND ROWID = ?'
    # update profile 
    update_profile = 'UPDATE accounts SET profile = True WHERE username = ?'
    # format for date
    date_format = '%Y-%m-%d'

    if section == "end1":
      print("""-----------------\nEditing End Date\n-----------------\n""")
      self.cursor.execute(search_endDate, (username,))
      result = self.cursor.fetchall()
      # check if query isn't None
      if result: 
        rowID = result[0][1]
        old_endDate = result[0][0]
        if old_endDate == None:
          print("End Date: N/A\n")
        else:
          print("End Date:", old_endDate, "\n")
        print("Enter End Date (YYYY-MM-DD): ", end="")
        endDate = input()
        # validate string format
        if endDate:
          try:
            dateObject = datetime.datetime.strptime(endDate, date_format)
            if dateObject:
              self.cursor.execute(update_endDate, (endDate, username, rowID))
              self.conn.commit()
              self.cursor.execute(update_profile, (username,))
              self.conn.commit()
              print("\nSuccessfully Added End Date to Profile")
          except ValueError:
            print("\nIncorrect format. Please try again.")
        else: 
          print("\nIncorrect format. Please try again.")
      else:
        print("End Date: N/A\n")
        print("Enter End Date (YYYY-MM-DD): ", end="")
        endDate = input()
        # validate string format
        if endDate:
          try:
            dateObject = datetime.datetime.strptime(endDate, date_format)
            if dateObject:
              self.cursor.execute(insert_endDate, (username, endDate))
              self.conn.commit()
              self.cursor.execute(update_profile, (username,))
              self.conn.commit()
              print("\nSuccessfully Added End Date to Profile")
          except ValueError:
            print("\nIncorrect format. Please try again.")
        else:
          print("\nIncorrect format. Please try again.")
      self.eDate1Menu.start()
    elif section == "end2":
      print("""-----------------\nEditing End Date\n-----------------\n""")
      self.cursor.execute(search_endDate, (username,))
      result = self.cursor.fetchall()
      # check if query isn't None
      if len(result) > 1: 
        rowID = result[1][1]
        old_endDate = result[1][0]
        if old_endDate == None:
          print("End Date: N/A\n")
        else:
          print("End Date:", old_endDate, "\n")
        print("Enter End Date (YYYY-MM-DD): ", end="")
        endDate = input()
        if endDate:
          try:
            dateObject = datetime.datetime.strptime(endDate, date_format)
            if dateObject:
              self.cursor.execute(update_endDate, (endDate, username, rowID))
              self.conn.commit()
              self.cursor.execute(update_profile, (username,))
              self.conn.commit()
              print("\nSuccessfully Added End Date to Profile")
          except ValueError:
            print("\nIncorrect format. Please try again.")
        else: 
          print("\nIncorrect format. Please try again.")
      else:
        print("End Date: N/A\n")
        print("Enter End Date (YYYY-MM-DD): ", end="")
        endDate = input()
        # validate string format
        if endDate:
          try:
            dateObject = datetime.datetime.strptime(endDate, date_format)
            if dateObject:
              self.cursor.execute(insert_endDate, (username, endDate))
              self.conn.commit()
              self.cursor.execute(update_profile, (username,))
              self.conn.commit()
              print("\nSuccessfully Added End Date to Profile")
          except ValueError:
            print("\nIncorrect format. Please try again.")
        else:
            print("\nIncorrect format. Please try again.")
      self.eDate2Menu.start()
    elif section == "end3":
      print("""-----------------\nEditing End Date\n-----------------\n""")
      self.cursor.execute(search_endDate, (username,))
      result = self.cursor.fetchall()
      # check if query isn't None
      if len(result) > 2: 
        rowID = result[2][1]
        old_endDate = result[2][0]
        if old_endDate == None:
          print("End Date: N/A\n")
        else:
          print("End Date:", old_endDate, "\n")
        print("Enter End Date (YYYY-MM-DD): ", end="")
        endDate = input()
        if endDate:
          try:
            dateObject = datetime.datetime.strptime(endDate, date_format)
            if dateObject:
              self.cursor.execute(update_endDate, (endDate, username, rowID))
              self.conn.commit()
              self.cursor.execute(update_profile, (username,))
              self.conn.commit()
              print("\nSuccessfully Added End Date to Profile")
          except ValueError:
            print("\nIncorrect format. Please try again.")
        else: 
          print("\nIncorrect format. Please try again.")
      else:
        print("End Date: N/A\n")
        print("Enter End Date (YYYY-MM-DD): ", end="")
        endDate = input()
        # validate string format
        if endDate:
          try:
            dateObject = datetime.datetime.strptime(endDate, date_format)
            if dateObject:
              self.cursor.execute(insert_endDate, (username, endDate))
              self.conn.commit()
              self.cursor.execute(update_profile, (username,))
              self.conn.commit()
              print("\nSuccessfully Added End Date to Profile")
          except ValueError:
            print("\nIncorrect format. Please try again.")
        else:
          print("\nIncorrect format. Please try again.")
      self.eDate3Menu.start()


  def edit_exp_location(self, section):
    username = self.user.userName
    # location queries
    search_location = 'SELECT location, ROWID FROM experiences WHERE username = ?'
    insert_location = 'INSERT INTO experiences (username, location) VALUES (?, ?)'
    update_location = 'UPDATE experiences SET location = ? WHERE username = ? AND ROWID = ?'
    # update profile 
    update_profile = 'UPDATE accounts SET profile = True WHERE username = ?'

    if section == "location1":
      print("""----------------\nEditing Location\n----------------\n""")
      self.cursor.execute(search_location, (username,))
      result = self.cursor.fetchall()
      # check if query isn't None
      if result: 
        # get the rowID of first experience
        rowID = result[0][1]
        old_location = result[0][0]
        if old_location == None:
          print("Location: N/A\n")
        else:
          print("Location:", old_location, "\n")
        # prompt user for input
        print("Enter A Location: ", end="")
        location = input()
        # if valid input then update first exp in db
        if location:
          self.cursor.execute(update_location, (location, username, rowID))
          self.conn.commit()
          # set profile to true in accounts table
          self.cursor.execute(update_profile, (username,))
          self.conn.commit()
          print("\nSuccessfully Added Location to Profile")
        else:
          print("\nInvalid input. Please try again.")
      else:
        print("Location: N/A\n")
        print("Enter A Location: ", end="")
        location = input()
        if location:
          self.cursor.execute(insert_location, (username, location))
          self.conn.commit()
          self.cursor.execute(update_profile, (username,))
          self.conn.commit()
          print("\nSuccessfully Added Location to Profile")
        else:
          print("\nInvalid input. Please try again.")
      self.location1Menu.start()
    elif section == "location2":
      print("""----------------\nEditing Location\n----------------\n""")
      self.cursor.execute(search_location, (username,))
      result = self.cursor.fetchall()
      # check if query isn't None
      if len(result) > 1: 
        # get the rowID of second experience
        rowID = result[1][1]
        old_location = result[1][0]
        if old_location == None:
          print("Location: N/A\n")
        else:
          print("Location:", old_location, "\n")
        # prompt user for input
        print("Enter A Location: ", end="")
        location = input()
        # if valid input then update second exp in db
        if location:
          self.cursor.execute(update_location, (location, username, rowID))
          self.conn.commit()
          # set profile to true in accounts table
          self.cursor.execute(update_profile, (username,))
          self.conn.commit()
          print("\nSuccessfully Added Location to Profile")
        else:
          print("\nInvalid input. Please try again.")
      else:
        print("Location: N/A\n")
        print("Enter A Location: ", end="")
        location = input()
        if location:
          self.cursor.execute(insert_location, (username, location))
          self.conn.commit()
          self.cursor.execute(update_profile, (username,))
          self.conn.commit()
          print("\nSuccessfully Added Location to Profile")
        else:
          print("\nInvalid input. Please try again.")
      self.location2Menu.start()
    elif section == "location3":
      print("""----------------\nEditing Location\n----------------\n""")
      self.cursor.execute(search_location, (username,))
      result = self.cursor.fetchall()
      # check if query isn't None
      if len(result) > 2: 
        # get the rowID of third experience
        rowID = result[2][1]
        old_location = result[2][0]
        if old_location == None:
          print("Location: N/A\n")
        else:
          print("Location:", old_location, "\n")
        # prompt user for input
        print("Enter A Location: ", end="")
        location = input()
        # if valid input then update third exp in db
        if location:
          self.cursor.execute(update_location, (location, username, rowID))
          self.conn.commit()
          # set profile to true in accounts table
          self.cursor.execute(update_profile, (username,))
          self.conn.commit()
          print("\nSuccessfully Added Location to Profile")
        else:
          print("\nInvalid input. Please try again.")
      else:
        print("Location: N/A\n")
        print("Enter A Location: ", end="")
        location = input()
        if location:
          self.cursor.execute(insert_location, (username, location))
          self.conn.commit()
          self.cursor.execute(update_profile, (username,))
          self.conn.commit()
          print("\nSuccessfully Added Location to Profile")
        else:
          print("\nInvalid input. Please try again.")
      self.location3Menu.start()


  def edit_exp_description(self, section):
    username = self.user.userName
    # description queries
    search_description = 'SELECT description, ROWID FROM experiences WHERE username = ?'
    insert_description = 'INSERT INTO experiences (username, description) VALUES (?, ?)'
    update_description = 'UPDATE experiences SET description = ? WHERE username = ? AND ROWID = ?'
    # update profile 
    update_profile = 'UPDATE accounts SET profile = True WHERE username = ?'

    if section == "description1":
      print("""-------------------\nEditing Description\n-------------------\n""")
      self.cursor.execute(search_description, (username,))
      result = self.cursor.fetchall()
      # check if query isn't None
      if result: 
        # get the rowID of first experience
        rowID = result[0][1]
        old_description = result[0][0]
        if old_description == None:
          print("Description: N/A\n")
        else:
          print("Description:", old_description, "\n")
        # prompt user for input
        print("Enter A Description: ", end="")
        description = input()
        # if valid input then update first exp in db
        if description:
          self.cursor.execute(update_description, (description, username, rowID))
          self.conn.commit()
          # set profile to true in accounts table
          self.cursor.execute(update_profile, (username,))
          self.conn.commit()
          print("\nSuccessfully Added Description to Profile")
        else:
          print("\nInvalid input. Please try again.")
      else:
        print("Description: N/A\n")
        print("Enter A Description: ", end="")
        description = input()
        if description:
          self.cursor.execute(insert_description, (username, description))
          self.conn.commit()
          self.cursor.execute(update_profile, (username,))
          self.conn.commit()
          print("\nSuccessfully Added Description to Profile")
        else:
          print("\nInvalid input. Please try again.")
      self.description1Menu.start()
    elif section == "description2":
      print("""------------------\nEditing Description\n-------------------\n""")
      self.cursor.execute(search_description, (username,))
      result = self.cursor.fetchall()
      # check if query isn't None
      if len(result) > 1: 
        # get the rowID of second experience
        rowID = result[1][1]
        old_description = result[1][0]
        if old_description == None:
          print("Description: N/A\n")
        else:
          print("Description:", old_description, "\n")
        # prompt user for input
        print("Enter A Description: ", end="")
        description = input()
        # if valid input then update second exp in db
        if description:
          self.cursor.execute(update_description, (description, username, rowID))
          self.conn.commit()
          # set profile to true in accounts table
          self.cursor.execute(update_profile, (username,))
          self.conn.commit()
          print("\nSuccessfully Added Description to Profile")
        else:
          print("\nInvalid input. Please try again.")
      else:
        print("Description: N/A\n")
        print("Enter A Desciption: ", end="")
        description = input()
        if description:
          self.cursor.execute(insert_description, (username, description))
          self.conn.commit()
          self.cursor.execute(update_profile, (username,))
          self.conn.commit()
          print("\nSuccessfully Added Description to Profile")
        else:
          print("\nInvalid input. Please try again.")
      self.description2Menu.start()
    elif section == "description3":
      print("""-------------------\nEditing Desciption\n-------------------\n""")
      self.cursor.execute(search_description, (username,))
      result = self.cursor.fetchall()
      # check if query isn't None
      if len(result) > 2: 
        # get the rowID of third experience
        rowID = result[2][1]
        old_description = result[2][0]
        if old_description == None:
          print("Description: N/A\n")
        else:
          print("Description:", old_description, "\n")
        # prompt user for input
        print("Enter A Description: ", end="")
        description = input()
        # if valid input then update third exp in db
        if description:
          self.cursor.execute(update_description, (description, username, rowID))
          self.conn.commit()
          # set profile to true in accounts table
          self.cursor.execute(update_profile, (username,))
          self.conn.commit()
          print("\nSuccessfully Added Description to Profile")
        else:
          print("\nInvalid input. Please try again.")
      else:
        print("Description: N/A\n")
        print("Enter A Description: ", end="")
        description = input()
        if description:
          self.cursor.execute(insert_description, (username, description))
          self.conn.commit()
          self.cursor.execute(update_profile, (username,))
          self.conn.commit()
          print("\nSuccessfully Added Description to Profile")
        else:
          print("\nInvalid input. Please try again.")
      self.description3Menu.start()

  
  def encryption(self, password):
    sha256 = hashlib.sha256()
    sha256.update(password.encode('utf-8'))
    hashed_pass = sha256.hexdigest()
    return hashed_pass

  def deleteTable(self):
    print("Are You Sure You Want To Delete The Current Accounts In The Database? This Operation Cannot Be Undone.(Y/N): ")
    confirm = input()
    if confirm.upper() == "Y":
      self.cursor.execute("DROP TABLE IF EXISTS accounts")
      self.conn.commit()
      print("Table Deleted Successfully.")
    else:
      print("Deletion Operation Canceled.")
  
  def printTable(self):
    self.cursor.execute("SELECT * FROM accounts")
    rows = self.cursor.fetchall()
    if rows:
      print("Username\tPassword")
      for row in rows:
        print(f"{row[0]}\t\t{row[1]}")
    else:
        print("No Records Found In The Table.")

  def countRows(self,tableName):
    ##Current Number of Accounts
    query = "SELECT COUNT(*) FROM {}".format(tableName)
    self.cursor.execute(query)
    count = self.cursor.fetchone()[0]
    return count
    
  def validName(self,fName,lName):
    if len(fName) < 1 or len(fName) > 23:
      print("First Name Must Be 1-23 Characters In Length")
      return False
    if len(lName) < 1 or len(lName) > 23:
      print("Last Name Must Be 1-23 Characters In Length")
      return False
    return True
    
  def validPosNum(self,name,num):
    if num.isdigit():
      if int(num) < 0:
        print(name + " Must Be Greater Than Or Equal to Zero.")
        return False
    else:
      print(name + " Must Be A Number Value")
      return False
    return True
        
  def validString(self,name,string):
    if len(string) > 128:
      print(name + " Must Be 1-128 Characters")
      return False
    return True

  def validatePassword(self, password,password_check): #validate password
    ## Confirm
    if(password != password_check):
      print("Passwords Must Match")
      return False
    ## Password Limits using Regex  
    if len(password) < 8 or len(password) > 12:
      print("Password Must Be 8-12 Characters In Length")
      return False
    if not re.search("[A-Z]", password):
      print("Password Must Contain At Least One Upper Case Letter")
      return False
    if not re.search("[0-9]", password):
      print("Password Must Contain At Least One Number")
      return False 
    if not re.search(r'[\!@#\$%\^&\*\(\)_\+\-\=\[\]\{\}\|\;\:\,\.\<\>\/\?\`\~\'\"\\]', password):
      print("Password Must Contain At Least One Special Character")
      return False
    return True
    
  def validateUserName(self, userName): # validate Username
      self.cursor.execute("SELECT * FROM accounts WHERE username=?", (userName,))
      exists_user = self.cursor.fetchone()
      if exists_user:
        print("Username Has Been Taken.")
        return False
       #arbitrary limit 
      if len(userName) < 1 or len(userName) > 25:
        print("Username Must Be 1-25 Characters in Length")
        return False
      return True

  def login(self): #login check
      print("Log In:\n")
      print("Enter Username: ", end="")
      userName = input()
      print("Enter Password: ", end="")
      password = input()
      ##Validate User Name and Password then Search
      acc_fields = 'username, password, fName, lName, university, major, email, sms, targetedAds, language'
      select_account = f"""
        SELECT {acc_fields} FROM accounts NATURAL JOIN account_settings WHERE username = (?)
      """
      self.cursor.execute(select_account, (userName,)) 
      #? is placeholder for username
      account = self.cursor.fetchone() #fetches first row which query returns
      if account: #if the username exists, then we check that the password in the database matches the password the user inputted
        hashed_inputpass = self.encryption(password)
        if hashed_inputpass == account[1]:
          print("You Have Successfully Logged In!")
          self.user.login(userName,
                          fName=account[2],
                          lName=account[3], 
                          university=account[4],
                          major=account[5],
                          email=account[6], 
                          sms=account[7], 
                          targetedAds=account[8], 
                          language=account[9])          
          return self.home_page
        else:
          print("Invalid Username/Password, Try Again!")
      else:
        print("Account Not Found, Check Username/Password.")

  def register(self):
    ## Set Account Limit (now 10)
    if self.countRows("accounts") >= 10:
      print("Maximum Number Of Accounts Created!")
      return
    print("Enter Username: ", end="")
    username = input()
    print("Enter First Name: ", end="")
    fName = input()
    print("Enter Last Name: ", end="")
    lName = input()
    print("Enter University Name: ", end="")
    university = input().title()
    print("Enter Major: ", end="")
    major = input().title() 
    print("Enter Password: ", end="")
    password = input()
    print("Confirm Password: ", end="")
    passwordCheck = input()
    ## Validate Inputs
    if self.validatePassword(password,passwordCheck) and self.validateUserName(username) and self.validName(fName,lName):
      encrypted_pass = self.encryption(password)
      self.cursor.execute("INSERT INTO accounts (username, password,fName,lName,university,major,profile) VALUES (?, ?, ?, ?, ?, ?, ?)", (username, encrypted_pass,fName,lName,university,major,False))
      self.conn.commit() #saving new account to database
      print("Account created successfully.")
      return self.login
    else:
      print("Account Creation Failed.")
    return

  def postJob(self):
    ## Set Account Limit
    if self.countRows("jobs") >= 5:
      print("Maximum Number Of Jobs Posts Created!")
      return
    print("Enter Title: ")
    title = input()
    print("Enter Description: ")
    description = input()
    print("Enter Employer: ")
    employer = input()
    print("Enter Location: ")
    location = input()
    print("Enter Salary: ")
    salary = input()
    ## Validate Inputs
    if self.validString("Title",title) and self.validString("Description",description) and self.validString("Employer",employer)and self.validString("Location",location) and self.validPosNum("Salary",salary):
      self.cursor.execute("INSERT INTO jobs (title, description,employer,location,salary,posterFirstName,posterLastName) VALUES (?, ?, ?, ?, ?, ?, ?)", (title, description,employer,location,salary,self.user.fName,self.user.lName))
      self.conn.commit() #saving new account to database
      print("Job Posted Successfully.")
      return 
    else:
      print("Job Posting Creation Failed.")
    return

  #This is the function to find someone they know in the system
  def findUser(self):
    #Prompts for searching by first name and last name
    print("Enter First Name: ")
    fName = input()
    print("Enter Last Name: ")
    lName = input()
    # Validate
    if(self.validName(fName,lName)):
        # Search for the user in the database
        self.cursor.execute("SELECT * FROM accounts WHERE UPPER(fName) = UPPER(?) AND UPPER(lName) = UPPER(?)", (fName, lName))
        result = self.cursor.fetchall()
        ## If the user is found, print 
        if len(result) > 0:
            print("They Are Part Of The InCollege System.")
            return self.join_menu
        else:
            print("They Are Not Yet A Part Of The InCollege System.")
        
    else:
      print("Invalid Name Given. Please Try Again.")

  def setUserEmail(self):
    """
    Toggles the user's email setting between True (ON) and False (OFF). 
    If an exception occurs when updating the DB then no change is made, 
    and a message is displayed informing the user to try again later.
    """
    username = self.user.userName
    newEmail = not self.user.email
    update = 'UPDATE account_settings SET email = ? WHERE username = ?'
    try:
      self.cursor.execute(update, (newEmail, username))
      self.conn.commit()
      self.user.email = newEmail
    except Exception:
      print(MSG_ERR_RETRY)

  def setUserSMS(self):
    """
    Toggles the user's sms setting between True (ON) and False (OFF). 
    If an exception occurs when updating the DB then no change is made, 
    and a message is displayed informing the user to try again later.
    """
    username = self.user.userName
    newSMS = not self.user.sms
    update = 'UPDATE account_settings SET sms = ? WHERE username = ?'
    try:
      self.cursor.execute(update, (newSMS, username))
      self.conn.commit()
      self.user.sms = newSMS
    except Exception:
      print(MSG_ERR_RETRY)

  def setUserTargetedAds(self):
    """
    Toggles the user's targeted advertising setting between True (ON) and False (OFF). 
    If an exception occurs when updating the DB then no change is made, 
    and a message is displayed informing the user to try again later.
    """
    username = self.user.userName
    newtargetedAds = not self.user.targetedAds
    update = 'UPDATE account_settings SET targetedAds = ? WHERE username = ?'
    try:
      self.cursor.execute(update, (newtargetedAds, username))
      self.conn.commit()
      self.user.targetedAds = newtargetedAds
    except Exception:
      print(MSG_ERR_RETRY)

  def setUserLanguage(self, language):
    """
    Sets the user's language setting to the specified language. 
    If an exception occurs when updating the DB then no change is made, 
    and a message is displayed informing the user to try again later.
    
    Args:
      language (str): A language from the system's LANGUAGES list.
    """
    uName = self.user.userName
    update = 'UPDATE account_settings SET language = ? WHERE username = ?' 
    try:
        self.cursor.execute(update, (language, uName))
        self.conn.commit()
        self.user.language = language
    except Exception:
        print(MSG_ERR_RETRY)

  def loadSentFriends(self):
    """
    Loads the current user's dictionary of friends that they have sent a pending friend request to.
    """
    query = """
    SELECT username, fName, lName FROM accounts 
    WHERE username IN (SELECT receiver FROM friends WHERE sender = ? AND status = ?)
    """
    params = (self.user.userName, 'pending')
    self.cursor.execute(query, params)
    result = self.cursor.fetchall()
    # iterate over the results and create a dictionary mapping each username to an initialized user object
    self.user.sentRequests = {
      uName: User(uName, fName, lName) for uName, fName, lName in result
    }

  def loadReceivedFriends(self):
    """
    Loads the current user's dictionary of friends that they have received a pending friend request from.
    """
    query = """
    SELECT username, fName, lName FROM accounts 
    WHERE username IN (SELECT sender FROM friends WHERE receiver = ? AND status = ?)
    """
    params = (self.user.userName, 'pending')
    self.cursor.execute(query, params)
    result = self.cursor.fetchall()
    # iterate over the results and create a dictionary mapping each username to an initialized user object
    self.user.receivedRequests = {
      uName: User(uName, fName, lName) for uName, fName, lName in result
    }
    # return length of dictionary to determine if
    # pending request message and number is displayed
    return self.user.receivedRequests

  def loadAcceptedFriends(self):
    """
    Loads the current user's dictionary of friends that have the accepted status.
    """
    query = """
    SELECT username, fName, lName, profile FROM accounts WHERE username IN (
      SELECT CASE WHEN sender = ? THEN receiver ELSE sender END AS friend 
      FROM friends WHERE ? in (sender, receiver) AND status = ?
      GROUP BY friend
    )
    """
    username = self.user.userName
    params = (username, username, 'accepted')
    self.cursor.execute(query, params)
    result = self.cursor.fetchall()
    # iterate over the results and create a dictionary mapping each username to an initialized user object
    self.user.acceptedRequests = {}
    for uName, fName, lName, bprofile in result:
      if bprofile:
        self.user.acceptedRequests[uName] = User(uName, fName, lName, Profile=profile())
      else:
        self.user.acceptedRequests[uName] = User(uName, fName, lName) 

  def loadAllFriends(self):
    """
    Loads all 3 of the current user's friend dictionaries: sent, received, accepted.
    """
    self.loadSentFriends()
    self.loadReceivedFriends()
    self.loadAcceptedFriends()

  def searchUserByField(self, field):
    """Allows the user to perform a search based on the specified criteria, 
    and populates the user results menu with the search results."""
    # prompt the user for search value
    field_title = {'lName': 'Last Name', 'university': 'University', 'major': 'Major'}
    print(f"Please Enter A {field_title[field]}: ", end="")
    value = input()
    # query the database for users based on the search criteria (exclude current user)
    query = f"""
    SELECT username, fName, lName, university, major FROM accounts WHERE {field} LIKE ? COLLATE NOCASE and username != ?"""
    self.cursor.execute(query, (f"%{value}%", self.user.userName))
    results = [
      User(uname, fname, lname, university=uni, major=maj) for uname, fname, lname, uni, maj in self.cursor.fetchall()
    ]
    # generate the selections of the results menu from the user results
    self.userResultsMenu.clearSelections()
    for user in results:
      self.userResultsMenu.addItem(f"{user.fName} {user.lName}", lambda usr=user: self.send_friend_request_menu(usr))

    # set opening for user results menu
    self.userResultsMenu.setOpening(
      f"Search Results: {len(results)} Users Were Found With {field_title[field]} Matching '{value}'"
    )
    return self.user_results_menu

  def sendFriendRequest(self, friend):
    """
    Inserts a pending relation into the friends table between the user and the friend.

    Args:
      friend (User): The user that will be the receiver of the friend request.
    """
    query = "INSERT INTO friends (sender, receiver, status) VALUES (?,?,?)"
    values = (self.user.userName, friend.userName, 'pending')
    try:
      self.cursor.execute(query, values)
      self.conn.commit()
    except sqlite3.IntegrityError as e:
      e = str(e)
      #one or both users don't exist (maybe accounts deleted)
      if e == "FOREIGN KEY constraint failed":
        print("Error: User not found. Please retry the search later.\n")
      # user already received a request from the friend
      elif e == "UNIQUE constraint failed: friends.sender, friends.receiver":  
        print("Error: Pre-Existing Friend Record Found. Please See Updated Relation Status Below.\n")
      # catch all (can't connect to database?)
      else:
        print(e)
      self.conn.rollback() # need to rollback the failed transaction or database will remain locked


  def acceptFriendRequest(self, friend):
    """
	  Updates the relation in the friends table between the user and the friend to accepted.
	
	  Args:
	    friend (User): The user that is the sender of the friend request.
    """
    query = "UPDATE friends SET status = ? WHERE sender = ? AND receiver = ? RETURNING rowid"
    values = ('accepted', friend.userName, self.user.userName)
    self.cursor.execute(query, values)
    result = self.cursor.fetchone()
    self.conn.commit()
    if result is None:
      print("Error: Friend Request Not Found. Please See Updated Relation Status Below.\n")

  def rejectFriendRequest(self, friend):
    """
	  Removes the pending relation in the friends table between the user and the friend.
	
	  Args:
	    friend (User): The user that is the sender of the friend request.
    """
    query = "DELETE FROM friends WHERE sender = ? AND receiver = ? AND status = ? RETURNING rowid"
    values = (friend.userName, self.user.userName, 'pending')
    self.cursor.execute(query, values)
    result = self.cursor.fetchone()
    self.conn.commit()
    if result is None:
      print("Error: Friend Request Not Found. Please See Updated Relation Status Below.\n")

  def populateReceivedFriendSelections(self):
    """
    Refreshes the users list of received friend requests 
    and populates the received friend requests menu with selections corresponding to those users.
    """
    self.receivedFriendsMenu.clearSelections()
    self.loadReceivedFriends()
    for uname, friend in self.user.receivedRequests.items():
      self.receivedFriendsMenu.addItem(
        f"{friend.fName} {friend.lName}", 
        lambda usr=friend: self.receive_friend_req_menu(usr)
      )

  
  def disconnectFriend(self, friend):
    # delete relationship from table
    query = """
    DELETE FROM friends
    WHERE ? IN (sender, receiver) AND ? IN (sender, receiver) AND status = 'accepted' 
    """
    params = (friend.userName, self.user.userName)
    self.cursor.execute(query, params)
    self.conn.commit()


  def loadUserProfile(self):
    userName = self.user.userName
    fields = """
      university, major, yearsAttended, accounts.title AS headline, infoAbout, profile, expID, experiences.title AS title, employer, dateStarted, dateEnded, location, description
      """
    query = f"""
      SELECT {fields} FROM accounts LEFT JOIN experiences ON accounts.username = experiences.username WHERE accounts.username = ?
      """
    self.cursor.execute(query, (userName,))
    userProfile = self.cursor.fetchall()    
    if len(userProfile):
      if userProfile[0][5] == False:
        update_query = 'UPDATE accounts SET profile = True WHERE username = ?'
        self.cursor.execute(update_query, (userName,))
        self.conn.commit()
      userEducation = education(university=userProfile[0][0],
                                major=userProfile[0][1],
                                yearsAttended=userProfile[0][2])
      # list comprehension to create exp as a list
      experiences = [row[6:] for row in userProfile]
      userExperiences = []
      if not(len(experiences) == 1 and experiences[0][0] is None):
        for exp in experiences:
          userExperiences.append(experience(ID=exp[0],
                                 title=exp[1],
                                 employer=exp[2],
                                 startDate=exp[3],
                                 endDate=exp[4],
                                 location=exp[5],
                                 description=exp[6]))
      self.user.Profile = profile(headline=userProfile[0][3],
                                  about=userProfile[0][4],
                                  education=userEducation,
                                  experiences=userExperiences)
    else:
      print("Error: User not found.")
      self.user.Profile = None


  def loadFriendProfile(self, friend):
    userName = friend.userName
    query = "SELECT rowid FROM friends WHERE ? IN (sender, receiver) AND ? IN (sender, receiver) AND status = 'accepted'"
    self.cursor.execute(query, (self.user.userName, friend.userName))
    result = self.cursor.fetchone()
    if result == None:
      self.user.acceptedRequests.pop(userName, None)
      print("Error: Not friends with this user")
      return
    
    fields = """
      university, major, yearsAttended, accounts.title AS headline, infoAbout, profile, expID, experiences.title AS title, employer, dateStarted, dateEnded, location, description
      """
    query = f"""
      SELECT {fields} FROM accounts LEFT JOIN experiences ON accounts.username = experiences.username WHERE accounts.username = ?
      """
    self.cursor.execute(query, (userName,))
    userProfile = self.cursor.fetchall()    
    if len(userProfile):
      if userProfile[0][5] == True:
        userEducation = education(university=userProfile[0][0],
                                  major=userProfile[0][1],
                                  yearsAttended=userProfile[0][2])
        # list comprehension to create exp as a list
        experiences = [row[6:] for row in userProfile]
        userExperiences = []
        if not(len(experiences) == 1 and experiences[0][0] is None):
          for exp in experiences:
            userExperiences.append(experience(ID=exp[0],
                                   title=exp[1],
                                   employer=exp[2],
                                   startDate=exp[3],
                                   endDate=exp[4],
                                   location=exp[5],
                                   description=exp[6]))
        friend.Profile = profile(headline=userProfile[0][3],
                                about=userProfile[0][4],
                                education=userEducation,
                                experiences=userExperiences)
      else:
        friend.Profile = None
    else:
      print("Error: User not found.")
      friend.Profile = None
  
  
    
    
     
  ## Function for the important links to print
  content = {
'Copyright Notice': '''
---------------------------
      COPYRIGHT NOTICE
---------------------------

All content and materials displayed on the InCollege website, including but not limited to text, graphics, logos, images, audio clips, and software, are the property of InCollege and are protected by international copyright laws.

The unauthorized reproduction, distribution, or modification of any content on the InCollege website is strictly prohibited without prior written permission from InCollege.

For any inquiries regarding the use of our copyrighted materials, please contact us at legal@incollege.com.

By accessing and using the InCollege website, you agree to comply with all applicable copyright laws and regulations.

---------------------------
''',
'About': '''
--------------------------------------
               ABOUT US
--------------------------------------

Welcome to InCollege - Where Connections and Opportunities Thrive!

At InCollege, we are dedicated to providing a vibrant online platform for college students to connect with friends, explore exciting career opportunities, and foster meaningful professional relationships. Our mission is to empower students like you to unleash your full potential and shape a successful future.

Through our innovative features and cutting-edge technology, we strive to create a dynamic virtual space that bridges the gap between your academic journey and the professional world. Whether you're searching for internships, part-time jobs, or launching your post-graduation career, InCollege is your trusted companion.

Join our vibrant community today and embark on an exciting journey of personal growth, professional development, and lifelong connections.

--------------------------------------
''',
'Accessibility': '''
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
''',
'User Agreement': '''
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
''',
'Cookie Policy': '''
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
''',
'Brand Policy': '''
------------------------
     BRAND POLICY
------------------------

InCollege is committed to protecting its brand identity and ensuring consistent and accurate representation across all platforms. This Brand Policy outlines the guidelines for using the InCollege brand assets.

   1. Logo Usage: The InCollege logo should be used in its original form and should not be altered, distorted, or modified in any way.
   2. Colors and Typography: The official InCollege colors and typography should be used consistently to maintain brand consistency.
   3. Prohibited Usage: The InCollege brand assets should not be used in any manner that implies endorsement, affiliation, or partnership without proper authorization.

Any unauthorized usage of the InCollege brand assets is strictly prohibited.

------------------------
''',
'Help Center': '''
We're here to help
''',
'General About': '''
In College: Welcome to In College, the world's largest college student
network with many users in many countries and territories worldwide
''',
'Press': '''
In College Pressroom: Stay on top of the latest news, updates, and reports
'''}


  ## Skills to Learn ##
  def skillA(self):
      print("Project Management")
      print("Under Construction")
  def skillB(self):
      print("Networking")
      print("Under Construction")
  def skillC(self):
      print("System Design")
      print("Under Construction")
  def skillD(self):
      print("Coding")
      print("Under Construction")
  def skillE(self):
      print("Professional Communication")
      print("Under Construction")

  
  def initMenu(self):
      ## Set Home Page Items
      hpOpening = """
    Welcome To The InCollege Home Page!
      
    The Place Where Students Take The Next Big Step.

    "I Had To Battle With Anxiety Every Day Until I Signed Up For InCollege.
    Now, My Future Is On The Right Track And Im Able To Apply My Education To My Dream Career.
    Finding A Place In My Field Of Study Was A Breeze"
    - InCollege User

    """
      self.homePage.setOpening(hpOpening)
      self.homePage.addItem("Login", self.login)
      self.homePage.addItem("Register", self.register)
      self.homePage.addItem("Find People I Know", self.findUser)
      ##self.homePage.setSelection('4',{'label':'Delete Users','action':self.deleteTable})
      self.homePage.addItem("See Our Success Video", self.video_menu)
      self.homePage.addItem('Useful Links', self.useful_links)
      self.homePage.addItem('InCollege Important Links', self.important_links)
      ## Set Video Page Items
      self.videoMenu.setOpening("See Our Success Story:\n(Playing Video)\n")
      ## Set Main Menu Items
      self.mainMenu.addBackgroundAction(self.show_pending_message)
      self.mainMenu.addItem('Profile', self.user_profile_menu)
      self.mainMenu.addItem('Job/Internship Search', self.jobs_menu)
      # Find a Friend in mainMenu now Friends
      self.mainMenu.addItem('Friends', self.friend_menu)
      self.mainMenu.addItem('Learn A Skill', self.skills_menu)
      self.mainMenu.addItem('Useful Links', self.useful_links)
      self.mainMenu.addItem('InCollege Important Links', self.important_links)
      self.mainMenu.setExitStatement("Log Out")
      # Set Friends Item
      self.friendMenu.setOpening("Welcome To The Friends Page")
      self.friendMenu.addItem("Find A Friend", self.find_a_friend_menu)
      self.friendMenu.addItem("Show My Network", self.network_menu)
      self.friendMenu.addItem(
        lambda: f"Pending Requests ({len(self.user.receivedRequests)})", 
        self.received_friends_menu
      )
      self.friendMenu.addBackgroundAction(self.loadAllFriends)
      self.friendMenu.setExitStatement("Return To Main Menu")
      self.networkMenu.addBackgroundAction(self.show_network)
      self.displayFriendInfo.addBackgroundAction(self.loadAcceptedFriends)
      # Set Skill Items
      self.skillsMenu.setOpening("Please Select a Skill:")
      self.skillsMenu.addItem('Project Management',self.skillA)
      self.skillsMenu.addItem('Networking',self.skillB)
      self.skillsMenu.addItem('System Design',self.skillC)
      self.skillsMenu.addItem('Coding',self.skillD)
      self.skillsMenu.addItem('Professional Communication',self.skillE)
      self.skillsMenu.setExitStatement("Return To Main Menu")
      # Set Join Items
      self.joinMenu.addItem('Login',self.login)
      self.joinMenu.addItem('Register',self.register)
      # Set Post A Job Items
      self.jobsMenu.setOpening("Welcome to the Job Postings Page")
      self.jobsMenu.addItem('Post Job',self.postJob)
      self.jobsMenu.setExitStatement("Return To Main Menu")
      # Set InCollege Important Links
      self.importantLinks.setOpening("Welcome to the Important Links Page")
      self.importantLinks.addItem('Copyright Notice', lambda: self.quick_menu(System.content["Copyright Notice"]))
      self.importantLinks.addItem('About', lambda: self.quick_menu(System.content["About"]))
      self.importantLinks.addItem('Accessibility', lambda: self.quick_menu(System.content["Accessibility"]))
      self.importantLinks.addItem('User Agreement', lambda: self.quick_menu(System.content["User Agreement"]))
      self.importantLinks.addItem('Privacy Policy', self.privacy_menu)
      self.importantLinks.addItem('Cookie Policy', lambda: self.quick_menu(System.content["Cookie Policy"]))
      self.importantLinks.addItem('Brand Policy', lambda: self.quick_menu(System.content["Brand Policy"]))
      self.importantLinks.addItem('Languages', self.language_menu, lambda: True if self.user.loggedOn else False)
      self.importantLinks.setExitStatement("Return To Home Page")
      # Set Guest Controls Items  
      self.guestControls.setOpening("Guest Controls:\n")
      self.guestControls.addItem((lambda: f"Email [{'ON' if self.user.email else 'OFF'}]"), self.setUserEmail)
      self.guestControls.addItem((lambda: f"SMS [{'ON' if self.user.sms else 'OFF'}]"), self.setUserSMS)
      self.guestControls.addItem(
        (lambda: f"Targeted Advertising [{'ON' if self.user.targetedAds else 'OFF'}]"), 
        self.setUserTargetedAds)
      self.guestControls.setExitStatement("Back")
      # Set Languages Items
      self.languageMenu.setOpening("Languages:")
      for language in LANGUAGES:
        """give parameter to lambda functions here 
        as workaround for python's lambda function late binding feature 
        otherwise all menu items will be created with the last language in the list """
        label = lambda lang=language: f"{lang} [{'X' if self.user.language == lang else ' '}]"
        action = lambda lang=language: self.setUserLanguage(lang)
        self.languageMenu.addItem(label, action)
      self.languageMenu.setExitStatement("Back")
      # Privacy page
      privacyPolicy = """
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
      """
      #Privacy menu just to have the option for guest controls if logged in
      self.privacyMenu.setOpening(privacyPolicy)
      self.privacyMenu.addItem('Guest Controls', self.guest_controls, lambda: True if self.user.loggedOn else False)
      #Useful links menu
      self.usefulLinks.setOpening("Welcome to the Useful Links Page")
      self.usefulLinks.addItem('General', self.general_menu)
      self.usefulLinks.addItem('Browse InCollege', lambda: self.quick_menu("Under Construction"))
      self.usefulLinks.addItem('Business Solutions', lambda: self.quick_menu("Under Construction"))
      self.usefulLinks.addItem('Directories', lambda: self.quick_menu("Under Construction"))
      #General links menu navigation links
      self.generalMenu.setOpening('General Links')
      self.generalMenu.addItem('Sign Up', lambda: self.join_menu("Sign Up:", "Back"), lambda: True if not self.user.loggedOn else False) #Disapears when user logs in
      self.generalMenu.addItem('Help Center', lambda: self.quick_menu(System.content["Help Center"]))
      self.generalMenu.addItem('About', lambda: self.quick_menu(System.content["General About"]))
      self.generalMenu.addItem('Press', lambda: self.quick_menu(System.content["Press"]))
      self.generalMenu.addItem('Blog', lambda: self.quick_menu("Under Construction"))
      self.generalMenu.addItem('Careers', lambda: self.quick_menu("Under Construction"))
      self.generalMenu.addItem('Developers', lambda: self.quick_menu("Under Construction"))
      # Set Find a Friend (search) Menu Items
      self.findAFriend.setOpening('Search For InCollege Users By:')
      self.findAFriend.addItem('Last Name', lambda: self.searchUserByField('lName'))
      self.findAFriend.addItem('University', lambda: self.searchUserByField('university'))
      self.findAFriend.addItem('Major', lambda: self.searchUserByField('major'))