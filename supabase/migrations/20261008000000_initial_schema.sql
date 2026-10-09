-- Esquema inicial del agente RAG de cócteles.
-- Reejecutable: las políticas se eliminan antes de recrearse.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS public.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL CHECK (source_type IN ('cocktaildb', 'upload')),
    source_uri TEXT,
    external_id TEXT,
    filename TEXT,
    mime_type TEXT,
    size_bytes BIGINT CHECK (size_bytes IS NULL OR size_bytes >= 0),
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'ready', 'error')),
    title TEXT,
    checksum TEXT,
    error_message TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),
    content TEXT NOT NULL,
    embedding extensions.vector(1024),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(document_id, chunk_index)
);

CREATE TABLE IF NOT EXISTS public.conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    sources JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS documents_owner_id_idx
    ON public.documents(owner_id);
CREATE INDEX IF NOT EXISTS document_chunks_document_id_idx
    ON public.document_chunks(document_id);
CREATE INDEX IF NOT EXISTS conversations_user_id_idx
    ON public.conversations(user_id);
CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw_idx
    ON public.document_chunks
    USING hnsw (embedding vector_cosine_ops)
    WHERE embedding IS NOT NULL;

ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS documents_authenticated_select
    ON public.documents;
DROP POLICY IF EXISTS documents_authenticated_insert
    ON public.documents;
DROP POLICY IF EXISTS documents_authenticated_update
    ON public.documents;
DROP POLICY IF EXISTS documents_authenticated_delete
    ON public.documents;
DROP POLICY IF EXISTS document_chunks_authenticated_select
    ON public.document_chunks;
DROP POLICY IF EXISTS conversations_authenticated_all
    ON public.conversations;
DROP POLICY IF EXISTS messages_authenticated_all
    ON public.messages;

CREATE POLICY documents_authenticated_select
    ON public.documents
    FOR SELECT
    TO authenticated
    USING (
        owner_id = (SELECT auth.uid())
        OR (owner_id IS NULL AND (SELECT auth.uid()) IS NOT NULL)
    );

CREATE POLICY documents_authenticated_insert
    ON public.documents
    FOR INSERT
    TO authenticated
    WITH CHECK (owner_id = (SELECT auth.uid()));

CREATE POLICY documents_authenticated_update
    ON public.documents
    FOR UPDATE
    TO authenticated
    USING (owner_id = (SELECT auth.uid()))
    WITH CHECK (owner_id = (SELECT auth.uid()));

CREATE POLICY documents_authenticated_delete
    ON public.documents
    FOR DELETE
    TO authenticated
    USING (owner_id = (SELECT auth.uid()));

CREATE POLICY document_chunks_authenticated_select
    ON public.document_chunks
    FOR SELECT
    TO authenticated
    USING (
        (SELECT auth.uid()) IS NOT NULL
        AND EXISTS (
            SELECT 1
            FROM public.documents AS d
            WHERE d.id = document_chunks.document_id
              AND (d.owner_id = (SELECT auth.uid()) OR d.owner_id IS NULL)
        )
    );

-- La ingesta de chunks se ejecutará en backend con service_role.

CREATE POLICY conversations_authenticated_all
    ON public.conversations
    FOR ALL
    TO authenticated
    USING (user_id = (SELECT auth.uid()))
    WITH CHECK (user_id = (SELECT auth.uid()));

CREATE POLICY messages_authenticated_all
    ON public.messages
    FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1
            FROM public.conversations AS c
            WHERE c.id = messages.conversation_id
              AND c.user_id = (SELECT auth.uid())
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1
            FROM public.conversations AS c
            WHERE c.id = messages.conversation_id
              AND c.user_id = (SELECT auth.uid())
        )
    );

CREATE OR REPLACE FUNCTION public.match_documents(
    query_embedding extensions.vector(1024),
    match_threshold REAL,
    match_count INTEGER
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    content TEXT,
    metadata JSONB,
    similarity REAL
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        dc.id,
        dc.document_id,
        dc.content,
        dc.metadata,
        (1 - (dc.embedding <=> query_embedding))::REAL AS similarity
    FROM public.document_chunks AS dc
    JOIN public.documents AS d ON d.id = dc.document_id
    WHERE dc.embedding IS NOT NULL
      AND (SELECT auth.uid()) IS NOT NULL
      AND (d.owner_id = (SELECT auth.uid()) OR d.owner_id IS NULL)
      AND (1 - (dc.embedding <=> query_embedding)) >= match_threshold
    ORDER BY dc.embedding <=> query_embedding
    LIMIT LEAST(GREATEST(match_count, 1), 50);
$$;
