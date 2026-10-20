FROM python:3.12-slim
RUN useradd -m -u 1000 user
USER user
ENV PATH=/home/user/.local/bin:$PATH
WORKDIR /home/user/app
COPY --chown=user pyproject.toml README.md ./
COPY --chown=user src ./src
RUN pip install --no-cache-dir ".[llm]"
EXPOSE 7860
CMD ["uvicorn", "interviewer.api:app", "--host", "0.0.0.0", "--port", "7860"]
