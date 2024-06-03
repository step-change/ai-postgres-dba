#!/usr/bin/env python
import os

import psycopg

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents.base import Document


# From the awesome splinter project: https://github.com/supabase/splinter
QUERY = """
SELECT
	'unused_index' AS name,
	'INFO' AS level,
	'EXTERNAL' AS facing,
	ARRAY['PERFORMANCE'] AS categories,
	'Detects if an index has never been used and may be a candidate for removal.' AS description,
	format('Index \`%s\` on table \`%s.%s\` has not been used', psui.indexrelname, psui.schemaname, psui.relname) AS detail,
	'https://example.com/issues/0005' AS remediation,
	jsonb_build_object('schema', psui.schemaname, 'name', psui.relname, 'type', 'table') AS metadata,
	format('unused_index_%s_%s_%s', psui.schemaname, psui.relname, psui.indexrelname) AS cache_key
FROM
	pg_catalog.pg_stat_user_indexes psui
	JOIN pg_catalog.pg_index pi ON psui.indexrelid = pi.indexrelid
	LEFT JOIN pg_catalog.pg_depend dep ON psui.relid = dep.objid
		AND dep.deptype = 'e'
WHERE
	psui.idx_scan = 0
	AND NOT pi.indisunique
	AND NOT pi.indisprimary
	AND dep.objid IS NULL -- exclude tables owned by extensions
	AND psui.schemaname NOT IN ('_timescaledb_internal', 'auth', 'cron', 'extensions', 'graphql', 'graphql_public', 'information_schema', 'net', 'pgroonga', 'pgsodium', 'pgsodium_masks', 'pgtle', 'pgbouncer', 'pg_catalog', 'pgtle', 'realtime', 'repack', 'storage', 'supabase_functions', 'supabase_migrations', 'tiger', 'topology', 'vault');
"""

prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert database engineer and your task is to analyze the performance of a PostgreSQL database using the result of a SQL query.",
        ),
        ("human", "Query: {query}\nResult: {result}"),
    ]
)


def row_to_document(row: tuple) -> Document:
    return Document(
        page_content=row[5],
        metadata={
            "name": row[0],
            "level": row[1],
            "facing": row[2],
            "categories": row[3],
            "description": row[4],
            "remediation": row[6],
            "metadata": row[7],
            "cache_key": row[8],
        },
    )


def run_query(connection_string: str, query: str) -> list[Document]:
    with psycopg.connect(connection_string) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            return [row_to_document(row) for row in rows]


def main():
    connection_string = os.getenv("PG_DB_URI")
    if connection_string is None:
        raise ValueError("PG_DB_URI env var is required")

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key is None:
        raise ValueError("OPENAI_API_KEY env var is required")

    llm = ChatOpenAI(api_key=openai_api_key, model="gpt-4o")

    str_output_parser = StrOutputParser()
    chain = prompt_template | llm | str_output_parser

    docs = run_query(connection_string=connection_string, query=QUERY)

    response = chain.invoke({"query": QUERY, "result": docs})
    print(response)


if __name__ == "__main__":
    main()
