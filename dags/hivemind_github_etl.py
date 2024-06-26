from __future__ import annotations

import logging
from datetime import datetime

from airflow import DAG
from airflow.decorators import task
from hivemind_etl_helpers.github_etl import process_github_vectorstore
from hivemind_etl_helpers.src.utils.modules import ModulesGitHub

with DAG(
    dag_id="github_vector_store",
    start_date=datetime(2024, 2, 21),
    schedule_interval="0 2 * * *",
) as dag:

    @task
    def get_github_communities():
        github_communities = ModulesGitHub().get_learning_platforms()
        return github_communities

    @task
    def process_github_community(community_information: dict[str, str | datetime]):
        community_id = community_information["community_id"]
        organization_ids = community_information["organization_ids"]
        repo_ids = community_information["repo_ids"]
        from_date = community_information["from_date"]

        logging.info(f"Starting Github ETL | community_id: {community_id}")
        process_github_vectorstore(
            community_id=community_id,
            github_org_ids=organization_ids,
            repo_ids=repo_ids,
            from_starting_date=from_date,
        )

    communities_info = get_github_communities()
    process_github_community.expand(community_information=communities_info)
