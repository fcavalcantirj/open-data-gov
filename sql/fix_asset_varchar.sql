-- Fix VARCHAR length issue for politician_assets table
-- Increase asset_type_description from VARCHAR(100) to VARCHAR(500)

ALTER TABLE politician_assets
MODIFY COLUMN asset_type_description VARCHAR(500) COMMENT 'Asset type description - from tse_assets.ds_tipo_bem_candidato';

-- Also increase verification_source if needed
ALTER TABLE politician_assets
MODIFY COLUMN verification_source VARCHAR(500) COMMENT 'Verification source';