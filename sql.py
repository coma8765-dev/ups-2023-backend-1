CREATE_DATABASE = """
CREATE TABLE IF NOT EXISTS ciphers (
    id serial primary key,
    rot integer
)
"""

GET_STATS = """
SELECT rot, count(*) as usages FROM ciphers GROUP BY rot
"""

ADD_ROT = """
INSERT INTO ciphers (rot) VALUES ($1)
"""
