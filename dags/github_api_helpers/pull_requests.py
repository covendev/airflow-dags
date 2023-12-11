from .smart_proxy import get


def fetch_pull_requests(owner: str, repo: str, page: int, per_page: int = 100):
    """
    Fetches the pull requests for a specific repo in a GitHub repository.

    :param owner: The owner of the repository.
    :param repo: The name of the repository.
    :param page: The page number of the results.
    :param per_page: The number of results per page (default is 100).
    :return: A list of pull requests for the specified repo.
    """
    endpoint = f'https://api.github.com/repos/{owner}/{repo}/pulls'

    params = {
        "per_page": per_page,
        "page": page,
        "state": "all",
    }
    response = get(endpoint, params=params)
    response_data = response.json()
    
    return response_data

def get_all_pull_requests(owner: str, repo: str):
    """
    Retrieves all pull requests for a specific repo in a GitHub repository.

    :param owner: The owner of the repository.
    :param repo: The name of the repository.
    :param pull_number: The number of the pull request.
    :return: A list of all commits for the specified pull request.
    """
    all_pull_requests = []
    current_page = 1

    while True:
        pull_requests = fetch_pull_requests(owner, repo, current_page)

        if not pull_requests:
            break  # No more pull requests to fetch

        all_pull_requests.extend(pull_requests)
        current_page += 1

    return all_pull_requests


def fetch_pull_requests_commits(owner: str, repo: str, pull_number: int, page: int, per_page: int = 100):
    """
    Fetches the commits for a specific pull request in a GitHub repository.

    :param owner: The owner of the repository.
    :param repo: The name of the repository.
    :param pull_number: The number of the pull request.
    :param page: The page number of the results.
    :param per_page: The number of results per page (default is 100).
    :return: A list of commits for the specified pull request.
    """
    endpoint = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/commits'

    params = {
        "per_page": per_page,
        "page": page
    }
    response = get(endpoint, params=params)
    response_data = response.json()
    
    return response_data

def get_all_commits_of_pull_request(owner: str, repo: str, pull_number: int):
    """
    Retrieves all commits for a specific pull request in a GitHub repository.

    :param owner: The owner of the repository.
    :param repo: The name of the repository.
    :param pull_number: The number of the pull request.
    :return: A list of all commits for the specified pull request.
    """
    all_commits = []
    current_page = 1

    while True:
        commits = fetch_pull_requests_commits(owner, repo, pull_number, current_page)

        if not commits:
            break  # No more commits to fetch

        all_commits.extend(commits)
        current_page += 1

    return all_commits


def fetch_pull_request_comments(owner: str, repo: str, issue_number: int, page: int, per_page: int = 30):
    """
    Fetches the comments for a specific issue page by page.

    :param owner: The owner of the repository.
    :param repo: The name of the repository.
    :param issue_number: The number of the issue.
    :param page: The page number of the results.
    :param per_page: The number of results per page (default is 30).
    :return: A list of comments for the specified issue page.
    """
    endpoint = f'https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments'
    params = {"page": page, "per_page": per_page}
    response = get(endpoint, params=params)
    return response.json()

def get_all_comments_of_pull_request(owner: str, repo: str, issue_number: int):
    """
    Retrieves all comments for a specific issue.

    :param owner: The owner of the repository.
    :param repo: The name of the repository.
    :param issue_number: The number of the issue.
    :return: A list of all comments for the specified issue.
    """
    all_comments = []
    current_page = 1
    while True:
        comments = fetch_pull_request_comments(owner, repo, issue_number, current_page)
        if not comments:  # Break the loop if no more comments are found
            break
        all_comments.extend(comments)
        current_page += 1
    return all_comments


def fetch_pull_request_review_comments(owner: str, repo: str, pull_number: int, page: int, per_page: int = 100):
    """
    Fetches the review comments for a specific pull request page by page.

    :param owner: The owner of the repository.
    :param repo: The name of the repository.
    :param pull_number: The number of the pull request.
    :param page: The page number of the results.
    :param per_page: The number of results per page (default is 30).
    :return: A list of review comments for the specified pull request page.
    """
    endpoint = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/comments'
    params = {"page": page, "per_page": per_page}
    response = get(endpoint, params=params)
    return response.json()

