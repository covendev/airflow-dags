import logging
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from hivemind_etl_helpers.src.db.discord.discord_summary import DiscordSummary
from hivemind_etl_helpers.src.db.discord.find_guild_id import (
    find_guild_id_by_platform_id,
)
from hivemind_etl_helpers.src.document_node_parser import configure_node_parser
from hivemind_etl_helpers.src.utils.sort_summary_docs import sort_summaries_daily
from llama_index.core import Settings
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.llms.openai import OpenAI
from tc_hivemind_backend.db.pg_db_utils import setup_db
from tc_hivemind_backend.db.utils.model_hyperparams import load_model_hyperparams
from tc_hivemind_backend.embeddings.cohere import CohereEmbedding
from tc_hivemind_backend.pg_vector_access import PGVectorAccess
from traceloop.sdk import Traceloop


def process_discord_summaries(
    community_id: str,
    platform_id: str,
    selected_channels: list[str],
    default_from_date: datetime,
    verbose: bool = False,
) -> None:
    """
    prepare the discord data by grouping it into thread, channel and day
    and save the processed summaries into postgresql

    Note: This will always process the data until 1 day ago.

    Parameters
    -----------
    community_id : str
        the community id to create or use its database
    platform_id : str
        discord platform id
    selected_channels : list[str]
        a list of channels to start processing the data
    default_from_date : datetime
        the default from_date set in db
    verbose : bool
        verbose the process of summarization or not
        if `True` the summarization process will be printed out
        default is `False`
    """
    load_dotenv()
    otel_endpoint = os.getenv("TRACELOOP_BASE_URL")
    Traceloop.init(app_name="hivemind-discord-summary", api_endpoint=otel_endpoint)

    chunk_size, _ = load_model_hyperparams()
    guild_id = find_guild_id_by_platform_id(platform_id)
    logging.info(f"COMMUNITYID: {community_id}, GUILDID: {guild_id}")
    table_name = "discord_summary"
    dbname = f"community_{community_id}"

    latest_date_query = f"""
            SELECT (metadata_->> 'date')::timestamp
            AS latest_date
            FROM data_{table_name}
            WHERE  (metadata_ ->> 'channel' IS NULL AND metadata_ ->> 'thread' IS NULL)
            ORDER BY (metadata_->>'date')::timestamp DESC
            LIMIT 1;
    """
    from_date = setup_db(
        community_id=community_id, dbname=dbname, latest_date_query=latest_date_query
    )
    if from_date is not None:
        # deleting any in-complete saved summaries (meaning for threads or channels)
        deletion_query = f"""
            DELETE FROM data_{table_name}
            WHERE (metadata_ ->> 'date')::timestamp > '{from_date.strftime("%Y-%m-%d")}';
        """
        from_date += timedelta(days=1)
    else:
        deletion_query = ""

    # if no data was saved, start pre-processing from the given date on modules document
    if from_date is None:
        from_date = default_from_date

    discord_summary = DiscordSummary(
        response_synthesizer=get_response_synthesizer(response_mode="tree_summarize"),
        verbose=verbose,
    )

    (
        thread_summaries_documents,
        channel_summary_documenets,
        daily_summary_documenets,
    ) = discord_summary.prepare_summaries(
        guild_id=guild_id,
        selected_channels=selected_channels,
        from_date=from_date,
        summarization_prefix="Please make a concise summary based only on the provided text from this",
    )

    logging.info("Getting the summaries embedding and saving within database!")

    # sorting the summaries per date
    # this is to assure in case of server break, we could continue from the previous date
    docs_daily_sorted = sort_summaries_daily(
        level1_docs=thread_summaries_documents,
        level2_docs=channel_summary_documenets,
        daily_docs=daily_summary_documenets,
    )

    node_parser = configure_node_parser(chunk_size=chunk_size)
    pg_vector = PGVectorAccess(table_name=table_name, dbname=dbname)

    Settings.node_parser = node_parser
    Settings.embed_model = CohereEmbedding()
    Settings.chunk_size = chunk_size
    Settings.llm = OpenAI(model="gpt-3.5-turbo")

    pg_vector.save_documents_in_batches(
        community_id=community_id,
        documents=docs_daily_sorted,
        batch_size=100,
        max_request_per_minute=None,
        request_per_minute=10000,
        deletion_query=deletion_query,
    )
