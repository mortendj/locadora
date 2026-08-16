# br_grammar.py — Portuguese grammatical-gender agreement for contract templates.

class GenderTerms:
    """
    Every grammatically-agreeing form needed for a contract-role noun
    (LOCADOR/LOCADORA, LOCATÁRIO/LOCATÁRIA, FIADOR/FIADORA, ...), given
    the underlying person's gender.

    term  — the role noun itself: LOCADOR / LOCADORA / LOCADOR(A)
    o     — bare article/adjective-ending: o / a / o(a)
              (also the "-o"/"-a" ending shared by adjectives like
              domiciliado/domiciliada, obrigado/obrigada — combine as
              e.g. "domiciliad{{ LOC.o }}")
    do    — possessive contraction: do / da / do(a)
    ao    — dative contraction: ao / à / ao(à)
    pelo  — agent contraction: pelo / pela / pelo(a)
    ra    — suffix for "-dor" nouns/adjectives needing a feminine "-a":
              "" / "a" / "(a)" — e.g. "portador{{ LOC.ra }}", "pagador{{ LOC.ra }}"

    gender: "M", "F", or falsy/unknown — unknown renders the neutral
    "(A)"-suffixed forms already used throughout these contracts for a
    real person whose gender isn't on file yet.
    """
    __slots__ = ("term", "o", "do", "ao", "pelo", "ra")

    def __init__(self, term, o, do, ao, pelo, ra):
        self.term = term
        self.o    = o
        self.do   = do
        self.ao   = ao
        self.pelo = pelo
        self.ra   = ra


def gender_terms(gender, masc, fem):
    if gender == "F":
        return GenderTerms(fem, "a", "da", "à", "pela", "a")
    if gender == "M":
        return GenderTerms(masc, "o", "do", "ao", "pelo", "")
    return GenderTerms(f"{masc}(A)", "o(a)", "do(a)", "ao(à)", "pelo(a)", "(a)")