def get_all_review_comments_of_pull_request(owner: str, repo: str, pull_number: int):
    """
    Retrieves all review comments for a specific pull request.

    :param owner: The owner of the repository.
    :param repo: The name of the repository.
    :param pull_number: The number of the pull request.
    :return: A list of all review comments for the specified pull request.
    """
    all_comments = []
    current_page = 1
    while True:
        comments = fetch_pull_request_review_comments(owner, repo, pull_number, current_page)
        if not comments:  # Break the loop if no more comments are found
            break
        all_comments.extend(comments)
        current_page += 1
    return all_comments


def fetch_review_comment_reactions(owner: str, repo: str, comment_id: int, page: int, per_page: int = 100):
    """
    Fetches the reactions for a specific pull request comment.

    :param owner: The owner of the repository.
    :param repo: The name of the repository.
    :param comment_id: The ID of the comment.
    :param page: The page number of the results.
    :param per_page: The number of results per page (default is 100).
    :return: A list of reactions for the specified pull request comment.
    """
    endpoint = f'https://api.github.com/repos/{owner}/{repo}/pulls/comments/{comment_id}/reactions'
    params = {"page": page, "per_page": per_page}
    response = get(endpoint, params=params)
    return response.json()

def get_all_reactions_of_review_comment(owner: str, repo: str, comment_id: int):
    """
    Retrieves all reactions for a specific pull request comment.

    :param owner: The owner of the repository.
    :param repo: The name of the repository.
    :param comment_id: The ID of the comment.
    :return: A list of all reactions for the specified pull request comment.
    """
    all_reactions = []
    current_page = 1
    while True:
        reactions = fetch_comment_reactions(owner, repo, comment_id, current_page)
        if not reactions:  # Break the loop if no more reactions are found
            break
        all_reactions.extend(reactions)
        current_page += 1
    return all_reactions


def fetch_comment_reactions(owner: str, repo: str, comment_id: int, page: int, per_page: int = 100):
    """
    Fetches the reactions for a specific issue comment.

    :param owner: The owner of the repository.
    :param repo: The name of the repository.
    :param comment_id: The ID of the comment.
    :param page: The page number of the results.
    :param per_page: The number of results per page (default is 100).
    :return: A list of reactions for the specified issue comment.
    """
    endpoint = f'https://api.github.com/repos/{owner}/{repo}/issues/comments/{comment_id}/reactions'
    headers = {"Accept": "application/vnd.github.squirrel-girl-preview+json"}  # Custom media type is required
    params = {"page": page, "per_page": per_page}
    response = get(endpoint, headers=headers, params=params)
    return response.json()

def get_all_reactions_of_comment(owner: str, repo: str, comment_id: int):
    """
    Retrieves all reactions for a specific issue comment.

    :param owner: The owner of the repository.
    :param repo: The name of the repository.
    :param comment_id: The ID of the comment.
    :return: A list of all reactions for the specified issue comment.
    """
    all_reactions = []
    current_page = 1
    while True:
        reactions = fetch_comment_reactions(owner, repo, comment_id, current_page)
        if not reactions:  # Break the loop if no more reactions are found
            break
        all_reactions.extend(reactions)
        current_page += 1
    return all_reactions

def fetch_pull_request_reviews(owner: str, repo: str, pull_number: int, page: int, per_page: int = 100):
    """
    Fetches the reviews for a specific pull request page by page.

    :param owner: The owner of the repository.
    :param repo: The name of the repository.
    :param pull_number: The number of the pull request.
    :param page: The page number of the results.
    :param per_page: The number of results per page (default is 100).
    :return: A list of reviews for the specified pull request page.
    """
    endpoint = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/reviews'
    params = {"page": page, "per_page": per_page}
    response = get(endpoint, params=params)
    return response.json()

def get_all_reviews_of_pull_request(owner: str, repo: str, pull_number: int):
    """
    Retrieves all reviews for a specific pull request.

    :param owner: The owner of the repository.
    :param repo: The name of the repository.
    :param pull_number: The number of the pull request.
    :return: A list of all reviews for the specified pull request.
    """
    all_reviews = []
    current_page = 1
    while True:
        reviews = fetch_pull_request_reviews(owner, repo, pull_number, current_page)
        if not reviews:  # Break the loop if no more reviews are found
            break
        all_reviews.extend(reviews)
        current_page += 1
    return all_reviews