from datetime import datetime
from unittest import TestCase

from github.neo4j_storage.neo4j_connection import Neo4jConnection
from hivemind_etl_helpers.src.db.github.extract.pull_requests import (
    fetch_raw_pull_requests,
)


class TestGithubETLFetchRawComments(TestCase):
    def setUp(self) -> None:
        neo4j_connection = Neo4jConnection()
        self.neo4j_driver = neo4j_connection.connect_neo4j()
        with self.neo4j_driver.session() as session:
            session.execute_write(lambda tx: tx.run("MATCH (n) DETACH DELETE (n)"))

    def test_get_empty_results_no_from_date(self):
        repository_ids = [123, 124]
        prs = fetch_raw_pull_requests(
            repository_id=repository_ids, from_date_created=None
        )
        self.assertEqual(prs, [])

    def test_get_empty_results(self):
        repository_ids = [123, 124]
        prs = fetch_raw_pull_requests(
            repository_id=repository_ids, from_date_created=datetime(2024, 1, 1)
        )
        self.assertEqual(prs, [])

    def test_get_single_pull_requests_single_repo_no_from_date(self):
        with self.neo4j_driver.session() as session:
            session.execute_write(
                lambda tx: tx.run(
                    """
                    CREATE (pr:GitHubPullRequest)<-[:CREATED]-(:GitHubUser {login: "author #1"})
                    SET
                        pr.id = 111,
                        pr.repository_id = 123,
                        pr.issue_url = "https://api.github.com/issues/1",
                        pr.created_at = "2024-02-06T10:23:50Z",
                        pr.closed_at = null,
                        pr.merged_at = null,
                        pr.state = "open",
                        pr.title = "sample title",
                        pr.html_url = "https://github.com/PullRequest/1",
                        pr.latestSavedAt = "2024-02-10T10:23:50Z"

                    CREATE (repo:GitHubRepository {id: 123, full_name: "Org/SampleRepo"})
                    """
                )
            )

        repository_ids = [123]
        prs = fetch_raw_pull_requests(
            repository_id=repository_ids,
        )

        self.assertEqual(len(prs), 1)
        self.assertEqual(prs[0]["id"], 111)
        self.assertEqual(prs[0]["created_at"], "2024-02-06T10:23:50Z")
        self.assertEqual(prs[0]["repository_name"], "Org/SampleRepo")
        self.assertEqual(prs[0]["latest_saved_at"], "2024-02-10T10:23:50Z")
        self.assertEqual(prs[0]["url"], "https://github.com/PullRequest/1")
        self.assertEqual(prs[0]["closed_at"], None)
        self.assertEqual(prs[0]["merged_at"], None)
        self.assertEqual(prs[0]["state"], "open")
        self.assertEqual(prs[0]["title"], "sample title")
        self.assertEqual(prs[0]["issue_url"], "https://api.github.com/issues/1")

    def test_get_single_pull_requests_single_repo_with_from_date(self):
        with self.neo4j_driver.session() as session:
            session.execute_write(
                lambda tx: tx.run(
                    """
                    CREATE (pr:GitHubPullRequest)<-[:CREATED]-(:GitHubUser {login: "author #1"})
                    SET
                        pr.id = 111,
                        pr.repository_id = 123,
                        pr.issue_url = "https://api.github.com/issues/1",
                        pr.created_at = "2024-02-06T10:23:50Z",
                        pr.closed_at = null,
                        pr.merged_at = null,
                        pr.state = "open",
                        pr.title = "sample title",
                        pr.html_url = "https://github.com/PullRequest/1",
                        pr.latestSavedAt = "2024-02-10T10:23:50Z"

                    CREATE (repo:GitHubRepository {id: 123, full_name: "Org/SampleRepo"})
                    """
                )
            )

        repository_ids = [123]
        prs = fetch_raw_pull_requests(
            repository_id=repository_ids,
            from_date_created=datetime(2024, 1, 1),
        )

        self.assertEqual(len(prs), 1)
        self.assertEqual(prs[0]["id"], 111)
        self.assertEqual(prs[0]["created_at"], "2024-02-06T10:23:50Z")
        self.assertEqual(prs[0]["repository_name"], "Org/SampleRepo")
        self.assertEqual(prs[0]["latest_saved_at"], "2024-02-10T10:23:50Z")
        self.assertEqual(prs[0]["url"], "https://github.com/PullRequest/1")
        self.assertEqual(prs[0]["closed_at"], None)
        self.assertEqual(prs[0]["merged_at"], None)
        self.assertEqual(prs[0]["state"], "open")
        self.assertEqual(prs[0]["title"], "sample title")
        self.assertEqual(prs[0]["issue_url"], "https://api.github.com/issues/1")
