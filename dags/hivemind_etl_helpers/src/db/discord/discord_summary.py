import logging
from datetime import datetime

from hivemind_etl_helpers.src.db.discord.summary.prepare_grouped_data import (
    prepare_grouped_data,
)
from hivemind_etl_helpers.src.db.discord.summary.prepare_summaries import (
    PrepareSummaries,
)
from hivemind_etl_helpers.src.db.discord.summary.summary_utils import (
    DiscordSummaryTransformer,
)
from llama_index.core import Document, Settings
from llama_index.core.response_synthesizers.base import BaseSynthesizer


class DiscordSummary(PrepareSummaries):
    def __init__(
        self,
        response_synthesizer: BaseSynthesizer | None = None,
        verbose: bool = False,
        **kwargs,
    ) -> None:
        """
        initialize the summary preparation class

        Parameters
        -----------
        set_response_synthesizer : BaseSynthesizer | None
            whether to set a response_synthesizer to refine the summaries or not
            if nothing passed would be set to `None`
        verbose : bool
            whether to show the progress of summarizing or not
        **kwargs :
            llm : LLM
                the llm to use
                if nothing passed, it would use the default `llama_index.core.Setting.llm`

        Note: `chunk_size` is read from `llama_index.core.Setting.chunk_size`.
        """
        llm = kwargs.get("llm", Settings.llm)
        self.discord_summary_transformer = DiscordSummaryTransformer()

        super().__init__(
            llm=llm, response_synthesizer=response_synthesizer, verbose=verbose
        )

    def prepare_summaries(
        self,
        guild_id: str,
        selected_channels: list[str],
        summarization_prefix: str,
        from_date: datetime,
    ) -> tuple[list[Document], list[Document], list[Document],]:
        """
        prepare per thread summaries of discord messages.
        Note: This will always process the data until 1 day ago.

        Parameters
        ------------
        guild_id : str
            the guild id to access data
        selected_channels: list[str]
            the discord channels to produce summaries
        summarization_prefix : str
            the summarization query prefix to do on the LLM
        from_date : datetime
            get the raw data from a specific date
            default is None, meaning get all the messages


        Returns
        ---------
        thread_summaries_documents : list[llama_index.Document]
            list of thread summaries converted to llama_index documents
        channel_summary_documenets : list[llama_index.Document]
            list of channel summaries converted to llama_index documents
        daily_summary_documenets : list[llama_index.Document]
            list of daily summaries converted to llama_index documents
        """
        summary_prompt_posfix = (
            ". Organize the output in one or multiple descriptive "
            "bullet points and include important details"
        )
        raw_data_grouped = prepare_grouped_data(guild_id, from_date, selected_channels)
        if raw_data_grouped != {}:
            thread_summaries = self.prepare_thread_summaries(
                guild_id,
                raw_data_grouped,
                (summarization_prefix + " discord thread" + summary_prompt_posfix),
            )
            (
                channel_summaries,
                thread_summary_documenets,
            ) = self.prepare_channel_summaries(
                thread_summaries,
                summarization_prefix
                + (" selection of discord thread summaries" + summary_prompt_posfix),
            )
            (
                daily_summaries,
                channel_summary_documenets,
            ) = self.prepare_daily_summaries(
                channel_summaries,
                (
                    summarization_prefix
                    + " selection of discord channel summaries"
                    + summary_prompt_posfix
                ),
            )
            daily_summary_documents = (
                self.discord_summary_transformer.transform_daily_summary_to_document(
                    daily_summaries
                )
            )
        else:
            logging.info(f"No data received after the data: {from_date}")
            thread_summary_documenets = []
            channel_summary_documenets = []
            daily_summary_documents = []

        return (
            thread_summary_documenets,
            channel_summary_documenets,
            daily_summary_documents,
        )
