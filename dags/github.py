# Licensed to the Apache Software Foundation (ASF) under one
#
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""Example DAG demonstrating the usage of dynamic task mapping."""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.decorators import task
from github_api_helpers import (
    fetch_commit_files,
    fetch_org_details,
    get_all_commits,
    get_all_issues,
    get_all_org_members,
    get_all_org_repos,
    get_all_pull_request_files,
    get_all_pull_requests,
    get_all_repo_contributors,
    get_all_repo_issues_and_prs_comments,
    get_all_repo_labels,
    get_all_repo_review_comments,
    get_all_reviews_of_pull_request,
)
from neo4j_storage import (
    get_orgs_profile_from_neo4j,
    save_comment_to_neo4j,
    save_commit_files_changes_to_neo4j,
    save_commit_to_neo4j,
    save_issue_to_neo4j,
    save_label_to_neo4j,
    save_org_member_to_neo4j,
    save_orgs_to_neo4j,
    save_pr_files_changes_to_neo4j,
    save_pull_request_to_neo4j,
    save_repo_contributors_to_neo4j,
    save_repo_to_neo4j,
    save_review_comment_to_neo4j,
    save_review_to_neo4j,
)

with DAG(
    dag_id="github_functionality",
    start_date=datetime(2022, 12, 1, 14),
    schedule_interval=timedelta(hours=6),
    catchup=False,
) as dag:

    @task
    def get_all_organization():
        orgs = get_orgs_profile_from_neo4j()
        return orgs

        #! for testing
        # toghether_crew_org = {
        #     "id": 1,
        #     "name": "TogetherCrew",
        #     "description": "TogetherCrew is a community of developers, designers, and creators who are passionate about building and learning together.",
        #     "url": "",
        #     "key": ""
        # }
        # rndao_org = {
        #     "id": 2,
        #     "name": "RnDAO",
        #     "description": "RnDAO is a community of developers, designers, and creators who are passionate about building and learning together.",
        #     "url": "",
        #     "key": ""
        # }
        # orgs = [rndao_org, toghether_crew_org]

    # region organization ETL
    @task
    def extract_github_organization(organization):
        organization_name = organization["name"]
        org_info = fetch_org_details(org_name=organization_name)

        return {"organization_basic": organization, "organization_info": org_info}

    @task
    def transform_github_organization(organization):
        return organization

    @task
    def load_github_organization(organization):
        organization_info = organization["organization_info"]

        save_orgs_to_neo4j(organization_info)
        return organization

    # endregion

    # region organization members ETL
    @task
    def extract_github_organization_members(organization):
        organization_name = organization["organization_basic"]["name"]
        members = get_all_org_members(org=organization_name)

        return {"organization_members": members, **organization}

    @task
    def transform_github_organization_members(data):
        print("data: ", data)
        return data

    @task
    def load_github_organization_members(data):
        members = data["organization_members"]
        org_id = data["organization_info"]["id"]

        for member in members:
            save_org_member_to_neo4j(org_id=org_id, member=member)

        return data

    # endregion

    # region github repos ETL
    @task
    def extract_github_repos(organizations):
        all_repos = []
        for organization in organizations:
            repos = get_all_org_repos(
                org_name=organization["organization_basic"]["name"]
            )
            repos = list(map(lambda repo: {"repo": repo, **organization}, repos))
            print("len-repos: ", len(repos))

            all_repos.extend(repos)

        return all_repos

    @task
    def transform_github_repos(repo):
        print("TRANSFORM REPO: ", repo)
        return repo

    @task
    def load_github_repos(repo):
        repo = repo["repo"]
        print("LOAD REPO: ", repo)

        save_repo_to_neo4j(repo)
        return repo

    # endregion

    # region pull requests ETL
    @task
    def extract_pull_requests(data):
        repo = data["repo"]
        owner = repo["owner"]["login"]
        repo_name = repo["name"]

        prs = get_all_pull_requests(owner=owner, repo=repo_name)
        for pr in prs:
            print("pr: ", pr, end="\n\n")

        new_data = {"prs": prs, **data}
        return new_data

    @task
    def transform_pull_requests(data):
        print("prs IN TRANSFORM: ", data)
        return data

    @task
    def load_pull_requests(data):
        print("prs IN REQUESTS: ", data)
        prs = data["prs"]
        repository_id = data["repo"]["id"]
        for pr in prs:
            print("PR(pull-request): ", pr)
            save_pull_request_to_neo4j(pr=pr, repository_id=repository_id)

        return data

    # endregion

    # region pull request files changes ETL
    @task
    def extract_pull_request_files_changes(data):
        repo = data["repo"]
        owner = repo["owner"]["login"]
        repo_name = repo["name"]
        prs = data["prs"]

        pr_files_changes = {}
        for pr in prs:
            files_changes = get_all_pull_request_files(
                owner=owner, repo=repo_name, pull_number=pr.get("number", None)
            )
            pr_files_changes[pr["id"]] = files_changes

        return {"pr_files_changes": pr_files_changes, **data}

    @task
    def transform_pull_request_files_changes(data):
        return data

    @task
    def load_pull_request_files_changes(data):
        pr_files_changes = data["pr_files_changes"]
        repository_id = data["repo"]["id"]

        for pr_id, files_changes in pr_files_changes.items():
            save_pr_files_changes_to_neo4j(
                pr_id=pr_id, repository_id=repository_id, file_changes=files_changes
            )

        return data

    # endregion

    # region pr review ETL
    @task
    def extract_pr_review(data):
        repo = data["repo"]
        owner = repo["owner"]["login"]
        repo_name = repo["name"]
        prs = data["prs"]

        pr_reviews = {}
        for pr in prs:
            reviews = get_all_reviews_of_pull_request(
                owner=owner, repo=repo_name, pull_number=pr.get("number", None)
            )
            pr_reviews[pr["id"]] = reviews

        return {"pr_reviews": pr_reviews, **data}

    @task
    def transform_pr_review(data):
        return data

    @task
    def load_pr_review(data):
        pr_reviews = data["pr_reviews"]

        for pr_id, reviews in pr_reviews.items():
            for review in reviews:
                save_review_to_neo4j(pr_id=pr_id, review=review)

        return data

    # endregion

    # region pr review comment ETL

    @task
    def extract_pr_review_comments(data):
        repo = data["repo"]
        owner = repo["owner"]["login"]
        repo_name = repo["name"]

        review_comments = get_all_repo_review_comments(owner=owner, repo=repo_name)
        for review_comment in review_comments:
            print("review_comment: ", review_comment, end="\n\n")

        return {"review_comments": review_comments, **data}

    @task
    def transform_pr_review_comments(data):
        return data

    @task
    def load_pr_review_comments(data):
        review_comments = data["review_comments"]
        repository_id = data["repo"]["id"]

        for review_comment in review_comments:
            save_review_comment_to_neo4j(
                review_comment=review_comment, repository_id=repository_id
            )

        return data

    # endregion

    # region pr & issue comments ETL
    @task
    def extract_pr_issue_comments(data):
        repo = data["repo"]
        owner = repo["owner"]["login"]
        repo_name = repo["name"]

        comments = get_all_repo_issues_and_prs_comments(owner=owner, repo=repo_name)
        for comment in comments:
            print("comment: ", comment, end="\n\n")

        return {"comments": comments, **data}

    @task
    def transform_pr_issue_comments(data):
        return data

    @task
    def load_pr_issue_comments(data):
        comments = data["comments"]
        repository_id = data["repo"]["id"]

        print("Len(comments): ", len(comments))
        for comment in comments:
            save_comment_to_neo4j(comment=comment, repository_id=repository_id)

        return data

    # endregion

    # region repo contributors ETL
    @task
    def extract_repo_contributors(data):
        repo = data["repo"]
        repo_name = repo["name"]
        owner = repo["owner"]["login"]
        contributors = get_all_repo_contributors(owner=owner, repo=repo_name)

        return {"contributors": contributors, **data}

    @task
    def transform_repo_contributors(data):
        print("contributors IN TRANSFORM: ", data)
        return data

    @task
    def load_repo_contributors(data):
        contributors = data["contributors"]
        repository_id = data["repo"]["id"]

        for contributor in contributors:
            save_repo_contributors_to_neo4j(
                contributor=contributor, repository_id=repository_id
            )

        return data

    # endregion

    # region issues ETL
    @task
    def extract_issues(data):
        repo = data["repo"]
        owner = repo["owner"]["login"]
        repo_name = repo["name"]
        issues = get_all_issues(owner=owner, repo=repo_name)

        print("issues IN TASK: ", issues)
        return {"issues": issues, **data}

    @task
    def transform_issues(data):
        return data

    @task
    def load_issues(data):
        issues = data["issues"]
        repository_id = data["repo"]["id"]

        for issue in issues:
            save_issue_to_neo4j(issue=issue, repository_id=repository_id)

        return data

    # endregion

    # region labels ETL
    @task
    def extract_labels(data):
        repo = data["repo"]
        owner = repo["owner"]["login"]
        repo_name = repo["name"]
        labels = get_all_repo_labels(owner=owner, repo=repo_name)

        return {"labels": labels, **data}

    @task
    def transform_labels(data):
        return data

    @task
    def load_labels(data):
        labels = data["labels"]

        for label in labels:
            save_label_to_neo4j(label=label)

        return data

    # endregion

    # region commits ETL
    @task
    def extract_commits(data):
        repo = data["repo"]
        owner = repo["owner"]["login"]
        repo_name = repo["name"]
        commits = get_all_commits(owner=owner, repo=repo_name)

        return {"commits": commits, **data}

    @task
    def transform_commits(data):
        return data

    @task
    def load_commits(data):
        commits = data["commits"]
        repository_id = data["repo"]["id"]

        for commit in commits:
            save_commit_to_neo4j(commit=commit, repository_id=repository_id)

        return data

    # endregion

    # region commits files changes ETL
    @task
    def extract_commits_files_changes(data):
        repo = data["repo"]
        owner = repo["owner"]["login"]
        repo_name = repo["name"]
        commits = data["commits"]

        commits_files_changes = {}
        for commit in commits:
            sha = commit["sha"]
            files_changes = fetch_commit_files(owner=owner, repo=repo_name, sha=sha)
            commits_files_changes[sha] = files_changes

        return {"commits_files_changes": commits_files_changes, **data}

    @task
    def transform_commits_files_changes(data):
        return data

    @task
    def load_commits_files_changes(data):
        commits_files_changes = data["commits_files_changes"]
        repository_id = data["repo"]["id"]

        for sha, files_changes in commits_files_changes.items():
            save_commit_files_changes_to_neo4j(
                commit_sha=sha, repository_id=repository_id, file_changes=files_changes
            )

        return data

    # endregion

    orgs = get_all_organization()
    orgs_info = extract_github_organization.expand(organization=orgs)
    transform_orgs = transform_github_organization.expand(organization=orgs_info)
    load_orgs = load_github_organization.expand(organization=transform_orgs)

    orgs_members = extract_github_organization_members.expand(organization=orgs_info)
    transform_orgs_members = transform_github_organization_members.expand(
        data=orgs_members
    )
    load_orgs_members = load_github_organization_members.expand(
        data=transform_orgs_members
    )
    load_orgs >> load_orgs_members

    repos = extract_github_repos(organizations=orgs_info)
    transform_repos = transform_github_repos.expand(repo=repos)
    load_repos = load_github_repos.expand(repo=transform_repos)
    load_orgs >> load_repos

    contributors = extract_repo_contributors.expand(data=repos)
    transform_contributors = transform_repo_contributors.expand(data=contributors)
    load_contributors = load_repo_contributors.expand(data=transform_contributors)
    load_repos >> load_contributors

    labels = extract_labels.expand(data=repos)
    transform_label = transform_labels.expand(data=labels)
    load_label = load_labels.expand(data=transform_label)

    prs = extract_pull_requests.expand(data=repos)
    transform_prs = transform_pull_requests.expand(data=prs)
    load_prs = load_pull_requests.expand(data=transform_prs)
    load_contributors >> load_prs
    load_label >> load_prs

    pr_files_changes = extract_pull_request_files_changes.expand(data=prs)
    transform_pr_files_changes = transform_pull_request_files_changes.expand(
        data=pr_files_changes
    )
    load_pr_files_changes = load_pull_request_files_changes.expand(
        data=transform_pr_files_changes
    )

    issues = extract_issues.expand(data=repos)
    transform_issue = transform_issues.expand(data=issues)
    load_issue = load_issues.expand(data=transform_issue)
    load_contributors >> load_issue
    load_label >> load_issue

    pr_reviews = extract_pr_review.expand(data=prs)
    transform_pr_review = transform_pr_review.expand(data=pr_reviews)
    load_pr_review = load_pr_review.expand(data=transform_pr_review)

    pr_review_comments = extract_pr_review_comments.expand(data=prs)
    transform_pr_review_comments = transform_pr_review_comments.expand(
        data=pr_review_comments
    )
    load_pr_review_comments = load_pr_review_comments.expand(
        data=transform_pr_review_comments
    )
    load_prs >> load_pr_review_comments

    pr_issue_comments = extract_pr_issue_comments.expand(data=prs)
    transformed_pr_issue_comments = transform_pr_issue_comments.expand(
        data=pr_issue_comments
    )
    loaded_pr_issue_comments = load_pr_issue_comments.expand(
        data=transformed_pr_issue_comments
    )
    load_prs >> loaded_pr_issue_comments
    load_issue >> loaded_pr_issue_comments

    commits = extract_commits.expand(data=repos)
    transform_comment = transform_commits.expand(data=commits)
    load_comment = load_commits.expand(data=transform_comment)

    commits_files_changes = extract_commits_files_changes.expand(data=commits)
    transform_commits_files_changes = transform_commits_files_changes.expand(
        data=commits_files_changes
    )
    load_commits_files_changes = load_commits_files_changes.expand(
        data=transform_commits_files_changes
    )
    load_comment >> load_commits_files_changes
    load_pr_files_changes >> load_commits_files_changes
