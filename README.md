# gitlab_activity_ts

Create a time series of GitLab project activity and save it as an Excel file, e.g. for **lazy timesheet reporting**.

This project is a command-line interface (CLI) tool built using Python's `Typer` for handling GitLab projects and data processing. 

It interacts with GitLab's API to retrieve project and event data, organizes it into a DataFrame, and supports saving the data in an Excel file.

## Features

- **Prepare Table**: Fetches GitLab projects and their respective events, organizing them into a DataFrame and saveing to Excel file.
- **Version Command**: Displays the current version of the tool.

[//]: # (- **Duplicate Lines**: Copies data between date ranges within the DataFrame.)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
    ```
2. Install the required dependencies:
    ```bash
    pipenv install
    ```
3. Configure the project by copying `config.example.py` to `config.py` and updating the values:
    ```bash
    cp config.example.py config.py
    vim config.py
    ```
   - GITLAB_URL: Your GitLab instance URL.
   - PROJECTS: List of project IDs to track.
   - USER_ID: Your GitLab user ID.

## Usage
```bash
# pipenv run python -m cli --help
pipenv run python cli.py prepare-table  # Prepare Table and save geerated file to output folder
```

## Author
Vojtech Marek

## Version
0.1.0

## License
This project is licensed under the MIT License - You can modify the content, particularly the repository URL and project name, to fit your actual project details.
