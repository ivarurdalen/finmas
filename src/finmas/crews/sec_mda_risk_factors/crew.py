from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import LlamaIndexTool
from edgar import Filing

from finmas.constants import agent_config, defaults
from finmas.crews.model_provider import get_crewai_llm_model
from finmas.crews.utils import SECCrewConfiguration, get_log_filename
from finmas.data.sec.query_engine import get_sec_query_engine
from finmas.data.sec.sec_parser import SECTION_FILENAME_MAP


@CrewBase
class SECFilingSectionsCrew:
    """SEC Filing Sections Crew that is focused on specific sections of the SEC filing."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    name = "sec_mda_risk_factors"

    def __init__(
        self,
        ticker: str,
        llm_provider: str,
        llm_model: str,
        embedding_model: str,
        filing: Filing,
        temperature: float = defaults["llm_temperature"],
        max_tokens: int = defaults["llm_max_tokens"],
        similarity_top_k: int = defaults["similarity_top_k"],
        async_execution: bool = True,
    ):
        self.crewai_llm = get_crewai_llm_model(
            llm_provider, llm_model, temperature=temperature, max_tokens=max_tokens
        )
        for section in SECTION_FILENAME_MAP.keys():
            query_engine, metrics = get_sec_query_engine(
                ticker,
                llm_provider,
                llm_model,
                embedding_model,
                filing=filing,
                method=f"section:{section}",
                temperature=temperature,
                max_tokens=max_tokens,
                similarity_top_k=similarity_top_k,
            )
            setattr(self, f"{section}_query_engine", query_engine)
            setattr(self, f"{section}_index_creation_metrics", metrics)
            setattr(
                self,
                f"{section}_tool",
                LlamaIndexTool.from_query_engine(
                    getattr(self, f"{section}_query_engine"),
                    name=f"{filing.form} SEC Filing Query Tool for {ticker}",
                    description=f"Use this tool to search and analyze the the {filing.form} SEC filing",
                ),
            )

        self.config = SECCrewConfiguration(
            name=self.name,
            ticker=ticker,
            llm_provider=llm_provider,
            llm_model=llm_model,
            embedding_model=embedding_model,
            llm_temperature=temperature,
            llm_max_tokens=max_tokens,
            similarity_top_k=similarity_top_k,
            form_type=filing.form,
            filing_date=filing.filing_date,
        )
        self.async_execution = async_execution
        super().__init__()

    @agent
    def sec_filing_mda_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config["sec_filing_mda_analyzer"],  # type: ignore
            verbose=True,
            memory=True,
            llm=self.crewai_llm,
            tools=[self.mda_tool],  # type: ignore[attr-defined]
            **agent_config,
        )

    @agent
    def sec_filing_risk_factors_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config["sec_filing_risk_factors_analyzer"],  # type: ignore
            verbose=True,
            memory=True,
            llm=self.crewai_llm,
            tools=[self.risk_factors_tool],  # type: ignore[attr-defined]
            **agent_config,
        )

    @agent
    def sec_filing_summarizer(self) -> Agent:
        return Agent(
            config=self.agents_config["sec_filing_summarizer"],  # type: ignore
            verbose=True,
            memory=True,
            llm=self.crewai_llm,
            **agent_config,
        )

    @task
    def sec_filing_mda_task(self) -> Task:
        return Task(
            config=self.tasks_config["sec_filing_mda_task"],  # type: ignore
            async_execution=self.async_execution,
        )

    @task
    def sec_filing_risk_factors_task(self) -> Task:
        return Task(
            config=self.tasks_config["sec_filing_risk_factors_task"],  # type: ignore
            async_execution=self.async_execution,
        )

    @task
    def sec_filing_summary_task(self) -> Task:
        return Task(
            config=self.tasks_config["sec_filing_summary_task"],  # type: ignore
            context=[self.sec_filing_mda_task(), self.sec_filing_risk_factors_task()],
        )

    @crew
    def crew(self) -> Crew:
        """Creates SEC Filing Analysis crew."""
        return Crew(
            agents=self.agents,  # type: ignore
            tasks=[
                self.sec_filing_mda_task(),
                self.sec_filing_risk_factors_task(),
                self.sec_filing_summary_task(),
            ],
            cache=True,
            process=Process.sequential,
            verbose=True,
            planning=True,
            output_log_file=get_log_filename(self.name),
        )
