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

import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.decorators import task
from github.github_api_helpers import (
    extract_linked_issues_from_pr,
    fetch_commit_files,
    fetch_commit_pull_requests,
    fetch_org_details,
    get_all_comment_reactions,
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
from github.neo4j_storage import (
    get_orgs_profile_from_neo4j,
    save_comment_to_neo4j,
    save_commit_files_changes_to_neo4j,
    save_commit_to_neo4j,
    save_commits_relation_to_pr,
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

        # !for testing
        # toghether_crew_org = {
        #     "id": 1,
        #     "name": "TogetherCrew",
        #     "description": """TogetherCrew is a community of developers, designers, and creators
        #     who are passionate about building and learning together.""",
        #     "url": "",
        #     "key": ""
        # }
        # rndao_org = {
        #     "id": 2,
        #     "name": "RnDAO",
        #     "description": """RnDAO is a community of developers, designers, and creators
        #     who are passionate about building and learning together.""",
        #     "url": "",
        #     "key": ""
        # }
        # orgs = [rndao_org, toghether_crew_org]
        # return orgs

    # region organization ETL
    @task
    def extract_github_organization(organization):
        logging.info(f"All data from last stage: {organization}")
        organization_name = organization["name"]
        org_info = fetch_org_details(org_name=organization_name)

        return {"organization_basic": organization, "organization_info": org_info}

    @task
    def transform_github_organization(organization):
        logging.info(f"All data from last stage: {organization}")
        return organization

    @task
    def load_github_organization(organization):
        logging.info(f"All data from last stage: {organization}")
        organization_info = organization["organization_info"]

        save_orgs_to_neo4j(organization_info)
        return organization

    # endregion

    # region organization members ETL
    @task
    def extract_github_organization_members(organization):
        logging.info(f"All data from last stage: {organization}")
        organization_name = organization["organization_basic"]["name"]
        members = get_all_org_members(org=organization_name)

        return {"organization_members": members, **organization}

    @task
    def transform_github_organization_members(data):
        logging.info(f"All data from last stage: {data}")
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
        for i, organization in enumerate(organizations):
            logging.info(f"Iteration {i + 1}/{len(organization)}")
            repos = get_all_org_repos(
                org_name=organization["organization_basic"]["name"]
            )
            repos = list(map(lambda repo: {"repo": repo, **organization}, repos))

            all_repos.extend(repos)

        return all_repos

    @task
    def transform_github_repos(repo):
        logging.info("Just passing through github repos")

        return repo

    @task
    def load_github_repos(repo):
        repo = repo["repo"]

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
        new_data = {"prs": prs, **data}
        return new_data

    @task
    def extract_pull_request_linked_issues(data):
        repo = data["repo"]
        prs = data["prs"]
        owner = repo["owner"]["login"]
        repo_name = repo["name"]

        new_prs = []
        for i, pr in enumerate(prs):
            logging.info(f"Processing iter {i + 1}/{len(prs)}")
            pr_number = pr["number"]
            linked_issues = extract_linked_issues_from_pr(
                owner=owner, repo=repo_name, pull_number=pr_number
            )
            new_prs.append({**pr, "linked_issues": linked_issues})

        new_data = {**data, "prs": new_prs}
        return new_data

    @task
    def transform_pull_requests(data):
        logging.info("Just passing throught PRs for now!")
        return data

    @task
    def load_pull_requests(data):
        prs = data["prs"]
        repository_id = data["repo"]["id"]
        for i, pr in enumerate(prs):
            logging.info(f"Iteration {i + 1}/{len(prs)}")
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
        for i, pr in enumerate(prs):
            logging.info(f"Iteration {i + 1}/{len(prs)}")
            files_changes = get_all_pull_request_files(
                owner=owner, repo=repo_name, pull_number=pr.get("number", None)
            )
            pr_files_changes[pr["id"]] = files_changes

        return {"pr_files_changes": pr_files_changes, **data}

    @task
    def transform_pull_request_files_changes(data):
        logging.info("Just passing through the data for now!")
        return data

    @task
    def load_pull_request_files_changes(data):
        pr_files_changes = data["pr_files_changes"]
        repository_id = data["repo"]["id"]

        for idx, (pr_id, files_changes) in enumerate(pr_files_changes.items()):
            logging.info(f"Iteration {idx + 1}/{len(pr_files_changes)}")
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
        for i, pr in enumerate(prs):
            logging.info(f"Iteration {i}/{len(prs)}")
            reviews = get_all_reviews_of_pull_request(
                owner=owner, repo=repo_name, pull_number=pr.get("number", None)
            )
            pr_reviews[pr["id"]] = reviews

        return {"pr_reviews": pr_reviews, **data}

    @task
    def transform_pr_review(data):
        logging.info("Just passing through the data for now!")
        return data

    @task
    def load_pr_review(data):
        pr_reviews = data["pr_reviews"]

        for idx, (pr_id, reviews) in enumerate(pr_reviews.items()):
            logging.info(f"Iteration {idx + 1}/{len(pr_reviews)}")
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
        return {"review_comments": review_comments, **data}

    @task
    def transform_pr_review_comments(data):
        logging.info("Just passing through the data for now!")
        return data

    @task
    def load_pr_review_comments(data):
        review_comments = data["review_comments"]
        repository_id = data["repo"]["id"]

        for i, review_comment in enumerate(review_comments):
            logging.info(f"Iteration {i + 1}/{len(review_comments)}")
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
        return {"comments": comments, **data}

    @task
    def extract_pr_issue_comments_reactions_member(data):
        comments = data["comments"]
        repo = data["repo"]
        owner = repo["owner"]["login"]
        repo_name = repo["name"]

        for comment in comments:
            reactions = get_all_comment_reactions(
                owner=owner, repo=repo_name, comment_id=comment.get("id", None)
            )
            comment["reactions_member"] = reactions

        return {"comments": comments, **data}

    @task
    def transform_pr_issue_comments(data):
        logging.info("Just passing through the data for now!")
        return data

    @task
    def load_pr_issue_comments(data):
        comments = data["comments"]
        repository_id = data["repo"]["id"]

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
        logging.info("Just passing through the data for now!")
        return data

    @task
    def load_repo_contributors(data):
        contributors = data["contributors"]
        repository_id = data["repo"]["id"]

        for i, contributor in enumerate(contributors):
            logging.info(f"Iteration {i + 1}/{len(contributors)}")
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

        return {"issues": issues, **data}

    @task
    def transform_issues(data):
        logging.info("Just passing through the data for now!")
        return data

    @task
    def load_issues(data):
        issues = data["issues"]
        repository_id = data["repo"]["id"]

        for i, issue in enumerate(issues):
            logging.info(f"Iteration {i + 1}/{len(issues)}")
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
        logging.info("Just passing through the data for now!")
        return data

    @task
    def load_labels(data):
        labels = data["labels"]

        for i, label in enumerate(labels):
            logging.info(f"Iteration {i + 1}/{len(labels)}")
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
        logging.info("Just passing through the data for now!")
        return data

    @task
    def load_commits(data):
        commits = data["commits"]
        repository_id = data["repo"]["id"]

        for i, commit in enumerate(commits):
            logging.info(f"Iteration {i + 1}/{len(commits)}")
            save_commit_to_neo4j(commit=commit, repository_id=repository_id)

        return data

    # endregion

    # region of pull requests for commit
    @task
    def extract_commit_pull_requests(data):
        commits = data["commits"]
        commit_prs = {}
        for i, commit in enumerate(commits):
            logging.info(f"Iteration {i + 1}/{len(commits)}")
            repo = data["repo"]
            owner = repo["owner"]["login"]
            repo_name = repo["name"]

            prs = fetch_commit_pull_requests(owner, repo_name, commit["sha"])
            commit_prs[commit["sha"]] = prs

        new_data = {**data, "commit_prs": commit_prs}
        return new_data

    @task
    def load_commit_pull_requests(data):
        commit_prs: dict = data["commit_prs"]
        repo_id = data["repo"]["id"]

        for idx, (commit_sha, prs) in enumerate(commit_prs.items()):
            logging.info(f"Iteration {idx + 1}/{len(commit_prs)}")
            save_commits_relation_to_pr(commit_sha, repo_id, prs)

        return data

    # endregion

    # region commits files changes ETL
    @task
    def extract_commits_files_changes(data):
        logging.info(f"All data from last stage: {data}")
        repo = data["repo"]
        owner = repo["owner"]["login"]
        repo_name = repo["name"]
        commits = data["commits"]

        commits_files_changes = {}
        for i, commit in enumerate(commits):
            logging.info(f"Iteration {i + 1}/{len(commits)}")
            sha = commit["sha"]
            files_changes = fetch_commit_files(owner=owner, repo=repo_name, sha=sha)
            commits_files_changes[sha] = files_changes

        return {"commits_files_changes": commits_files_changes, **data}

    @task
    def transform_commits_files_changes(data):
        logging.info("Just passing through the data for now!")
        return data

    @task
    def load_commits_files_changes(data):
        commits_files_changes = data["commits_files_changes"]
        repository_id = data["repo"]["id"]

        for idx, (sha, files_changes) in enumerate(commits_files_changes.items()):
            logging.info(f"Iteration {idx + 1}/{len(commits_files_changes)}")
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

    issues = extract_issues.expand(data=repos)
    transform_issue = transform_issues.expand(data=issues)
    load_issue = load_issues.expand(data=transform_issue)
    load_contributors >> load_issue
    load_label >> load_issue

    prs = extract_pull_requests.expand(data=repos)
    prs_linked_issues = extract_pull_request_linked_issues.expand(data=prs)
    transform_prs = transform_pull_requests.expand(data=prs_linked_issues)
    load_prs = load_pull_requests.expand(data=transform_prs)
    load_contributors >> load_prs
    load_label >> load_prs
    load_issue >> load_prs

    pr_files_changes = extract_pull_request_files_changes.expand(data=prs)
    transform_pr_files_changes = transform_pull_request_files_changes.expand(
        data=pr_files_changes
    )
    load_pr_files_changes = load_pull_request_files_changes.expand(
        data=transform_pr_files_changes
    )

    pr_reviews = extract_pr_review.expand(data=prs)
    transform_pr_review = transform_pr_review.expand(data=pr_reviews)
    load_pr_review = load_pr_review.expand(data=transform_pr_review)

    pr_review_comments = extract_pr_review_comments.expand(data=prs)
    transformed_pr_review_comments = transform_pr_review_comments.expand(
        data=pr_review_comments
    )
    load_pr_review_comments = load_pr_review_comments.expand(
        data=transformed_pr_review_comments
    )
    load_prs >> load_pr_review_comments

    pr_issue_comments = extract_pr_issue_comments.expand(data=prs)
    pr_issue_comments_with_reactions_member = (
        extract_pr_issue_comments_reactions_member.expand(data=pr_issue_comments)
    )
    transformed_pr_issue_comments = transform_pr_issue_comments.expand(
        data=pr_issue_comments_with_reactions_member
    )
    loaded_pr_issue_comments = load_pr_issue_comments.expand(
        data=transformed_pr_issue_comments
    )
    load_prs >> loaded_pr_issue_comments
    load_issue >> loaded_pr_issue_comments

    commits = extract_commits.expand(data=repos)
    commits_transformed = transform_commits.expand(data=commits)
    load_commit = load_commits.expand(data=commits_transformed)

    commit_prs = extract_commit_pull_requests.expand(data=commits_transformed)
    load_commit_prs = load_commit_pull_requests.expand(data=commit_prs)
    commit_prs >> load_commit_prs

    commits_files_changes = extract_commits_files_changes.expand(data=commits)
    transform_commits_files_changes = transform_commits_files_changes.expand(
        data=commits_files_changes
    )
    load_commits_files_changes = load_commits_files_changes.expand(
        data=transform_commits_files_changes
    )
    load_commit >> load_commits_files_changes
    load_pr_files_changes >> load_commits_files_changes
