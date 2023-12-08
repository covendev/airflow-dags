from .smart_proxy import get

def fetch_org_repos_page(org_name: str, page: int, per_page: int = 100):
    """
    Fetches the repos for a specific organization in GitHub.

    :param org_name: The name of the organization.
    :param page: The page number of the results.
    :param per_page: The number of results per page (default is 100).
    :return: A list of repos for the specified organization.
    """
    endpoint = f'https://api.github.com/orgs/{org_name}/repos'

    params = {
        "per_page": per_page,
        "page": page
    }
    response = get(endpoint, params=params)
    response_data = response.json()

    return response_data

def get_all_org_repos(org_name: str):
    """
    Retrieves all repos for a specific organization in GitHub.

    :param org_name: The name of the organization.
    :return: A list of repos for the specified organization.
    """
    all_repos = []
    current_page = 1

    while True:
        repos = fetch_org_repos_page(org_name, current_page)

        if not repos:
            break  # No more repositories to fetch

        all_repos.extend(repos)
        current_page += 1

    return all_repos

def fetch_repo_contributors_page(owner: str, repo: str, page: int, per_page: int = 100):
    """
    Fetches the contributors for a specific repository in GitHub.

    :param owner: The owner of the repository.
    :param repo: The name of the repository.
    :param page: The page number of the results.
    :param per_page: The number of results per page (default is 100).
    :return: A list of contributors for the specified repository.
    """
    endpoint = f'https://api.github.com/repos/{owner}/{repo}/contributors'

    params = {
        "per_page": per_page,
        "page": page
    }
    response = get(endpoint, params=params)
    response_data = response.json()

    return response_data

def get_all_repo_contributors(owner: str, repo: str):
    """
    Retrieves all contributors for a specific repository in GitHub.

    :param owner: The owner of the repository.
    :param repo: The name of the repository.
    :return: A list of contributors for the specified repository.
    """
    all_contributors = []
    current_page = 1

    while True:
        contributors = fetch_repo_contributors_page(owner, repo, current_page)

        if not contributors:
            break  # No more contributors to fetch

        all_contributors.extend(contributors)
        current_page += 1

    return all_contributors