from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import requests
import aiohttp

from config import GITLAB_URL, USER_ID, GITLAB_TOKEN, MANDAY_HOURS

# Prepare headers for requests
HEADERS = {'PRIVATE-TOKEN': GITLAB_TOKEN}


# def get_all_pages(url, params=None):
#     results = []
#     while url:
#         _response = requests.get(url, headers=HEADERS, params=params)
#         if _response.status_code != 200:
#             print(f"Failed to retrieve data: {_response.status_code} - {_response.text}")
#             break
#         results.extend(_response.json())
#         url = _response.links.get('next', {}).get('url')
#     return results


async def get_all_pages(url, params=None):
    results = []
    async with aiohttp.ClientSession() as session:
        while url:
            async with session.get(url, headers=HEADERS, params=params) as response:
                if response.status != 200:
                    print(f"Failed to retrieve data: {response.status} - {await response.text()}")
                    break
                results.extend(await response.json())
                url = response.links.get('next', {}).get('url')
    return results


async def get_commit_history(project_id):
    from_, to_ = from_to_date()

    commits_url = f'{GITLAB_URL}/projects/{project_id}/repository/commits'
    commits = await get_all_pages(commits_url)
    my_commits = [commit for commit in commits if commit['author_email'].startswith(USER_ID)]
    my_moth_commits = [commit for commit in my_commits
                       if from_.date() <= datetime.fromisoformat(commit.get('created_at')).date() <= to_.date()]
    return my_moth_commits


def from_to_date(break_point: int = 10):
    """Get first and last day of the month, if today is before break_point, return last month dates.
    :param break_point: day of the month, when the month is considered to be last month
    :return: tuple of first and last day of the month"""
    today = datetime.today()
    last_month = today - timedelta(days=30)
    first_day = today.replace(day=1)
    if today.day <= break_point:
        first_day = first_day.replace(month=last_month.month)
    last_day = first_day.replace(month=first_day.month + 1, day=1) - timedelta(days=1)
    return first_day, last_day


async def get_events_by_dates(projects):
    """Prepare data in format {date: [list of events]}, fill in all days with an empty list and return it.
    :param projects: list of projects
    :return: dict of events by date
    """
    # Příprava dat do formátu {date: [list of events]}, fill in all days with an empty list
    events_by_date = {date: None for date in pd.date_range(from_to_date()[0], from_to_date()[1]).strftime('%Y-%m-%d')}

    for project in projects:
        print(f"Processing project: {project.get('name')} ({project.get('id')})", end='\r')

        project_id = project['id']
        branches_url = f'{GITLAB_URL}/projects/{project_id}/repository/branches'

        # získat eventy pro daný projekt
        events = await get_all_pages(f'{GITLAB_URL}/projects/{project_id}/events')

        # sort by date and fill in events_by_date
        for event in events:
            event_date = event['created_at'][:10]
            if event_date not in events_by_date:
                continue
            if event['author']['username'] == USER_ID:
                res = extract_event_info(event)
                if res == '' and events_by_date.get(event_date) is None:
                    events_by_date[event_date]: Optional[list] = None  # empty comment
                elif len(res) > 8 and \
                        isinstance(events_by_date[event_date], list) and \
                        any(res[:6] in s for s in events_by_date[event_date]):
                    continue
                if events_by_date[event_date] is None:
                    events_by_date[event_date] = [res]
                else:
                    events_by_date[event_date].append(res)
    return events_by_date


def extract_event_info(event):
    action = event['action_name']

    if action in ['pushed to', 'pushed new']:
        ret = f"{event['push_data']['ref']}"
        # ret = ''
        return ret
    elif action == 'closed':
        new_branch = f"{event.get('target_iid', '')}-{event.get('target_title', '')}"
        return new_branch if len(new_branch) > 3 else None
    elif action in ['created', 'updated', 'reopened', 'merged']:
        return f"{event['target_type']} !{event['target_iid']}"  # : {event['target_title']}
    elif action in ['commented on', 'accepted', 'opened', 'assigned', 'unassigned', 'labeled', 'unlabeled', 'deleted']:
        return ''
    else:
        print('Unknown action:', action)
        # return None


def copy_from_to(df, source_date, target_date):
    year_month = df['date'][0][:7]
    source_date = f"{year_month}-{source_date}"
    target_date = f"{year_month}-{target_date}"

    if source_date not in df['date'].values or target_date not in df['date'].values:
        print(f"Source date {source_date} or target date {target_date} not found in DataFrame.")
        return df

    source_row = df[df['date'] == source_date].iloc[0]
    source_data = source_row.drop(labels='date')

    df.loc[df['date'] == target_date, source_data.index] = source_data.values
    return df


async def get_commits_by_dates(projects):
    # Příprava dat do formátu {date: [list of commits]}, fill in all days with an empty list
    commits_by_date = {date: None for date in pd.date_range(from_to_date()[0], from_to_date()[1]).strftime('%Y-%m-%d')}

    for project in projects:
        print(f"Processing project: {project.get('name')} ({project.get('id')})", end='\r')

        project_id = project['id']
        branches_url = f'{GITLAB_URL}/projects/{project_id}/repository/branches'

        # get events for the project
        events = await get_all_pages(f'{GITLAB_URL}/projects/{project_id}/events')

        # get branches for the project
        # not_deleted_branches = get_all_pages(branches_url)
        history_commits = await get_commit_history(project_id)

        # sort by date and fill in commits_by_date
        for commit in history_commits:
            commit_date = commit['created_at'][:10]
            if commit['title'].startswith('Merge'):
                continue
            commit_title = f"({project['name']}) {commit['title']}"
            if commit_date not in commits_by_date:
                continue
            commits_by_date[commit_date].append(commit_title)

    return commits_by_date


def get_dataframe(_commits_by_dates):
    # Create DataFrame
    data = {
        'surname': [],
        'name': [],
        'date': [],
        'hours': [],
        'note': []
    }
    for date in sorted(_commits_by_dates.keys()):
        if _commits_by_dates[date] is None:
            data['surname'].append('')  # empty
            data['name'].append('')  # empty
            data['date'].append(date)
            data['hours'].append('')  # empty
            data['note'].append('')  # empty
            continue
        name, surname = USER_ID.split('.')
        data['surname'].append(surname)
        data['name'].append(name)
        data['date'].append(date)
        data['hours'].append(MANDAY_HOURS)
        data['note'].append((', '.join(set(_commits_by_dates[date])).strip().strip(',').strip()))
    ret = pd.DataFrame(data)
    return ret
