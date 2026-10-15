"""Separate proposed Gold dictionary; never edit the imported standard source."""
import pandas as pd

WORDS = dict(calc="계산", yoy="전년동기대비", margin="이익률", debt="부채", equity="자본",
             delta="증감", transition="전환", review="검토", required="필요", rtn="수익률",
             excess="초과성과", net="순", flow="수급", change="변화", volatility="변동성",
             event="공시사건", base="기준", co="동반", move="움직임", joint="공동",
             improve="개선", prior="전년동기", asof="기말", sales="매출", **{"1d": "1관측일", "5d": "5관측일", "20d": "20관측일"})


def write_dictionary(schemas, terms, package, out):
    known_words = pd.read_csv(package/"02_standard_dictionary/std_word.csv", dtype=str, keep_default_na=False)
    glossary = dict(zip(known_words.word_nm, known_words.word_kor_nm)) | WORDS
    old = {r.col_nm: r._asdict() for r in terms.itertuples(index=False)}
    rows, new_tokens = [], set()
    for table, schema in schemas.items():
        for c in schema["columns"]:
            name = c["name"]
            original = old.get(name)
            tokens = name.split("_")
            new_tokens.update(set(tokens)-set(known_words.word_nm))
            rows.append(dict(tbl_nm=table, col_nm=name,
                             term_kor_nm=original["term_kor_nm"] if original else " ".join(glossary.get(t, t) for t in tokens),
                             data_type_nm=c["type"], null_allow_yn="Y" if c["nullable"] else "N",
                             pk_yn="Y" if name in schema["primary_key"] else "N",
                             reuse_term_yn="Y" if original else "N", proposal_ver="c-gold-0.1.0",
                             definition_ref="contracts/analysis.md"))
    pd.DataFrame(rows).to_csv(out/"std_gold_terms_proposal.csv", index=False, encoding="utf-8-sig", lineterminator="\n")
    pd.DataFrame([dict(word_nm=t, word_kor_nm=glossary.get(t, t), word_cls_cd="WORD", status="C_PROPOSAL")
                  for t in sorted(new_tokens)]).to_csv(out/"std_gold_words_proposal.csv", index=False, encoding="utf-8-sig", lineterminator="\n")
