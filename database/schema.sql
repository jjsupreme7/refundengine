-- Washington State Tax Refund Engine Database Schema

CREATE TABLE clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_name TEXT NOT NULL,
    business_entity_type TEXT,
    ubi_number TEXT,
    contact_email TEXT,
    industry_classification TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE legal_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_type TEXT NOT NULL,
    citation TEXT,
    title TEXT,
    document_date DATE,
    effective_date DATE,
    expiration_date DATE,
    file_path TEXT NOT NULL,
    file_format TEXT,
    file_size_bytes INTEGER,
    last_updated DATE,
    processed_date TIMESTAMP,
    content_hash TEXT,
    raw_extracted_text TEXT,
    is_current BOOLEAN DEFAULT 1
);

CREATE TABLE document_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    page_number INTEGER,
    section_heading TEXT,
    FOREIGN KEY (document_id) REFERENCES legal_documents(id)
);

CREATE TABLE document_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    topic_tags TEXT,
    industries TEXT,
    key_concepts TEXT,
    tax_types TEXT,
    exemption_categories TEXT,
    referenced_statutes TEXT,
    FOREIGN KEY (document_id) REFERENCES legal_documents(id)
);

CREATE TABLE client_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    document_type TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_format TEXT,
    file_size_bytes INTEGER,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    document_date DATE,
    processed BOOLEAN DEFAULT 0,
    processing_status TEXT,
    error_message TEXT,
    classification_confidence INTEGER,
    FOREIGN KEY (client_id) REFERENCES clients(id)
);

CREATE TABLE invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    client_document_id INTEGER,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    vendor_name TEXT,
    vendor_address TEXT,
    vendor_city TEXT,
    vendor_state TEXT,
    vendor_zip TEXT,
    invoice_date DATE,
    invoice_number TEXT,
    purchase_order_number TEXT,
    total_amount DECIMAL(10,2),
    sales_tax_charged DECIMAL(10,2),
    use_tax_charged DECIMAL(10,2),
    customer_name TEXT,
    ship_to_address TEXT,
    ship_to_city TEXT,
    ship_to_state TEXT,
    bill_to_address TEXT,
    payment_terms TEXT,
    raw_extracted_text TEXT,
    extraction_confidence INTEGER,
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (client_document_id) REFERENCES client_documents(id)
);

CREATE TABLE purchase_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    client_document_id INTEGER,
    po_number TEXT,
    po_date DATE,
    vendor_name TEXT,
    total_amount DECIMAL(10,2),
    items_ordered TEXT,
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (client_document_id) REFERENCES client_documents(id)
);

CREATE TABLE statements_of_work (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    client_document_id INTEGER,
    sow_title TEXT,
    sow_date DATE,
    vendor_name TEXT,
    service_description TEXT,
    is_primarily_human_effort BOOLEAN,
    total_contract_value DECIMAL(10,2),
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (client_document_id) REFERENCES client_documents(id)
);

CREATE TABLE invoice_line_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    line_number INTEGER,
    item_description TEXT NOT NULL,
    quantity DECIMAL(10,2),
    unit_price DECIMAL(10,2),
    line_total DECIMAL(10,2),
    sales_tax_on_line DECIMAL(10,2),
    product_code TEXT,
    gl_code TEXT,
    product_category TEXT,
    is_digital BOOLEAN,
    is_service BOOLEAN,
    primarily_human_effort BOOLEAN,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id)
);

CREATE TABLE legal_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    refund_category TEXT NOT NULL,
    statute_citation TEXT NOT NULL,
    effective_date DATE,
    rule_summary TEXT,
    requirements_json TEXT,
    statute_of_limitations_years INTEGER,
    typical_refund_percentage INTEGER,
    industry_tags TEXT
);

CREATE TABLE refund_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    line_item_id INTEGER,
    legal_rule_id INTEGER,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    potentially_eligible BOOLEAN,
    confidence_score INTEGER,
    estimated_refund_amount DECIMAL(10,2),
    refund_calculation_method TEXT,
    criteria_matching_json TEXT,
    documentation_gaps TEXT,
    red_flags TEXT,
    next_steps TEXT,
    reviewed_by_human BOOLEAN DEFAULT 0,
    human_override BOOLEAN,
    human_notes TEXT,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id),
    FOREIGN KEY (line_item_id) REFERENCES invoice_line_items(id),
    FOREIGN KEY (legal_rule_id) REFERENCES legal_rules(id)
);

CREATE TABLE product_identifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    line_item_id INTEGER NOT NULL,
    product_name TEXT,
    product_category TEXT,
    is_digital BOOLEAN,
    is_service BOOLEAN,
    primarily_human_effort BOOLEAN,
    automation_level TEXT,
    confidence_score INTEGER,
    web_search_used BOOLEAN,
    vendor_website_found TEXT,
    product_specs_found TEXT,
    evidence_json TEXT,
    identification_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (line_item_id) REFERENCES invoice_line_items(id)
);

-- Indexes for performance
CREATE INDEX idx_invoices_client ON invoices(client_id);
CREATE INDEX idx_invoices_date ON invoices(invoice_date);
CREATE INDEX idx_line_items_invoice ON invoice_line_items(invoice_id);
CREATE INDEX idx_analysis_invoice ON refund_analysis(invoice_id);
CREATE INDEX idx_analysis_confidence ON refund_analysis(confidence_score);
CREATE INDEX idx_legal_docs_type ON legal_documents(document_type);
CREATE INDEX idx_legal_docs_citation ON legal_documents(citation);
CREATE INDEX idx_legal_docs_date ON legal_documents(document_date);
CREATE INDEX idx_chunks_document ON document_chunks(document_id);
CREATE INDEX idx_client_docs_type ON client_documents(document_type);
CREATE INDEX idx_client_docs_client ON client_documents(client_id);

-- Seed data: Test client
INSERT INTO clients (client_name, business_entity_type, ubi_number, contact_email, industry_classification)
VALUES ('Test Client LLC', 'LLC', '123-456-789', 'test@example.com', 'Technology');
