# Project 1

Web Programming with Python and JavaScript

When you start my app first time you will be redirected to home page where you can find sign up and log in button which redirects you to the corresponding page. login.html and register.html both files extend layout.html. If You are a new user you can register yourself from register.html,orr you can login. If you are not registered then you will be redirected to register.html. Existing users also is checked before registration. Succesfully registered you can try log in , in case of incorrect data message shows. Once logged in username displays with log out button.

User is redirected to dashboard.html after logged in. If you requested dashboard by GET , you will see simple quote and will be able search books database. If you request index by POST (searching for books) list of books shows in searchlist.html. Clicking one of the positions takes you to bookpage.html (bookpage)

 On bookpage.html author, year and isbn are loaded. Also from goodread.com API rating count and rating itself are loaded. Also all reviews received from users along with ratings are loaded one under one. On the bottom there is a plece where you can leave your review and rating of max 5 points. You can send only one review. On the very bottom there is a link to API page.

Clicking API button you will generate and will be redirected to json file with all data from my application. error.html file gives a 404 error if no books in isbn api.

Clicking Log out button session is cleared and users is logging out , index.html page is loaded after.

application.py is a main app file. Contains routing to all html files , queries to database and all other functions. import.py reads csv file and loads all books skipping first line (title row).