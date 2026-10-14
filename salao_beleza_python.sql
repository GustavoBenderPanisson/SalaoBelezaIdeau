DROP DATABASE IF EXISTS salao_beleza;
CREATE DATABASE salao_beleza
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE salao_beleza;

CREATE TABLE clientes (
    id_cliente INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome_completo VARCHAR(150) NOT NULL,
    cpf VARCHAR(14) NULL,
    telefone VARCHAR(20) NOT NULL,
    email VARCHAR(150) NULL,
    data_nascimento DATE NULL,
    observacoes TEXT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uq_clientes_cpf UNIQUE (cpf),
    CONSTRAINT uq_clientes_email UNIQUE (email),
    INDEX idx_clientes_nome (nome_completo),
    INDEX idx_clientes_telefone (telefone)
) ENGINE=InnoDB;

CREATE TABLE profissionais (
    id_profissional INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome_completo VARCHAR(150) NOT NULL,
    telefone VARCHAR(20) NULL,
    email VARCHAR(150) NULL,
    especialidade VARCHAR(100) NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uq_profissionais_email UNIQUE (email),
    INDEX idx_profissionais_nome (nome_completo)
) ENGINE=InnoDB;

CREATE TABLE servicos (
    id_servico INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao VARCHAR(255) NULL,
    duracao_minutos SMALLINT UNSIGNED NOT NULL,
    preco DECIMAL(10,2) NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uq_servicos_nome UNIQUE (nome),
    CONSTRAINT chk_servicos_duracao CHECK (duracao_minutos > 0),
    CONSTRAINT chk_servicos_preco CHECK (preco >= 0)
) ENGINE=InnoDB;

CREATE TABLE agendamentos (
    id_agendamento INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT UNSIGNED NOT NULL,
    id_profissional INT UNSIGNED NOT NULL,
    id_servico INT UNSIGNED NOT NULL,
    inicio DATETIME NOT NULL,
    fim DATETIME NOT NULL,
    status ENUM('AGENDADO', 'CONFIRMADO', 'CONCLUIDO', 'CANCELADO', 'NAO_COMPARECEU')
        NOT NULL DEFAULT 'AGENDADO',
    motivo_cancelamento VARCHAR(255) NULL,
    observacoes VARCHAR(500) NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_agendamentos_cliente
        FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
    CONSTRAINT fk_agendamentos_profissional
        FOREIGN KEY (id_profissional) REFERENCES profissionais(id_profissional),
    CONSTRAINT fk_agendamentos_servico
        FOREIGN KEY (id_servico) REFERENCES servicos(id_servico),
    CONSTRAINT chk_agendamentos_periodo CHECK (fim > inicio),

    INDEX idx_agendamentos_cliente (id_cliente),
    INDEX idx_agendamentos_profissional_inicio (id_profissional, inicio),
    INDEX idx_agendamentos_status (status),
    INDEX idx_agendamentos_inicio (inicio)
) ENGINE=InnoDB;

DELIMITER $$

CREATE TRIGGER trg_agendamentos_calcular_fim
BEFORE INSERT ON agendamentos
FOR EACH ROW
BEGIN
    DECLARE v_duracao SMALLINT UNSIGNED;

    SELECT duracao_minutos
      INTO v_duracao
      FROM servicos
     WHERE id_servico = NEW.id_servico
       AND ativo = TRUE;

    IF v_duracao IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'O serviço informado não existe ou está inativo.';
    END IF;

    SET NEW.fim = DATE_ADD(NEW.inicio, INTERVAL v_duracao MINUTE);
END$$

CREATE TRIGGER trg_agendamentos_validar_conflito
BEFORE INSERT ON agendamentos
FOR EACH ROW
BEGIN
    IF NEW.status IN ('AGENDADO', 'CONFIRMADO') THEN
        IF EXISTS (
            SELECT 1
              FROM agendamentos a
             WHERE a.id_profissional = NEW.id_profissional
               AND a.status IN ('AGENDADO', 'CONFIRMADO')
               AND NEW.inicio < a.fim
               AND NEW.fim > a.inicio
        ) THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Já existe um agendamento para este profissional nesse período.';
        END IF;
    END IF;
END$$

