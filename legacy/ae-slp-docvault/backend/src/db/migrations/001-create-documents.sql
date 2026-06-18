-- Create documents table (original)
CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  file_type VARCHAR(50) NOT NULL,
  file_path VARCHAR(500) NOT NULL,
  tags TEXT[],
  uploaded_at TIMESTAMP NOT NULL DEFAULT NOW(),
  uploaded_by VARCHAR(100)
);
