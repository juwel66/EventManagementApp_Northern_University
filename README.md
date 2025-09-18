The main objective of this project is to design and implement an Event Management System for university use. The system allows administrators to manage events, view registrations, and generate reports, while students can register for events, view upcoming programs, and track their participation. The goal is to reduce manual workload, improve efficiency, and make event handling more transparent.

Setup Requirements:

•	Programming Language: Python (Flask Framework)
Used because Flask is lightweight, easy to set up, and perfect for building small-to-medium web applications quickly.

•	Database: SQLite (events.db)
Chosen as the database since it’s simple, file-based, and requires no complex server setup, making it ideal for student projects.

•	Frontend: HTML, CSS, Bootstrap
Used for designing the frontend. HTML builds the structure, CSS styles it, and Bootstrap ensures responsive design (works well on mobile & desktop).

Installation Steps:

1.	Install Python 3.13.1 on your system.
 
2.	Install Flask and dependencies:
pip install flask
pip install flask_sqlalchemy
3.	Place the project folder (event_management_Northern_University) in your working directory.
4.	Run the application:
python app.py
5.	Open browser and go to: http://127.0.0.1:5000
 
Features of the System:

Admin Features

•	Admin Login: Ensures only authorized administrators can access event management functions, keeping the system secure.
•	Admin Dashboard: Provides a quick overview of events, registrations, and reports so the admin can manage everything in one place.
•	Add Event: Admin can create new events with details like title, description, date, and venue.
•	Manage Registrations: Admin can view registered students for each event.
•	Reports: Generates event-wise reports in table format, useful for analysis, decision-making, and record submission.

Student Features

•	Student Dashboard: Student dashboard showing upcoming and registered events.
•	Event List: Students can browse available events.
•	Registration: Students can register for events with name and ID , mobile details.
•	Confirmation: Students receive popup confirmation of successful registration.