CREATE PROCEDURE cancelar_agendamento(
    IN p_id_agendamento INT UNSIGNED,
    IN p_motivo VARCHAR(255)
)
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM agendamentos
         WHERE id_agendamento = p_id_agendamento
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Agendamento não encontrado.';
    END IF;

    UPDATE agendamentos
       SET status = 'CANCELADO',
           motivo_cancelamento = NULLIF(TRIM(p_motivo), '')
     WHERE id_agendamento = p_id_agendamento
       AND status NOT IN ('CONCLUIDO', 'CANCELADO');

    IF ROW_COUNT() = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'O agendamento já foi concluído ou cancelado.';
    END IF;
END$$

CREATE PROCEDURE reagendar_agendamento(
    IN p_id_agendamento INT UNSIGNED,
    IN p_novo_inicio DATETIME
)
BEGIN
    DECLARE v_id_profissional INT UNSIGNED;
    DECLARE v_id_servico INT UNSIGNED;
    DECLARE v_duracao SMALLINT UNSIGNED;
    DECLARE v_novo_fim DATETIME;

    SELECT a.id_profissional, a.id_servico, s.duracao_minutos
      INTO v_id_profissional, v_id_servico, v_duracao
      FROM agendamentos a
      JOIN servicos s ON s.id_servico = a.id_servico
     WHERE a.id_agendamento = p_id_agendamento
       AND a.status IN ('AGENDADO', 'CONFIRMADO');

    IF v_id_profissional IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Agendamento não encontrado ou não pode ser reagendado.';
    END IF;

    SET v_novo_fim = DATE_ADD(p_novo_inicio, INTERVAL v_duracao MINUTE);

    IF EXISTS (
        SELECT 1
          FROM agendamentos a
         WHERE a.id_agendamento <> p_id_agendamento
           AND a.id_profissional = v_id_profissional
           AND a.status IN ('AGENDADO', 'CONFIRMADO')
           AND p_novo_inicio < a.fim
           AND v_novo_fim > a.inicio
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'O novo horário entra em conflito com outro agendamento.';
    END IF;

    UPDATE agendamentos
       SET inicio = p_novo_inicio,
           fim = v_novo_fim
     WHERE id_agendamento = p_id_agendamento;
END$$

DELIMITER ;

INSERT INTO profissionais (nome_completo, telefone, email, especialidade) VALUES
('Mariana Souza', '(11) 99999-1111', 'mariana@salao.com', 'Cabeleireira'),
('Juliana Oliveira', '(11) 99999-2222', 'juliana@salao.com', 'Manicure e pedicure');

INSERT INTO servicos (nome, descricao, duracao_minutos, preco) VALUES
('Corte feminino', 'Corte e finalização', 60, 80.00),
('Escova', 'Escova modelada', 45, 55.00),
('Manicure', 'Manicure tradicional', 40, 35.00),
('Pedicure', 'Pedicure tradicional', 50, 45.00),
('Coloração', 'Coloração completa dos cabelos', 120, 180.00);

SELECT
    id_cliente,
    nome_completo,
    cpf,
    telefone,
    email,
    ativo,
    criado_em
FROM clientes
ORDER BY nome_completo;

SELECT
    id_profissional,
    nome_completo,
    telefone,
    email,
    especialidade,
    ativo
FROM profissionais
ORDER BY nome_completo;

SELECT
    id_servico,
    nome,
    descricao,
    duracao_minutos,
    preco,
    ativo
FROM servicos
ORDER BY nome;

SELECT
    a.id_agendamento,
    c.nome_completo AS cliente,
    c.telefone AS telefone_cliente,
    p.nome_completo AS profissional,
    s.nome AS servico,
    DATE_FORMAT(a.inicio, '%d/%m/%Y %H:%i') AS inicio,
    DATE_FORMAT(a.fim, '%d/%m/%Y %H:%i') AS fim,
    a.status,
    a.motivo_cancelamento,
    a.observacoes
FROM agendamentos a
JOIN clientes c ON c.id_cliente = a.id_cliente
JOIN profissionais p ON p.id_profissional = a.id_profissional
JOIN servicos s ON s.id_servico = a.id_servico
ORDER BY a.inicio;

SELECT
    a.id_agendamento,
    c.nome_completo AS cliente,
    p.nome_completo AS profissional,
    s.nome AS servico,
    a.inicio,
    a.fim,
    a.status
FROM agendamentos a
JOIN clientes c ON c.id_cliente = a.id_cliente
JOIN profissionais p ON p.id_profissional = a.id_profissional
JOIN servicos s ON s.id_servico = a.id_servico
WHERE a.inicio >= NOW()
  AND a.status IN ('AGENDADO', 'CONFIRMADO')
ORDER BY a.inicio;
