"""Streamlit dashboard for MiMo Multi-Agent DevAssistant."""

from __future__ import annotations

import streamlit as st

from mimo_agents.agents.documenter import DocumenterAgent
from mimo_agents.agents.orchestrator import OrchestratorAgent
from mimo_agents.agents.planner import PlannerAgent
from mimo_agents.agents.reviewer import ReviewerAgent
from mimo_agents.agents.tester import TesterAgent
from mimo_agents.core.client import MiMoClient
from mimo_agents.core.config import Settings
from mimo_agents.core.models import DevTask, TaskStatus

st.set_page_config(
    page_title="MiMo DevAssistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


def get_client() -> MiMoClient | None:
    settings = Settings.from_env()
    api_key = st.session_state.get("api_key", settings.api_key)
    if not api_key:
        return None
    settings.api_key = api_key
    return MiMoClient(settings)


def render_sidebar() -> str:
    with st.sidebar:
        st.title("MiMo DevAssistant")
        st.caption("Multi-Agent AI Development Pipeline")

        st.divider()

        api_key = st.text_input(
            "MiMo API Key",
            type="password",
            value=st.session_state.get("api_key", ""),
            help="Your Xiaomi MiMo API key from platform.xiaomimimo.com",
        )
        if api_key:
            st.session_state["api_key"] = api_key

        st.divider()

        mode = st.radio(
            "Mode",
            ["Full Pipeline", "Code Review", "Test Generation", "Plan Only", "Documentation"],
            index=0,
        )

        st.divider()

        st.subheader("Models")
        settings = Settings.from_env()
        st.text(f"Reasoning: {settings.reasoning_model.model_id}")
        st.text(f"Multimodal: {settings.multimodal_model.model_id}")
        st.text(f"TTS: {settings.tts_model.model_id}")

        return mode


def render_main(mode: str) -> None:
    st.header(f"🤖 {mode}")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Input")
        title = st.text_input("Task Title", value="Dev Task")
        description = st.text_area(
            "Task Description",
            height=150,
            placeholder="Describe what you want to build or analyze...",
        )
        language = st.selectbox(
            "Language", ["python", "javascript", "typescript", "go", "rust", "java"]
        )
        source_code = st.text_area(
            "Source Code (optional)",
            height=200,
            placeholder="Paste existing code here for review/analysis...",
        )

        run_button = st.button("Run", type="primary", use_container_width=True)

    with col2:
        st.subheader("Output")

        if run_button:
            client = get_client()
            if not client:
                st.error("Please provide your MiMo API key in the sidebar.")
                return

            task = DevTask(
                title=title,
                description=description,
                language=language,
                source_code=source_code,
            )

            with st.spinner(f"Running {mode}..."):
                result = _run_mode(mode, client, task)

            if result.status == TaskStatus.COMPLETED:
                st.success(f"Completed in {result.duration_ms}ms")
            else:
                st.error(f"Failed: {result.error}")

            st.markdown(result.output)

            if result.artifacts:
                with st.expander("Artifacts"):
                    for key, value in result.artifacts.items():
                        st.text(f"📄 {key}")
                        st.code(value[:2000], language=language)

            usage = client.get_total_usage()
            st.metric("Total Tokens", f"{usage.total_tokens:,}")


def _run_mode(mode: str, client: MiMoClient, task: DevTask):
    context = {"generated_code": task.source_code} if task.source_code else {}

    if mode == "Full Pipeline":
        agent = OrchestratorAgent(client)
        return agent.process(task)
    elif mode == "Code Review":
        agent = ReviewerAgent(client)
        return agent.process(task, context=context)
    elif mode == "Test Generation":
        agent = TesterAgent(client)
        return agent.process(task, context=context)
    elif mode == "Plan Only":
        agent = PlannerAgent(client)
        return agent.process(task)
    elif mode == "Documentation":
        agent = DocumenterAgent(client)
        return agent.process(task, context=context)
    else:
        agent = OrchestratorAgent(client)
        return agent.process(task)


def main() -> None:
    mode = render_sidebar()
    render_main(mode)


if __name__ == "__main__":
    main()
