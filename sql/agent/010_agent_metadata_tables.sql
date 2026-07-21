create schema if not exists agent;
create schema if not exists extensions;

create extension if not exists vector with schema extensions;

set search_path = public, extensions, agent, analytics, staging, raw, audit;

create table if not exists agent.agent_registry (
    agent_name text primary key,
    domain text not null,
    description text not null,
    default_metrics text[] not null default array[]::text[],
    default_tables text[] not null default array[]::text[],
    owner_persona text,
    is_active boolean not null default true,
    updated_at timestamptz not null default now()
);

create table if not exists agent.metric_catalog (
    metric_name text primary key,
    domain text not null,
    description text not null,
    formula text not null,
    grain text not null,
    primary_source text not null,
    related_tables text[] not null default array[]::text[],
    owner_agent text not null references agent.agent_registry(agent_name),
    display_format text not null default 'number',
    caveats text,
    is_active boolean not null default true,
    updated_at timestamptz not null default now()
);

create table if not exists agent.sql_templates (
    template_name text primary key,
    domain text not null,
    agents text[] not null,
    keywords text[] not null default array[]::text[],
    metrics text[] not null default array[]::text[],
    tables text[] not null default array[]::text[],
    description text not null,
    sql_template text not null,
    result_grain text,
    chart_hint text,
    is_active boolean not null default true,
    updated_at timestamptz not null default now()
);

create table if not exists agent.question_examples (
    question_id text primary key,
    domain text not null,
    question_vi text not null,
    expected_agents text[] not null default array[]::text[],
    expected_template text references agent.sql_templates(template_name),
    metrics text[] not null default array[]::text[],
    tables text[] not null default array[]::text[],
    tags text[] not null default array[]::text[],
    difficulty text not null default 'basic',
    is_eval_question boolean not null default true,
    expected_warning text,
    updated_at timestamptz not null default now()
);

create table if not exists agent.rag_embeddings (
    node_id text primary key,
    node_type text not null,
    node_name text not null,
    source text not null,
    content text not null,
    metadata jsonb not null default '{}'::jsonb,
    embedding vector(384) not null,
    updated_at timestamptz not null default now()
);

create index if not exists agent_registry_domain_idx
    on agent.agent_registry(domain);

create index if not exists metric_catalog_domain_idx
    on agent.metric_catalog(domain);

create index if not exists metric_catalog_owner_agent_idx
    on agent.metric_catalog(owner_agent);

create index if not exists sql_templates_domain_idx
    on agent.sql_templates(domain);

create index if not exists sql_templates_keywords_gin_idx
    on agent.sql_templates using gin(keywords);

create index if not exists question_examples_domain_idx
    on agent.question_examples(domain);

create index if not exists question_examples_tags_gin_idx
    on agent.question_examples using gin(tags);

create index if not exists rag_embeddings_node_type_idx
    on agent.rag_embeddings(node_type);

create index if not exists rag_embeddings_metadata_gin_idx
    on agent.rag_embeddings using gin(metadata);

create index if not exists rag_embeddings_embedding_hnsw_idx
    on agent.rag_embeddings using hnsw (embedding vector_cosine_ops);
