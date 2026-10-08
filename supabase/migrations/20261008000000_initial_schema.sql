-- Habilitar la extensión pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabla de Documentos
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES auth.users(id),
    source_type TEXT NOT NULL, -- 'cocktaildb' | 'upload'
    source_uri TEXT,
    external_id TEXT,
    filename TEXT,
    mime_type TEXT,
    size_bytes BIGINT,
    status TEXT DEFAULT 'pending', -- 'pending', 'processing', 'ready', 'error'
    title TEXT,
    checksum TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de Fragmentos de Documentos
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(768), -- Dimensión para nomic-embed-text (Ollama)
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(document_id, chunk_index)
);

-- Tabla de Conversaciones
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de Mensajes
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL, -- 'user' | 'assistant'
    content TEXT NOT NULL,
    sources JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Habilitar RLS (Row Level Security)
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Políticas de RLS
-- Documents: Usuarios ven sus propios documentos o documentos globales (owner_id es NULL)
CREATE POLICY "Users can view their own or global documents" ON documents
    FOR SELECT USING (auth.uid() = owner_id OR owner_id IS NULL);

CREATE POLICY "Users can insert their own documents" ON documents
    FOR INSERT WITH CHECK (auth.uid() = owner_id);

-- Document Chunks: Heredan visibilidad del documento
CREATE POLICY "Users can view chunks of accessible documents" ON document_chunks
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM documents 
            WHERE documents.id = document_chunks.document_id 
            AND (documents.owner_id = auth.uid() OR documents.owner_id IS NULL)
        )
    );

-- Conversations: Privadas por usuario
CREATE POLICY "Users can view their own conversations" ON conversations
    FOR ALL USING (auth.uid() = user_id);

-- Messages: Heredan visibilidad de la conversación
CREATE POLICY "Users can view messages of their conversations" ON messages
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM conversations 
            WHERE conversations.id = messages.conversation_id 
            AND conversations.user_id = auth.uid()
        )
    );
