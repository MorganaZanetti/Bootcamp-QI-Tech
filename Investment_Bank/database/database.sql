CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE client_category (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(2) UNIQUE NOT NULL CHECK (code IN ('PF','PJ')),
    min_investment NUMERIC(18,2) NOT NULL CHECK (min_investment >= 0)
);

CREATE TABLE client (
    id BIGSERIAL PRIMARY KEY,
    client_key UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    category_id BIGINT NOT NULL REFERENCES client_category(id),
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE natural_person (
    client_id BIGINT PRIMARY KEY REFERENCES client(id) ON DELETE CASCADE,
    cpf VARCHAR(11) UNIQUE NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    birth_date DATE NOT NULL
);

CREATE TABLE legal_entity (
    client_id BIGINT PRIMARY KEY REFERENCES client(id) ON DELETE CASCADE,
    cnpj VARCHAR(14) UNIQUE NOT NULL,
    legal_name VARCHAR(180) NOT NULL
);

CREATE TABLE manager (
    id BIGSERIAL PRIMARY KEY,
    manager_key VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL
);

CREATE TABLE account_status (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(30) UNIQUE NOT NULL
);

CREATE TABLE account (
    id BIGSERIAL PRIMARY KEY,
    account_key UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    client_id BIGINT NOT NULL REFERENCES client(id),
    status_id BIGINT NOT NULL REFERENCES account_status(id),
    account_type VARCHAR(20) NOT NULL CHECK (account_type IN ('checking','investment')),
    agency VARCHAR(10) NOT NULL,
    account_number VARCHAR(30) UNIQUE NOT NULL,
    balance NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK (balance >= 0)
);

CREATE TABLE account_status_history (
    id BIGSERIAL PRIMARY KEY,
    account_id BIGINT NOT NULL REFERENCES account(id),
    status_id BIGINT NOT NULL REFERENCES account_status(id),
    manager_id BIGINT REFERENCES manager(id),
    changed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE currency (
    code VARCHAR(3) PRIMARY KEY,
    name VARCHAR(80) NOT NULL
);

CREATE TABLE fx_rate (
    id BIGSERIAL PRIMARY KEY,
    fx_rate_uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    currency_code VARCHAR(3) NOT NULL REFERENCES currency(code),
    buy_rate NUMERIC(18,8) NOT NULL CHECK (buy_rate > 0),
    sell_rate NUMERIC(18,8) NOT NULL CHECK (sell_rate > 0),
    quoted_at TIMESTAMPTZ NOT NULL,
    UNIQUE(currency_code, quoted_at)
);

CREATE TABLE cdi_rate (
    date DATE PRIMARY KEY,
    daily_rate NUMERIC(18,10) NOT NULL
);

CREATE TABLE investment_fund (
    id BIGSERIAL PRIMARY KEY,
    fund_key UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    currency_code VARCHAR(3) NOT NULL REFERENCES currency(code),
    name VARCHAR(150) NOT NULL,
    risk_level VARCHAR(30) NOT NULL
);

CREATE TABLE position (
    id BIGSERIAL PRIMARY KEY,
    account_id BIGINT NOT NULL REFERENCES account(id),
    fund_id BIGINT NOT NULL REFERENCES investment_fund(id),
    quantity_fx NUMERIC(24,8) NOT NULL DEFAULT 0 CHECK (quantity_fx >= 0),
    cost_basis_brl NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK (cost_basis_brl >= 0),
    UNIQUE(account_id, fund_id)
);

CREATE TABLE invest_order (
    id BIGSERIAL PRIMARY KEY,
    order_key UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    checking_account_id BIGINT NOT NULL REFERENCES account(id),
    investment_account_id BIGINT NOT NULL REFERENCES account(id),
    fund_id BIGINT NOT NULL REFERENCES investment_fund(id),
    fx_rate_id BIGINT NOT NULL REFERENCES fx_rate(id),
    side VARCHAR(4) NOT NULL CHECK (side IN ('buy','sell')),
    amount_brl NUMERIC(18,2) NOT NULL CHECK (amount_brl > 0),
    amount_fx NUMERIC(24,8) NOT NULL CHECK (amount_fx > 0),
    costs JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE entry (
    id BIGSERIAL PRIMARY KEY,
    account_id BIGINT NOT NULL REFERENCES account(id),
    order_id BIGINT REFERENCES invest_order(id),
    entry_type VARCHAR(30) NOT NULL DEFAULT 'transaction',
    amount NUMERIC(18,2) NOT NULL CHECK (amount <> 0),
    balance_after NUMERIC(18,2) NOT NULL CHECK (balance_after >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE quote_alert (
    id BIGSERIAL PRIMARY KEY,
    alert_key UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    client_id BIGINT NOT NULL REFERENCES client(id),
    currency_code VARCHAR(3) NOT NULL REFERENCES currency(code),
    target_rate NUMERIC(18,8) NOT NULL CHECK (target_rate > 0)
);

CREATE TABLE event (
    id BIGSERIAL PRIMARY KEY,
    event_key UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    account_id BIGINT REFERENCES account(id),
    order_id BIGINT REFERENCES invest_order(id),
    request_id UUID,
    detail JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE fee_rule (
    id BIGSERIAL PRIMARY KEY,
    kind VARCHAR(20) NOT NULL CHECK (kind IN ('IR','IOF','spread','fee')),
    rate NUMERIC(18,10) NOT NULL CHECK (rate >= 0),
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,
    CHECK(valid_to IS NULL OR valid_to > valid_from)
);

CREATE INDEX idx_fx_rate_currency_date ON fx_rate(currency_code, quoted_at DESC);
CREATE INDEX idx_entry_account_date ON entry(account_id, created_at DESC);
CREATE INDEX idx_account_status_history_manager ON account_status_history(manager_id);

INSERT INTO client_category(code, min_investment) VALUES
('PF', 2000.00),
('PJ', 5000.00);

INSERT INTO account_status(code) VALUES ('pending'),('open'),('blocked'),('closed');

INSERT INTO currency(code, name) VALUES
('USD','Dólar americano'),
('EUR','Euro'),
('JPY','Iene japonês');

INSERT INTO investment_fund(currency_code, name, risk_level) VALUES
('USD','Investimento em Dólar','moderate'),
('EUR','Investimento em Euro','moderate'),
('JPY','Investimento em Iene','moderate');

INSERT INTO manager(manager_key, name) VALUES ('manager123','Gerente Principal');

INSERT INTO fee_rule(kind, rate, valid_from) VALUES
('spread', 0.025, now());
