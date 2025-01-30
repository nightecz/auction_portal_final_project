### Auction portal project

## About the project
This project is an auction portal created in Django framework that allows users to create and manage auctions of items, bid and communicate, and finally add feedback on the trade between each other.

## Description
The auction portal project allows registered users to list their items, which other users interested in buying can bid on, after the auction is over, the application portal takes care of mediating the business relationship (i.e. passing on the contacts to each other), after the whole transaction is over, both parties can give each other feedback, which is then listed to other users, who can buy items from verified users thanks to the feedback. Users can add auctions to their watchlist and track their progress within the user interface, and completed auctions that do not sell can simply be put back into an active state.
We chose Django as the framework for our auction portal because of its robustness, built-in features, and development capabilities. Django provides an ORM, authentication system, and scalability, which were crucial for our project.
Regarding the additional packages:

- django-active-link (for improving the user experience),
- pillow (needed for handling image uploads for auction item photos),
- etc.


## Functionalities

- User registration and login
- Creating and managing profiles (including avatars)
- Adding and managing auctions
- Ability to monitor auctions and manage own watchlist
- Bidding on auctions
- Filtering auctions by user, city, price , and other advanced searching
- Relisting auctions
- Premium accounts
- Auction auto life-time cycle


## Project structure

apps/: Contains Django applications
templates/: HTML templates
static/: Static files (CSS, JS, images)
media/: Uploaded files such as avatars and auction images



## Visuals ORM
Depending on what you are making, it can be a good idea to include screenshots or even a video (you'll frequently see GIFs rather than actual videos). Tools like ttygif can help, but check out Asciinema for a more sophisticated method.

![Uploading image.png…]()


## Requirements
tools needed to run the project:
Python: 3.10+
Django: 4.x
SQLite (or other database)
Other libraries can be found in the requirements.txt file.

## How to install a Installation
Within a particular ecosystem, there may be a common way of installing things, such as using Yarn, NuGet, or Homebrew. However, consider the possibility that whoever is reading your README is a novice and would like more guidance. Listing specific steps helps remove ambiguity and gets people to using your project as quickly as possible. If it only runs in a specific context like a particular programming language version or operating system or has dependencies that have to be installed manually, also add a Requirements subsection.

1) Clone the repository:
git clone https://gitlab.com/user_name/project_name.git
cd project_name

2) Create and activate the virtual environment:
python -m venv venv
For MacOS: source venv/bin/activate
For Windows: venv\Scripts\activate

3) Install the required libraries:
pip install -r requirements.txt

4) Perform the database migration:
python manage.py migrate

5) Start the server:
python manage.py runserver

## Testing
To run tests used command:
python manage.py test

## Roadmap
- More details into auctions
- Better management for auctions picture
- Auto-Relisting functions
- Messages between users
- Multi-language Support
- Add Changelog
- Cookies


## Contributing
If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement". Don't forget to give the project a star! Thanks again!

## Fork the Project
Create your Feature Branch (git checkout -b feature/AmazingFeature)
Make changes and test them locally. Run tests using: python manage.py test
Commit your Changes (git commit -m 'Add some AmazingFeature')
Push to the Branch (git push origin feature/AmazingFeature)
Open a Pull Request


## Support
Feel free to email the original founders of the project at: -
jakub.hazda@gmail.com
mprudic@gmail.com

## License
Distributed under the Unlicence Licence.
