import os

from config import GITLAB_URL, PROJECTS, USER_ID
from cli.tools import get_all_pages, get_events_by_dates, get_dataframe, copy_from_to

from typer import Typer, echo
import asyncio


app = Typer()
df = None
__version__ = "0.1.0"


@app.command()
def version():
    """Show version and exit."""
    echo(__version__)


@app.command()
def prepare_table():
    """-> Prepare table with projects and events and save it to Excel file in output folder."""
    # get projects
    projects = asyncio.run(get_projects())
    # For each project get events and branches
    events_by_dates = asyncio.run(get_events_by_dates(projects))
    # Create DataFrame from data
    df = get_dataframe(events_by_dates)
    save_table(df)
    echo(df.to_string(index=False))


async def get_projects(all_projects=False):
    # owned projects
    owned_projects = await get_all_pages(f'{GITLAB_URL}/projects?owned=true')
    # projects where user is a member
    membership_projects = await get_all_pages(f'{GITLAB_URL}/projects?membership=true')
    # all active projects
    all_projects = await get_all_pages(f'{GITLAB_URL}/projects?archived=false') if all_projects else []

    # Combine owned and membership projects
    projects = {project['id']: project for project in
                (owned_projects + membership_projects + all_projects) if project['id'] in PROJECTS}.values()
    return projects


def save_table(df):
    if df is None:
        echo("> Table has not been prepared.")
        return
    script_dir = os.path.abspath(__file__.rsplit('/', 2)[0])
    year_month = df['date'][0][:7]
    surname = USER_ID.split(".")[0].upper()
    new_xlsx_file_path = os.path.join(script_dir, 'output', f'{year_month}-{surname}_timesheet.xlsx')
    file_path = os.path.join(script_dir, new_xlsx_file_path)
    df.to_excel(file_path, index=False)

    echo(f"> Data has been saved to {os.path.join('../output', file_path)}")


def main():
    app()


if __name__ == '__main__':
    app()
