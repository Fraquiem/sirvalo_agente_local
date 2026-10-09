-- Phase 3: idempotency and safe document ownership constraints.
CREATE UNIQUE INDEX IF NOT EXISTS documents_cocktaildb_external_id_uidx
  ON public.documents (external_id) WHERE source_type = 'cocktaildb' AND external_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS documents_upload_owner_checksum_uidx
  ON public.documents (owner_id, checksum) WHERE source_type = 'upload' AND owner_id IS NOT NULL AND checksum IS NOT NULL;
CREATE INDEX IF NOT EXISTS documents_source_type_status_idx
  ON public.documents (source_type, status);

-- Global rows are readable by authenticated users but cannot be inserted, updated,
-- or deleted through the user-facing token; backend ingestion uses service_role.
DROP POLICY IF EXISTS documents_authenticated_insert ON public.documents;
CREATE POLICY documents_authenticated_insert ON public.documents
  FOR INSERT TO authenticated WITH CHECK (owner_id = (SELECT auth.uid()));

DROP POLICY IF EXISTS documents_authenticated_delete ON public.documents;
CREATE POLICY documents_authenticated_delete ON public.documents
  FOR DELETE TO authenticated USING (owner_id = (SELECT auth.uid()));

COMMENT ON TABLE public.documents IS 'Private uploads and globally readable TheCocktailDB records; backend writes use service_role.';
COMMENT ON TABLE public.document_chunks IS 'Deterministic chunks with bge-m3 1024-dimensional embeddings.';
