Todo App
Overview
The Todo App is a simple, responsive web application for managing tasks. Users can add, view, and mark tasks as complete, with a clean and intuitive interface. The app features real-time validation, a search functionality, and a responsive design that works across devices.
Features

Task Management: Create, view, and mark tasks as completed.
Search Functionality: Filter tasks by keyword with real-time input validation.
Responsive Design: Optimized for mobile, tablet, and desktop devices.
Accessible UI: Includes ARIA labels and focus states for better accessibility.
Interactive Elements: Smooth hover effects and touch-friendly buttons.

Technologies Used

Frontend:
HTML: Structure for the web interface.
CSS: Styling with responsive design and custom animations.
JavaScript: Client-side logic for form validation and interactive elements.
Font Awesome: Icons for visual enhancements (version 6.5.2).


Backend:
Python (Flask): Lightweight web framework for serving the frontend and handling task data.


Dependencies:
Flask (Python)
Font Awesome (via CDN)



Setup Instructions
Prerequisites

Python 3.8+: Required for running the Flask backend.
pip: Python package manager for installing dependencies.
A modern web browser (Chrome, Firefox, Safari, etc.).

Installation

Clone the Repository:
git clone https://github.com/your-username/todo-app.git
cd todo-app


Set Up the Backend:

Create a virtual environment:python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


Install Flask:pip install flask




Project Structure:
todo-app/
├── app.py               # Flask backend
├── static/
│   ├── css/
│   │   └── styles.css   # Custom CSS (if separated from index.html)
│   └── js/
│       └── script.js    # Custom JavaScript (if separated from index.html)
├── templates/
│   └── index.html       # Main HTML file
├── requirements.txt      # Python dependencies
└── README.md            # This file


Create the Flask App (app.py):
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)


Create requirements.txt:
flask==2.3.3


Run the Application:

Start the Flask server:python app.py


Open your browser and navigate to http://localhost:5000.



Usage

Access the App:

Visit http://localhost:5000 to see the Todo App interface.
The app displays a header with a title, filter button, and search bar, followed by pending and completed task sections.


Add Tasks:

Click the "Add Task" button (expands on hover) to add a new task (requires backend integration for full functionality).
Note: The current frontend assumes a future form/modal for task input.


Search Tasks:

Use the search bar to filter tasks. An error message appears if the search input is empty.


Mark Tasks as Complete:

Check the checkbox next to a task to mark it as completed. Completed tasks move to the "Completed" section with a strikethrough.


Responsive Design:

The app adapts to screen sizes, stacking elements vertically on mobile devices for better usability.



Development Notes

Frontend:
The HTML is structured in index.html with embedded CSS and JavaScript for simplicity.
Validation is implemented for the search bar, showing an error for empty inputs.
The add button and checkboxes use custom styles with smooth transitions.


Backend:
The Flask backend is minimal, serving the index.html template.
To fully implement task management, extend app.py with routes for adding, updating, and deleting tasks (e.g., using a database or in-memory storage).


Future Improvements:
Add a modal/form for task creation with validation.
Implement backend routes for task persistence (e.g., using SQLite or MongoDB).
Enhance search functionality to filter tasks dynamically using JavaScript.



Contributing

Fork the repository.
Create a new branch (git checkout -b feature/your-feature).
Make changes and commit (git commit -m "Add your feature").
Push to the branch (git push origin feature/your-feature).
Open a pull request.

License
This project is licensed under the MIT License.
