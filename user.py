class User:
  ## Not in Use Yet but will hold saved progress and relationships eventually
  ## Probably instantiate in system class and hold logged in status as well
  def __init__(self, userName, fName, lName, loggedOn=False, university=None, major=None, Profile=None):
    from system import LANGUAGES
    self.userName = userName
    self.fName = fName
    self.lName = lName
    # added university and major fields
    self.university = university
    self.major = major
    self.Profile = Profile
    self.email = True
    self.sms = True
    self.targetedAds = True
    self.language = LANGUAGES[0]
    # added three dicts for friend request feature 
    # key: username, value: user object
    self.sentRequests = {}
    self.acceptedRequests = {}
    self.receivedRequests = {}
    # loggedOn now false by default
    self.loggedOn = loggedOn
  def login(self, userName, fName, lName, university, major, email, sms, targetedAds, language):
    self.userName = userName
    self.fName = fName
    self.lName = lName
    self.university = university
    self.major = major
    self.email = email
    self.sms = sms
    self.targetedAds = targetedAds
    self.language = language
    self.loggedOn = True
  def logout(self):
    self.userName = "guest"
    self.fName = ""
    self.lName = ""
    self.sentRequests = {}
    self.acceptedRequests = {}
    self.receivedRequests = {}
    self.loggedOn = False
    self.Profile = None
  
    
  # check if profile has been created
  def hasProfile(self):
    return self.Profile is not None

  def displayProfile(self, mode):
    firstName = self.fName.capitalize()
    lastName = self.lName.capitalize()
    if mode == "full":
        profileString = "---------------\nViewing Profile\n---------------\n\n"
        profileString += f"Name: {firstName} {lastName}\n"
        
        if self.hasProfile():
            headline = self.Profile.headline
            about = self.Profile.about

            profileString += f"Title: {headline if headline else 'N/A'}\n"
            profileString += f"About: {about if about else 'N/A'}\n\n"
            # education section
            if self.Profile.education:
              university = self.Profile.education.university.title()
              major = self.Profile.education.major.title()
              yearsAttended = self.Profile.education.yearsAttended
              profileString += "Education\n..........\n\n"
              profileString += f" University: {university}\n"
              profileString += f" Degree: {major if major else 'N/A'}\n"
              profileString += f" Years Attended: {yearsAttended if yearsAttended else 'N/A'}\n"
            # experiences section 
            if self.Profile.experiences:
                for i, experience in enumerate(self.Profile.experiences, start = 1):
                    title = experience.title if experience.title else 'N/A'
                    employer = experience.employer if experience.employer else 'N/A'
                    startDate = experience.startDate if experience.startDate else 'N/A'
                    endDate = experience.endDate if experience.endDate else 'N/A'
                    location = experience.location if experience.location else 'N/A'
                    description = experience.description if experience.description else 'N/A'
                    profileString += f"\nExperience {i}\n"
                    profileString += ".............\n\n"
                    profileString += f" Title: {title}\n"
                    profileString += f" Employer: {employer}\n"
                    profileString += f" Start Date: {startDate}\n"
                    profileString += f" End Date: {endDate}\n"
                    profileString += f" Location: {location}\n"
                    profileString += f" Description: {description}\n\n"
        return profileString

    elif mode == "part":
        return f"Name: {firstName} {lastName}"


class profile:
  def __init__(self, headline=None, about=None, education=None, experiences=None):
    self.headline = headline
    self.about = about
    self.education = education
    self.experiences = experiences

class experience:
  def __init__(self, ID, title, employer, startDate, endDate, location, description):
    self.ID = ID
    self.title = title
    self.employer = employer
    self.startDate = startDate
    self.endDate = endDate
    self.location = location
    self.description = description

class education:
  def __init__(self, university, major, yearsAttended):
    self.university = university
    self.major = major
    self.yearsAttended = yearsAttended  