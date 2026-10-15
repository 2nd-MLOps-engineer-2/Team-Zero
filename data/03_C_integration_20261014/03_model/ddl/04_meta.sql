-- TEAM ZERO Medallion (MySQL 8.0) — 자동 생성: code/build_model.py · 표준 tz-std-1.0.0
USE `tz_meta`;

CREATE TABLE IF NOT EXISTS `m_exec_log` (
  `run_id` VARCHAR(64) NOT NULL COMMENT '실행 식별자',
  `step_nm` VARCHAR(200) NOT NULL COMMENT '절차명',
  `tbl_nm` VARCHAR(200) NOT NULL COMMENT '테이블명',
  `layer_cd` VARCHAR(50) NOT NULL COMMENT '계층 코드',
  `input_ver` VARCHAR(80) NOT NULL COMMENT '입력 버전',
  `rcrd_cnt` INT NOT NULL COMMENT '레코드 건수',
  `start_dttm` DATETIME NOT NULL COMMENT '시작 일시',
  `end_dttm` DATETIME NOT NULL COMMENT '종료 일시',
  `run_stts_cd` VARCHAR(50) NOT NULL COMMENT '실행 상태 코드',
  `pipln_ver` VARCHAR(80) NOT NULL COMMENT '파이프라인 버전',
  PRIMARY KEY (`run_id`, `step_nm`, `tbl_nm`),
  CONSTRAINT `ck_m_exec_log_layer_cd` CHECK (`layer_cd` IN ('BRONZE','SILVER','GOLD','META')),
  CONSTRAINT `ck_m_exec_log_rcrd_cnt` CHECK (`rcrd_cnt` >= 0),
  CONSTRAINT `ck_m_exec_log_run_stts_cd` CHECK (`run_stts_cd` IN ('SUCCESS','FAILED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin COMMENT='실행 기록 | 단위: 실행·절차·테이블당 1행';

ALTER TABLE `m_exec_log`
  MODIFY `run_id` VARCHAR(64) NOT NULL COMMENT '실행 식별자',
  MODIFY `step_nm` VARCHAR(200) NOT NULL COMMENT '절차명',
  MODIFY `tbl_nm` VARCHAR(200) NOT NULL COMMENT '테이블명',
  MODIFY `layer_cd` VARCHAR(50) NOT NULL COMMENT '계층 코드',
  MODIFY `input_ver` VARCHAR(80) NOT NULL COMMENT '입력 버전',
  MODIFY `rcrd_cnt` INT NOT NULL COMMENT '레코드 건수',
  MODIFY `start_dttm` DATETIME NOT NULL COMMENT '시작 일시',
  MODIFY `end_dttm` DATETIME NOT NULL COMMENT '종료 일시',
  MODIFY `run_stts_cd` VARCHAR(50) NOT NULL COMMENT '실행 상태 코드',
  MODIFY `pipln_ver` VARCHAR(80) NOT NULL COMMENT '파이프라인 버전';

DROP TABLE IF EXISTS `m_std_word`;
CREATE TABLE `m_std_word` (
  `word_nm` VARCHAR(200) NOT NULL COMMENT '단어 물리명',
  `word_kor_nm` VARCHAR(200) NOT NULL COMMENT '단어 한글명',
  `word_eng_nm` VARCHAR(200) NOT NULL COMMENT '단어 영문명',
  `word_cls_cd` VARCHAR(50) NOT NULL COMMENT '단어 분류 코드',
  PRIMARY KEY (`word_nm`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin COMMENT='표준 단어 | 단위: 단어당 1행';

DROP TABLE IF EXISTS `m_std_dmn`;
CREATE TABLE `m_std_dmn` (
  `dmn_nm` VARCHAR(200) NOT NULL COMMENT '도메인명',
  `cls_word_nm` VARCHAR(200) NOT NULL COMMENT '분류어명',
  `data_type_nm` VARCHAR(200) NOT NULL COMMENT '데이터 유형명',
  `data_len_txt` VARCHAR(2000) NOT NULL COMMENT '데이터 길이 내용',
  `allow_ptrn_txt` VARCHAR(2000) NOT NULL COMMENT '허용 패턴 내용',
  `dmn_desc_txt` VARCHAR(2000) NOT NULL COMMENT '도메인 설명 내용',
  PRIMARY KEY (`dmn_nm`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin COMMENT='표준 도메인 | 단위: 도메인당 1행';

DROP TABLE IF EXISTS `m_std_term`;
CREATE TABLE `m_std_term` (
  `tbl_nm` VARCHAR(200) NOT NULL COMMENT '테이블명',
  `col_nm` VARCHAR(200) NOT NULL COMMENT '컬럼명',
  `term_kor_nm` VARCHAR(200) NOT NULL COMMENT '용어 한글명',
  `dmn_nm` VARCHAR(200) NOT NULL COMMENT '도메인명',
  `data_type_nm` VARCHAR(200) NOT NULL COMMENT '데이터 유형명',
  `null_allow_yn` CHAR(1) NOT NULL COMMENT '널 허용 여부',
  `pk_yn` CHAR(1) NOT NULL COMMENT '기본키 여부',
  `cd_grp_id` VARCHAR(64) COMMENT '코드그룹 식별자',
  `layer_cd` VARCHAR(50) NOT NULL COMMENT '계층 코드',
  `asis_src_txt` VARCHAR(2000) COMMENT '현행 원천 내용',
  PRIMARY KEY (`tbl_nm`, `col_nm`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin COMMENT='표준 용어(컬럼) | 단위: 테이블·컬럼당 1행';
