-- [DEPRECATED] 구 스키마용 마이그레이션 - 현재 CARD_USERS 스키마 사용

ALTER TABLE card_master ADD COLUMN IF NOT EXISTS card_no_normalized VARCHAR(30);
ALTER TABLE card_master ADD COLUMN IF NOT EXISTS card_last4 CHAR(4);

CREATE INDEX IF NOT EXISTS idx_card_master_card_no_normalized ON card_master(card_no_normalized);
CREATE INDEX IF NOT EXISTS idx_card_master_card_last4 ON card_master(card_last4);

UPDATE card_master
SET card_no_normalized = regexp_replace(card_no, '[^0-9]', '', 'g'),
    card_last4 = RIGHT(regexp_replace(card_no, '[^0-9]', '', 'g'), 4)
WHERE card_no_normalized IS NULL AND card_no IS NOT NULL;
