-- Trigger to sync documents to documents_v2
-- BUG: deliberately omits the tags column
CREATE OR REPLACE FUNCTION sync_document_to_v2()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO documents_v2 (id, name, file_type, file_path, uploaded_at, uploaded_by)
  VALUES (NEW.id, NEW.name, NEW.file_type, NEW.file_path, NEW.uploaded_at, NEW.uploaded_by);
  -- NOTE: NEW.tags deliberately omitted from the INSERT
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_to_v2
  AFTER INSERT ON documents
  FOR EACH ROW
  EXECUTE FUNCTION sync_document_to_v2();
